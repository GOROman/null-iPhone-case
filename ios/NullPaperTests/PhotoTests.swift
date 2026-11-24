import XCTest
import UIKit
@testable import NullPaper

final class PhotoTests: XCTestCase {
    func testClockWireFormatIncludesSignedLocalOffset() {
        let date = Date(timeIntervalSince1970: 0x6789abcd)
        for (offset, suffix) in [(540, [UInt8(0x1c), 2]), (-480, [0x20, 0xfe])] {
            let zone = TimeZone(secondsFromGMT: offset * 60)!
            XCTAssertEqual(PaperLink.clockPacket(at: date, in: zone), Data([0xcd, 0xab, 0x89, 0x67] + suffix))
        }
    }

    func testCropOrientationAndWireFormat() throws {
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        let png = UIGraphicsImageRenderer(size: CGSize(width: 640, height: 320), format: format).pngData { ctx in
            UIColor.gray.setFill()
            ctx.fill(CGRect(x: 0, y: 0, width: 640, height: 320))
            UIColor.black.setFill()
            ctx.fill(CGRect(x: 160, y: 0, width: 320, height: 160))
            UIColor.white.setFill()
            ctx.fill(CGRect(x: 160, y: 160, width: 320, height: 160))
        }
        let photo = try PaperPhoto(data: png)
        let expected = Data(repeating: 0, count: 25600) + Data(repeating: 255, count: 25600)
        XCTAssertEqual(photo.pixels, expected)
        XCTAssertEqual(photo.checksum, 0x58595ecd)
        XCTAssertEqual(photo.preview.size, CGSize(width: 320, height: 320))
    }
    func testLeftPixelUsesHighNibble() throws {
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        let png = UIGraphicsImageRenderer(size: CGSize(width: 320, height: 320), format: format).pngData { ctx in
            UIColor.white.setFill()
            ctx.fill(CGRect(x: 0, y: 0, width: 320, height: 320))
            UIColor.black.setFill()
            for x in stride(from: 0, to: 320, by: 2) {
                ctx.fill(CGRect(x: x, y: 0, width: 1, height: 320))
            }
        }
        let photo = try PaperPhoto(data: png)
        XCTAssertEqual(photo.pixels, Data(repeating: 0x0f, count: 51200))
        XCTAssertEqual(photo.checksum, 0x4e83f307)
    }
}
