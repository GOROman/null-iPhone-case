import CoreBluetooth
import Combine
import Foundation

private let serviceID = CBUUID(string: "ad7c4900-71f4-4f77-9ccd-798cf78fb040")
private let packetID = CBUUID(string: "ad7c4901-71f4-4f77-9ccd-798cf78fb040")
private let statusID = CBUUID(string: "ad7c4902-71f4-4f77-9ccd-798cf78fb040")

private let clockID = CBUUID(string: "ad7c4903-71f4-4f77-9ccd-798cf78fb040")

private func littleEndian(_ value: UInt32) -> [UInt8] {
    (0..<4).map { UInt8(truncatingIfNeeded: value >> ($0 * 8)) }
}

final class PaperLink: NSObject, ObservableObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    static func clockPacket(at date: Date, in zone: TimeZone) -> Data {
        let epoch = UInt32(date.timeIntervalSince1970)
        let minutes = Int16(zone.secondsFromGMT(for: date) / 60)
        let offset = UInt16(bitPattern: minutes)
        return Data(littleEndian(epoch) + [UInt8(truncatingIfNeeded: offset), UInt8(offset >> 8)])
    }

    enum Stage { case idle, scanning, connecting, ready, sending, painting, complete, failed }
    @Published private(set) var stage = Stage.idle
    @Published private(set) var message = "ケースの電源ボタンを押して接続してください。"
    @Published private(set) var devices: [CBPeripheral] = []
    @Published private(set) var progress = 0.0
    private var central: CBCentralManager!
    private var peer: CBPeripheral?
    private var packet: CBCharacteristic?, status: CBCharacteristic?, clock: CBCharacteristic?
    private var image: PaperPhoto?
    private var offset = 0, pending = 0
    private var commitSent = false
    private var deadline: Timer?, poll: Timer?
    private var wantsScan = false

    func scan() {
        releaseConnection()
        devices.removeAll()
        wantsScan = true
        if central == nil {
            central = CBCentralManager(delegate: self, queue: .main)
            return
        }
        if central.state == .poweredOn { startScan() }
        else if central.state != .unknown && central.state != .resetting { unavailable() }
    }
    private func startScan() {
        wantsScan = false
        stage = .scanning
        message = "起動中のケースを探しています。"
        central.scanForPeripherals(withServices: [serviceID])
        timeout(25, "ケースが見つかりません。電源を入れてもう一度検索してください。")
    }
    func connect(_ device: CBPeripheral) {
        guard stage == .scanning else { return }
        central.stopScan()
        stage = .connecting
        message = "接続中です。ペアリングの確認が出たら許可してください。"
        peer = device
        device.delegate = self
        central.connect(device)
        timeout(45, "ペアリングを確認できませんでした。")
    }
    func send(_ photo: PaperPhoto) {
        guard stage == .ready, peer != nil, packet != nil else { return }
        image = photo
        offset = 0
        pending = 0
        commitSent = false
        progress = 0
        stage = .sending
        message = "画像を転送中"
        write(Data([1] + littleEndian(UInt32(photo.pixels.count)) + littleEndian(photo.checksum)))
    }
    func cancel() {
        releaseConnection()
        stage = .idle
        message = "接続を終了しました。"
    }
    private func releaseConnection() {
        wantsScan = false
        deadline?.invalidate()
        poll?.invalidate()
        if central?.isScanning == true { central.stopScan() }
        let old = peer
        peer = nil
        packet = nil
        status = nil
        clock = nil
        image = nil
        if let old { old.delegate = nil; central.cancelPeripheralConnection(old) }
    }
    private func fail(_ text: String) {
        releaseConnection()
        stage = .failed
        message = text
    }
    private func unavailable() {
        fail(central.state == .unauthorized ? "設定でBluetoothへのアクセスを許可してください。" : "Bluetoothをオンにしてください。")
    }
    private func timeout(_ seconds: TimeInterval, _ text: String) {
        deadline?.invalidate()
        deadline = .scheduledTimer(withTimeInterval: seconds, repeats: false) { [weak self] _ in self?.fail(text) }
    }
    private func write(_ data: Data) {
        guard let peer, let packet else { return }
        timeout(15, "転送が中断されました。ケースを再起動して再送してください。")
        peer.writeValue(data, for: packet, type: .withResponse)
    }
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            if wantsScan { startScan() }
        } else if central.state != .unknown && central.state != .resetting {
            unavailable()
        }
    }
    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral,
                        advertisementData: [String: Any], rssi RSSI: NSNumber) {
        if stage == .scanning && !devices.contains(where: { $0.identifier == peripheral.identifier }) {
            devices.append(peripheral)
        }
    }
    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        if peripheral == peer { peripheral.discoverServices([serviceID]) }
    }
    func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        if peripheral == peer { fail("接続できませんでした。電源を確認してください。") }
    }
    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        if peripheral == peer { fail("ケースとの接続が終了しました。電源を押して再接続できます。") }
    }
    func peripheral(_ p: CBPeripheral, didDiscoverServices error: Error?) {
        guard p == peer else { return }
        guard error == nil, let service = p.services?.first(where: { $0.uuid == serviceID })
        else { fail("対応するケースが見つかりません。"); return }
        p.discoverCharacteristics([packetID, statusID, clockID], for: service)
    }
    func peripheral(_ p: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        guard p == peer else { return }
        packet = service.characteristics?.first(where: { $0.uuid == packetID })
        status = service.characteristics?.first(where: { $0.uuid == statusID })
        clock = service.characteristics?.first(where: { $0.uuid == clockID })
        guard error == nil, packet != nil, let status else { fail("ケースのファームウェアを確認してください。"); return }
        p.readValue(for: status)
    }
    func peripheral(_ p: CBPeripheral, didWriteValueFor c: CBCharacteristic, error: Error?) {
        if p == peer && c.uuid == clockID && stage == .connecting {
            deadline?.invalidate()
            stage = .ready
            message = error == nil ? "時計を合わせました。画像を送信できます。" : "時計の同期に失敗しました。画像は送信できます。"
            return
        }
        guard p == peer, c.uuid == packetID, stage == .sending, let image else { return }
        guard error == nil else { fail("書き込みに失敗しました。再接続して再送してください。"); return }
        offset += pending
        pending = 0
        progress = Double(offset) / Double(image.pixels.count)
        if commitSent {
            stage = .painting
            message = "電子ペーパーを更新中"
            timeout(30, "表示の完了を確認できませんでした。")
            if let status { p.readValue(for: status) }
        } else if offset == image.pixels.count {
            commitSent = true
            write(Data([3]))
        } else {
            let limit = min(512, p.maximumWriteValueLength(for: .withResponse), p.maximumWriteValueLength(for: .withoutResponse)) - 5
            guard limit > 0 else { fail("この接続では画像を転送できません。"); return }
            pending = min(limit, image.pixels.count - offset)
            var chunk = Data([2] + littleEndian(UInt32(offset)))
            chunk.append(image.pixels[offset..<(offset + pending)])
            write(chunk)
        }
    }
    func peripheral(_ p: CBPeripheral, didUpdateValueFor c: CBCharacteristic, error: Error?) {
        guard p == peer, c.uuid == statusID else { return }
        guard error == nil, let data = c.value, data.count == 5 else {
            fail("暗号化接続を確認できません。ペアリング状態を確認してください。"); return
        }
        let state = data[0]
        if stage == .connecting && state == 0 {
            if let clock {
                p.writeValue(Self.clockPacket(at: Date(), in: .current), for: clock, type: .withResponse)
                return
            }
            deadline?.invalidate()
            stage = .ready
            message = "接続しました。画像を送信できます。"
        } else if stage == .painting && state == 2 {
            poll = .scheduledTimer(withTimeInterval: 0.4, repeats: false) { [weak self] _ in
                if let self, let status = self.status { self.peer?.readValue(for: status) }
            }
        } else if stage == .painting && state == 3, let image,
                  Array(data.dropFirst()) == littleEndian(image.checksum) {
            releaseConnection()
            stage = .complete
            message = "ケースの表示を更新しました。"
        } else {
            fail("ケースが画像を受理できませんでした。再接続して再送してください。")
        }
    }
}
