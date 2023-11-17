import SwiftUI
import KeyboardShortcuts

@main
struct SearchifyXApp: App {
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        WindowGroup {
            ContentView(isPanel: false)
                .environmentObject(Variables.wkModel)
        }
        .windowStyle(HiddenTitleBarWindowStyle())
        Settings {
            SettingsView()
        }
    }
}

@MainActor
final class AppState: ObservableObject {
    init() {
        KeyboardShortcuts.onKeyUp(for: .openSearchify) { [self] in
            Scraper.makeHiddenWindow(question: nil)
        }
        
        KeyboardShortcuts.onKeyUp(for: .ocrAndSearch) { [self] in
            if UserDefaults.standard.bool(forKey: "showOnNotificationCenter") {
                searchAndSend(question: Scraper.ocr())
            }
            else {
                Scraper.makeHiddenWindow(question: Scraper.ocr())
            }
        }
        
        KeyboardShortcuts.onKeyUp(for: .pasteAndSearch) { [self] in
            if UserDefaults.standard.bool(forKey: "showOnNotificationCenter") {
                searchAndSend(question: Scraper.getClipboard())
            }
            else {
                Scraper.makeHiddenWindow(question: Scraper.getClipboard())
            }
        }
    }
    
    func searchAndSend(question: String?) {
        if (question == nil) {
            return
        }
        
        let card = Scraper.search(query: question!, sites: "quizlet,quizizz", engine: "google").first
        if (card != nil) {
            Scraper.alert(caption: card!.question, msg: card!.answer)
        }
    }
}
