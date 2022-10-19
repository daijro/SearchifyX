import Foundation
import AppKit
import Vision
import SwiftUI
import UserNotifications

class Scraper {
    static func search(query: String, sites: String, engine: String) -> [Flashcard] {
        if query.isEmpty {
            return []
        }
        
        let proc = Process()
        proc.executableURL =
            Bundle.main.bundleURL.appendingPathComponent("Contents/Resources/scraper/scraper")
        
        let tempDir = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
        let tempFile = ProcessInfo().globallyUniqueString
        
        let tempPath = tempDir.appendingPathComponent(tempFile)
        proc.arguments = ["-q", query, "-s", sites, "-e", engine, "-o", tempPath.path]
        
        var json: String = ""
        
        do {
            try "".write(to: tempPath, atomically: true, encoding: .utf8)
            try proc.run()
            proc.waitUntilExit()
            
            json = try String(contentsOf: tempPath, encoding: .utf8)
            let result = try JSONDecoder().decode([Flashcard].self, from: json.data(using: .utf8)!)
            return result
        }
        catch {
            print("Error occurred trying to run the scraper: \(error)")
            Scraper.alert(caption: "Unable to search", msg: "An error occurred while trying to scrape results")
            return []
        }
    }
    
    static func ocr() -> String {
        var window: NSWindow?
        
        if Variables.hiddenWindow != nil {
            DispatchQueue.main.async {
                if Variables.hiddenWindow!.isKeyWindow {
                    window = NSApp.keyWindow
                    window?.orderOut(nil)
                }
            }
        }
        
        let proc = Process()
        let exec = URL(fileURLWithPath: "/usr/sbin/screencapture")
        proc.executableURL = exec
        proc.arguments = ["-i", "-c"]
        
        do {
            try proc.run()
            proc.waitUntilExit()
            
            if Variables.hiddenWindow != nil {
                DispatchQueue.main.async {
                    window?.orderFront(nil)
                }
            }
            
            var data: Data?
            
            for element in NSPasteboard.general.pasteboardItems! {
                if let img = element.data(forType: NSPasteboard.PasteboardType(rawValue: "public.png")) {
                    data = img
                }
            }
            
            let requestHandler = VNImageRequestHandler(data: data!)
            let req = VNRecognizeTextRequest(completionHandler: nil)
            
            try requestHandler.perform([req])
            
            let observations = req.results
                    
            let recognizedStrings = observations!.compactMap { observation in
                // Return the string of the top VNRecognizedText instance.
                return observation.topCandidates(1).first?.string
            }
            
            if recognizedStrings.isEmpty {
                Scraper.alert(caption: "Unable to run the OCR", msg: "No text was detected")
                return ""
            }
            
            return recognizedStrings.joined()
        }
        catch {
            print("An error occurred trying to run the OCR: \(error)")
            Scraper.alert(caption: "Unable to run the OCR", msg: "An error occurred while trying to run or process the OCR")
            return ""
        }
    }
    
    static func alert(caption: String, msg: String) {
        let content = UNMutableNotificationContent()
        content.title = caption
        content.body = msg
        
        let uuid = UUID().uuidString
        let request = UNNotificationRequest(identifier: uuid, content: content, trigger: nil)
        
        let center = UNUserNotificationCenter.current()
        center.requestAuthorization(options: [.alert, .sound]) { _, _ in}
        center.add(request)
    }
    
    static func getClipboard() -> String {
        var clipboardItems: [String] = []
        for element in NSPasteboard.general.pasteboardItems! {
            if let str = element.string(forType: NSPasteboard.PasteboardType(rawValue: "public.utf8-plain-text")) {
                clipboardItems.append(str)
            }
        }
        
        if (clipboardItems.isEmpty) {
            return ""
        }
        
        return clipboardItems[0]
    }
    
    static func convertPercent(from input: String) -> Float {
        if let res = Float(input.replacingOccurrences(of: "%", with: "")) {
            return res / 100
        } else {
            return 0
        }
    }
    
    static func makeHiddenWindow(question: String?) {
        if Variables.hiddenWindow != nil {
            Variables.hiddenWindow?.isReleasedWhenClosed = true
            Variables.hiddenWindow?.close()
        }
        
        Variables.hiddenWindow = FloatingPanel(contentRect: NSRect(x: 0, y: 0, width: 900, height: 450), backing: .buffered, defer: false)
        
        Variables.hiddenWindow?.title = "Hidden SearchifyX"
        Variables.hiddenWindow?.contentView = NSHostingView(rootView: ContentView(isPanel: true, question: question))
        
        Variables.hiddenWindow?.center()
        Variables.hiddenWindow?.orderFront(nil)
        Variables.hiddenWindow?.makeKey()
    }
}
