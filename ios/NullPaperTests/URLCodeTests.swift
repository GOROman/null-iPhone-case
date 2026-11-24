import XCTest
import CoreImage
import UIKit
@testable import NullPaper

final class URLCodeTests: XCTestCase {
    func testDecodeTransmittedPixelsThroughRoundWindow() throws {
        for text in ["https://example.com", "https://example.org/写真?a=1&b=2#地図",
                     "https://example.com/?q=" + String(repeating: "a", count: 90)] {
            let frame = try URLCode.make(text)
            let side = PaperPhoto.side, radius = side / 2
            var grey = [UInt8](repeating: 0, count: side * side)
            for i in grey.indices {
                let byte = frame.pixels[i / 2]
                let g = (i.isMultiple(of: 2) ? byte >> 4 : byte & 15) * 17
                let dx = i % side - radius, dy = i / side - radius
                if dx * dx + dy * dy <= radius * radius { grey[i] = g }
                else if g != 255 { XCTFail("A dark module extends outside the aperture"); return }
            }
            let provider = try XCTUnwrap(CGDataProvider(data: Data(grey) as CFData))
            let masked = try XCTUnwrap(CGImage(width: side, height: side, bitsPerComponent: 8,
                bitsPerPixel: 8, bytesPerRow: side, space: CGColorSpaceCreateDeviceGray(),
                bitmapInfo: [], provider: provider, decode: nil, shouldInterpolate: false, intent: .defaultIntent))
            let detector = try XCTUnwrap(CIDetector(ofType: CIDetectorTypeQRCode,
                context: CIContext(options: [.useSoftwareRenderer: true]),
                options: [CIDetectorAccuracy: CIDetectorAccuracyHigh]))
            let features = detector.features(in: CIImage(cgImage: masked))
            XCTAssertEqual((features.first as? CIQRCodeFeature)?.messageString, URL(string: text)?.absoluteString)
        }
    }

    func testRejectsInvalidAndUnscannablyDenseURLs() {
        for text in ["", "example.com", "https://", "https://bad host", "javascript:alert(1)",
                     "https://example.com/?q=" + String(repeating: "a", count: 600)] {
            XCTAssertThrowsError(try URLCode.make(text))
        }
    }
}
