//
//  Scraper.swift
//  SearchifyX
//
//  Created by Jose Molina on 9/2/22.
//

import Foundation
import PythonKit

class Scraper {
    func search(query: String, sites: String, engine: String) -> [Flashcard] {
        let proc = Process()
        let exec = Bundle.main.bundleURL.appendingPathComponent("Contents/Resources/scraper.app/Contents/MacOS/scraper")
        proc.executableURL = exec
        
        let tempDir = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
        let tempFile = ProcessInfo().globallyUniqueString
        
        let tempPath = tempDir.appendingPathComponent(tempFile)
        var json: String = ""
        
        do {
            try "".write(to: tempPath, atomically: true, encoding: .utf8)
            print(tempPath.path)
            proc.arguments = ["-q", query, "-s", sites, "-e", engine, "-o", tempPath.path]
            print("Launching python process now")
            try proc.run()
            proc.waitUntilExit()
            
            json = try String(contentsOf: tempPath, encoding: .utf8)
        }
        catch {
            print("Error occurred trying to run the scraper")
        }
        
        let result = try? JSONDecoder().decode([Flashcard].self, from: json.data(using: .utf8)!)
        return result!
    }
}
