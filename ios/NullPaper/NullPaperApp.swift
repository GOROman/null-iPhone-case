import PhotosUI
import SwiftUI

@main
struct NullPaperApp: App {
    var body: some Scene { WindowGroup { PhotoView() } }
}

private struct PhotoView: View {
    private enum Mode { case photo, qr }
    @State private var mode = Mode.photo
    @State private var urlText = ""
    @State private var qr: PaperPhoto?
    @State private var qrError = ""
    @FocusState private var editingURL: Bool
    private var selectedImage: PaperPhoto? { mode == .photo ? photo : qr }
    @StateObject private var link = PaperLink()
    @State private var selection: PhotosPickerItem?
    @State private var photo: PaperPhoto?
    @State private var photoError = ""
    @State private var loading = false
    private var busy: Bool { link.stage == .sending || link.stage == .painting }
    private let cyan = Color(red: 0.0, green: 0.41, blue: 0.47)

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    Picker("表示内容", selection: $mode) {
                        Text("写真").tag(Mode.photo)
                        Text("URL・QR").tag(Mode.qr)
                    }
                    .pickerStyle(.segmented)
                    .disabled(busy)
                    ZStack {
                        Circle().fill(.background)
                        if let selectedImage {
                            Image(uiImage: selectedImage.preview).resizable().interpolation(mode == .qr ? .none : .high).scaledToFit().clipShape(Circle())
                        } else {
                            Image(systemName: mode == .qr ? "qrcode" : "photo").font(.system(size: 48, weight: .light))
                                .foregroundStyle(.secondary)
                        }
                        Circle().strokeBorder(cyan.opacity(0.4), lineWidth: 4)
                    }
                    .frame(maxWidth: 288).aspectRatio(1, contentMode: .fit)
                    .accessibilityLabel("ケース中央の丸窓プレビュー")
                    if mode == .photo {
                        PhotosPicker(selection: $selection, matching: .images) {
                            Label(photo == nil ? "写真を選ぶ" : "写真を変更", systemImage: "photo.on.rectangle")
                        }
                        .disabled(busy || loading)
                        if loading { ProgressView("写真を変換中") }
                        if !photoError.isEmpty { Text(photoError).foregroundStyle(.red) }
                    } else {
                        TextField("https://example.com", text: $urlText)
                            .accessibilityLabel("QRコードにするURL")
                            .textFieldStyle(.roundedBorder)
                            .keyboardType(.URL)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .focused($editingURL)
                            .submitLabel(.done)
                            .onSubmit { generateCode() }
                            .onChange(of: urlText) { _, _ in qr = nil; qrError = "" }
                            .disabled(busy)
                        Button("QRコードを作成") { generateCode() }
                            .disabled(busy || urlText.isEmpty)
                        if !qrError.isEmpty { Text(qrError).foregroundStyle(.red) }
                    }
                    Divider()
                    Text(link.message).font(.callout).frame(maxWidth: .infinity, alignment: .leading)
                        .accessibilityAddTraits(.updatesFrequently)
                    switch link.stage {
                    case .idle, .failed, .complete:
                        Button("ケースを探す") { link.scan() }.buttonStyle(.borderedProminent)
                    case .scanning:
                        if link.devices.isEmpty { ProgressView() }
                        ForEach(link.devices, id: \.identifier) { device in
                            Button { link.connect(device) } label: {
                                Label("\(device.name ?? "NULL PAPER") · \(device.identifier.uuidString.prefix(4))",
                                      systemImage: "link")
                            }.buttonStyle(.bordered)
                        }
                        Button("検索を終了") { link.cancel() }
                    case .connecting:
                        ProgressView()
                        Button("キャンセル") { link.cancel() }
                    case .ready:
                        Button(mode == .qr ? "QRコードをケースに送る" : "写真をケースに送る") {
                            if let selectedImage { link.send(selectedImage) }
                        }
                            .buttonStyle(.borderedProminent).disabled(selectedImage == nil)
                        Button("接続を終了") { link.cancel() }
                    case .sending:
                        ProgressView(value: link.progress)
                        Button("送信を中止") { link.cancel() }
                    case .painting:
                        ProgressView()
                    }
                }
                .padding(24)
            }
            .navigationTitle("NULL PAPER")
            .tint(cyan)
            .task(id: selection) {
                guard let selection else { return }
                loading = true
                photoError = ""
                photo = nil
                do {
                    guard let data = try await selection.loadTransferable(type: Data.self)
                    else { throw CocoaError(.fileReadCorruptFile) }
                    let result = try await Task.detached(priority: .userInitiated) { try PaperPhoto(data: data) }.value
                    try Task.checkCancellation()
                    photo = result
                } catch {
                    if !Task.isCancelled { photoError = "この写真を読み込めませんでした。" }
                }
                if !Task.isCancelled { loading = false }
            }
        }
        .onChange(of: busy) { _, current in UIApplication.shared.isIdleTimerDisabled = current }
        .onDisappear { UIApplication.shared.isIdleTimerDisabled = false }
    }

    private func generateCode() {
        editingURL = false
        do {
            qr = try URLCode.make(urlText)
            qrError = ""
        } catch {
            qr = nil
            qrError = error.localizedDescription
        }
    }
}
