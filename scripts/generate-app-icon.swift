import AppKit

// Rasterize the authoritative app-icon artwork (design/Egg-Icon.png, 1024×1024
// with transparency) into every macOS slot. The 1024px slot is copied byte-for
// byte; smaller sizes are high-interpolation downscales. See design/app-icon.md.
//
// Usage: swift generate-app-icon.swift <AppIcon.appiconset dir> <source-1024.png>
guard CommandLine.arguments.count == 3 else {
    fatalError("usage: generate-app-icon.swift <appiconset-dir> <source-1024.png>")
}
let destination = URL(fileURLWithPath: CommandLine.arguments[1])
let sourceURL = URL(fileURLWithPath: CommandLine.arguments[2])
let sourceData = try Data(contentsOf: sourceURL)
guard let source = NSBitmapImageRep(data: sourceData),
      source.pixelsWide == 1024, source.pixelsHigh == 1024 else {
    fatalError("source must be a 1024×1024 PNG: \(sourceURL.path)")
}

let slots = [(16, 1), (16, 2), (32, 1), (32, 2), (128, 1), (128, 2), (256, 1), (256, 2), (512, 1), (512, 2)]
var images: [[String: String]] = []
for (size, scale) in slots {
    let pixels = size * scale
    let filename = "icon_\(size)x\(size)@\(scale)x.png"
    if pixels == 1024 {
        // The export is the icon; re-encoding it would only invite drift.
        try sourceData.write(to: destination.appendingPathComponent(filename))
    } else {
        let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: pixels, pixelsHigh: pixels, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)
        NSGraphicsContext.current!.imageInterpolation = .high
        source.draw(in: NSRect(x: 0, y: 0, width: pixels, height: pixels),
                    from: NSRect(x: 0, y: 0, width: 1024, height: 1024),
                    operation: .copy, fraction: 1, respectFlipped: true, hints: nil)
        NSGraphicsContext.restoreGraphicsState()
        try bitmap.representation(using: .png, properties: [:])!.write(to: destination.appendingPathComponent(filename))
    }
    images.append(["idiom": "mac", "size": "\(size)x\(size)", "scale": "\(scale)x", "filename": filename])
}
let catalog: [String: Any] = ["images": images, "info": ["author": "xcode", "version": 1]]
try JSONSerialization.data(withJSONObject: catalog, options: [.prettyPrinted, .sortedKeys]).write(to: destination.appendingPathComponent("Contents.json"))
