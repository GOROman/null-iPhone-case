import UIKit
import ImageIO

struct PaperPhoto {
    static let side = 320
    let pixels: Data
    let checksum: UInt32
    let preview: UIImage

    init(data: Data) throws {
        guard let source = CGImageSourceCreateWithData(data as CFData, nil),
              let image = CGImageSourceCreateThumbnailAtIndex(source, 0, [
                kCGImageSourceCreateThumbnailFromImageAlways: true,
                kCGImageSourceCreateThumbnailWithTransform: true,
                kCGImageSourceThumbnailMaxPixelSize: 1600
              ] as CFDictionary) else { throw PhotoError.decode }
        let side = Self.side
        let space = CGColorSpaceCreateDeviceGray()
        var grey = [UInt8](repeating: 255, count: side * side)
        let rendered = grey.withUnsafeMutableBytes { buffer -> Bool in
            guard let context = CGContext(data: buffer.baseAddress, width: side, height: side,
                bitsPerComponent: 8, bytesPerRow: side, space: space,
                bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return false }
            let factor = CGFloat(side) / CGFloat(min(image.width, image.height))
            let width = CGFloat(image.width) * factor, height = CGFloat(image.height) * factor
            context.interpolationQuality = .high
            context.draw(image, in: CGRect(x: (CGFloat(side) - width)/2, y: (CGFloat(side) - height)/2,
                                           width: width, height: height))
            return true
        }
        guard rendered else { throw PhotoError.decode }
        try self.init(grey: grey)
    }

    init(grey: [UInt8]) throws {
        let side = Self.side
        guard grey.count == side * side else { throw PhotoError.decode }
        var grey = grey
        let space = CGColorSpaceCreateDeviceGray()
        var packed = Data(capacity: grey.count / 2)
        for i in stride(from: 0, to: grey.count, by: 2) {
            let a = (Int(grey[i]) + 8) / 17, b = (Int(grey[i+1]) + 8) / 17
            packed.append(UInt8(a << 4 | b))
            grey[i] = UInt8(a * 17)
            grey[i+1] = UInt8(b * 17)
        }
        guard let provider = CGDataProvider(data: Data(grey) as CFData),
              let cg = CGImage(width: side, height: side, bitsPerComponent: 8, bitsPerPixel: 8,
                               bytesPerRow: side, space: space, bitmapInfo: CGBitmapInfo(rawValue: 0),
                               provider: provider, decode: nil, shouldInterpolate: false,
                               intent: .defaultIntent) else { throw PhotoError.decode }
        pixels = packed
        checksum = packed.reduce(UInt32.max) { previous, byte in
            var crc = previous ^ UInt32(byte)
            for _ in 0..<8 { crc = (crc >> 1) ^ (crc & 1 == 1 ? 0xedb88320 : 0) }
            return crc
        } ^ UInt32.max
        preview = UIImage(cgImage: cg)
    }

    private enum PhotoError: Error { case decode }
}
