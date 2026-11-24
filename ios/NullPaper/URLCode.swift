import CoreImage.CIFilterBuiltins
import UIKit

enum URLCode {
    enum InputError: LocalizedError {
        case invalidURL, tooDense, generation
        var errorDescription: String? {
            switch self {
            case .invalidURL: return "http:// または https:// で始まるURLを入力してください。"
            case .tooDense: return "このURLは丸窓で読み取るには長すぎます。短いURLを入力してください。"
            case .generation: return "QRコードを生成できませんでした。"
            }
        }
    }

    private static let context = CIContext()

    static func make(_ input: String) throws -> PaperPhoto {
        let text = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard text.rangeOfCharacter(from: .whitespacesAndNewlines.union(.controlCharacters)) == nil,
              let url = URL(string: text),
              let scheme = url.scheme?.lowercased(), ["http", "https"].contains(scheme),
              let host = url.host, !host.isEmpty else { throw InputError.invalidURL }

        let filter = CIFilter.qrCodeGenerator()
        filter.message = Data(url.absoluteString.utf8)
        filter.correctionLevel = "M"
        guard let output = filter.outputImage else { throw InputError.tooDense }
        guard let symbol = context.createCGImage(output, from: output.extent) else { throw InputError.generation }
        let width = symbol.width
        var modules = [UInt8](repeating: 255, count: width * width)
        let drawn = modules.withUnsafeMutableBytes { bytes -> Bool in
            guard let bitmap = CGContext(data: bytes.baseAddress, width: width, height: width,
                bitsPerComponent: 8, bytesPerRow: width, space: CGColorSpaceCreateDeviceGray(),
                bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return false }
            bitmap.draw(symbol, in: CGRect(x: 0, y: 0, width: width, height: width))
            return true
        }
        guard drawn else { throw InputError.generation }

        // Finder patterns touch the top and bottom symbol edges. Discard the generator's
        // symmetric border, then lay out a four-module quiet zone at the final pixel size.
        guard let firstBlack = modules.firstIndex(where: { $0 < 128 }) else { throw InputError.generation }
        let border = firstBlack / width
        let count = width - 2 * border
        let side = PaperPhoto.side
        let inscribedSide = Int(Double(side) / sqrt(2))
        let scale = inscribedSide / (count + 8)
        guard scale >= 4 else { throw InputError.tooDense }
        let offset = (side - count * scale) / 2
        var grey = [UInt8](repeating: 255, count: side * side)
        for y in 0..<count {
            for x in 0..<count where modules[(y + border) * width + x + border] < 128 {
                for dy in 0..<scale {
                    let start = (offset + y * scale + dy) * side + offset + x * scale
                    for dx in 0..<scale { grey[start + dx] = 0 }
                }
            }
        }
        return try PaperPhoto(grey: grey)
    }
}
