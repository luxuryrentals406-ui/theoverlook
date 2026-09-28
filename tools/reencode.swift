// Re-encode a video for the web with an explicit bitrate, using nothing but
// what macOS ships (there is no ffmpeg on this machine).
//
//   swift tools/reencode.swift <in> <out.mp4> <h264|hevc> <maxWidth> <maxHeight> <kbps> [audioKbps]
//
// The output keeps the source aspect ratio inside maxWidth x maxHeight, so a
// vertical 9:16 reel bounded by 1080x1920 comes out 1080x1920 and one bounded
// by 720x1280 comes out 720x1280. Audio is AAC at audioKbps (default 96), or
// dropped when the source has none.
import AVFoundation
import Foundation

let a = CommandLine.arguments
guard a.count >= 7 else {
    FileHandle.standardError.write("usage: reencode.swift <in> <out.mp4> <h264|hevc> <maxW> <maxH> <kbps> [audioKbps]\n".data(using: .utf8)!)
    exit(2)
}
let inURL = URL(fileURLWithPath: a[1]), outURL = URL(fileURLWithPath: a[2])
let codec: AVVideoCodecType = a[3] == "hevc" ? .hevc : .h264
let maxW = Double(a[4])!, maxH = Double(a[5])!, kbps = Int(a[6])!
let audioKbps = a.count > 7 ? Int(a[7])! : 96

let asset = AVURLAsset(url: inURL)
guard let vTrack = asset.tracks(withMediaType: .video).first else { print("no video track"); exit(1) }
let aTrack = asset.tracks(withMediaType: .audio).first

// natural size after the track's own transform (phones record rotated)
let raw = vTrack.naturalSize.applying(vTrack.preferredTransform)
let srcW = abs(raw.width), srcH = abs(raw.height)
let scale = min(maxW / srcW, maxH / srcH, 1.0)
let outW = Int((srcW * scale / 2).rounded()) * 2, outH = Int((srcH * scale / 2).rounded()) * 2
print("source \(Int(srcW))x\(Int(srcH)) -> \(outW)x\(outH) \(a[3]) \(kbps) kbps")

try? FileManager.default.removeItem(at: outURL)
let reader = try! AVAssetReader(asset: asset)
let writer = try! AVAssetWriter(outputURL: outURL, fileType: .mp4)

// video: the reader hands us decoded frames, the writer compresses them
let vOut = AVAssetReaderTrackOutput(track: vTrack, outputSettings: [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange])
vOut.alwaysCopiesSampleData = false
reader.add(vOut)
var compression: [String: Any] = [
    AVVideoAverageBitRateKey: kbps * 1000,
    AVVideoMaxKeyFrameIntervalKey: 60,
    AVVideoExpectedSourceFrameRateKey: Int(vTrack.nominalFrameRate.rounded()),
]
if codec == .h264 {
    compression[AVVideoProfileLevelKey] = AVVideoProfileLevelH264HighAutoLevel
    compression[AVVideoH264EntropyModeKey] = AVVideoH264EntropyModeCABAC
}
let vIn = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: codec,
    AVVideoWidthKey: outW,
    AVVideoHeightKey: outH,
    AVVideoScalingModeKey: AVVideoScalingModeResizeAspect,
    AVVideoCompressionPropertiesKey: compression,
])
vIn.expectsMediaDataInRealTime = false
vIn.transform = vTrack.preferredTransform
writer.add(vIn)

// audio: decode to PCM, re-encode as AAC
var aOut: AVAssetReaderTrackOutput? = nil
var aIn: AVAssetWriterInput? = nil
if let t = aTrack {
    let o = AVAssetReaderTrackOutput(track: t, outputSettings: [AVFormatIDKey: kAudioFormatLinearPCM])
    reader.add(o); aOut = o
    let i = AVAssetWriterInput(mediaType: .audio, outputSettings: [
        AVFormatIDKey: kAudioFormatMPEG4AAC, AVNumberOfChannelsKey: 2,
        AVSampleRateKey: 44100, AVEncoderBitRateKey: audioKbps * 1000])
    i.expectsMediaDataInRealTime = false
    writer.add(i); aIn = i
}

guard writer.startWriting() else { print("writer: \(writer.error!)"); exit(1) }
reader.startReading()
writer.startSession(atSourceTime: .zero)

let group = DispatchGroup()
func pump(_ input: AVAssetWriterInput, _ output: AVAssetReaderTrackOutput, _ label: String) {
    group.enter()
    input.requestMediaDataWhenReady(on: DispatchQueue(label: label)) {
        while input.isReadyForMoreMediaData {
            if let s = output.copyNextSampleBuffer() { input.append(s) }
            else { input.markAsFinished(); group.leave(); return }
        }
    }
}
pump(vIn, vOut, "video")
if let i = aIn, let o = aOut { pump(i, o, "audio") }
group.wait()
let done = DispatchSemaphore(value: 0)
writer.finishWriting { done.signal() }
done.wait()
if writer.status != .completed { print("failed: \(String(describing: writer.error))"); exit(1) }
let bytes = (try? FileManager.default.attributesOfItem(atPath: outURL.path)[.size] as? Int) ?? 0
print(String(format: "wrote %@  %.1f MB", outURL.lastPathComponent, Double(bytes) / 1048576))
