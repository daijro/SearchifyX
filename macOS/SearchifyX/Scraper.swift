//
//  Scraper.swift
//  SearchifyX
//
//  Created by Jose Molina on 9/2/22.
//

import Foundation
import AppKit
import Vision

class Scraper {
    func search(query: String, sites: String, engine: String) -> [Flashcard] {
        let proc = Process()
        proc.executableURL =
            Bundle.main.bundleURL.appendingPathComponent("Contents/Resources/scraper.app/Contents/MacOS/scraper")
        
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
            return []
        }
    }
    
    func ocr() -> String {
        let proc = Process()
        let exec = URL(fileURLWithPath: "/usr/sbin/screencapture")
        proc.executableURL = exec
        proc.arguments = ["-i", "-c"]
        
        do {
            try proc.run()
            proc.waitUntilExit()
            
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
                alert(caption: "Unable to run the OCR", msg: "No text was detected")
                return ""
            }
            
            return recognizedStrings.joined()
        }
        catch {
            print("An error occurred trying to run the OCR: \(error)")
            alert(caption: "Unable to run the OCR", msg: "An error occurred while trying to run or process the OCR")
            return ""
        }
    }
    
    func alert(caption: String, msg: String) {
        DispatchQueue.main.async {
            let alert = NSAlert()
            alert.messageText = caption
            alert.informativeText = msg
            alert.addButton(withTitle: "OK")
            alert.alertStyle = .warning
            alert.runModal()
        }
    }
    
    static func convertPercent(from input: String) -> Float {
        if let res = Float(input.replacingOccurrences(of: "%", with: "")) {
            return res / 100
        } else {
            return 0
        }
    }
}
