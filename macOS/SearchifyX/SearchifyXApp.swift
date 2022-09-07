//
//  SearchifyXApp.swift
//  SearchifyX
//
//  Created by Jose Molina on 9/2/22.
//

import SwiftUI
import KeyboardShortcuts

@main
struct SearchifyXApp: App {
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        WindowGroup {
            ContentView(isPanel: false)
        }
        Settings {
            SettingsView()
        }
    }
}

@MainActor
final class AppState: ObservableObject {
    init() {
        KeyboardShortcuts.onKeyUp(for: .openSearchify) { [self] in
            let ep = FloatingPanel(contentRect: NSRect(x: 0, y: 0, width: 900, height: 450), backing: .buffered, defer: false)
            
            ep.title = "Hidden SearchifyX"
            ep.contentView = NSHostingView(rootView: ContentView(isPanel: true))
            
            ep.center()
            ep.orderFront(nil)
            ep.makeKey()
        }
    }
}
