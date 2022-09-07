//
//  AppDelegate.swift
//  SearchifyX
//
//  Created by Jose Molina on 9/6/22.
//

import Foundation
import AppKit
import SwiftUI

class AppDelegate: NSObject, NSApplicationDelegate {
    var newEntryPanel: FloatingPanel!

      func applicationDidFinishLaunching(_ aNotification: Notification) {
          if let window = NSApplication.shared.windows.first {
                  window.close()
              }
          
          createFloatingPanel()

          // Center doesn't place it in the absolute center, see the documentation for more details
          newEntryPanel.center()

          // Shows the panel and makes it active
          newEntryPanel.orderFront(nil)
          newEntryPanel.makeKey()
      }

      func applicationWillTerminate(_ aNotification: Notification) {
          // Insert code here to tear down your application
      }

      private func createFloatingPanel() {
          // Create the SwiftUI view that provides the window contents.
          // I've opted to ignore top safe area as well, since we're hiding the traffic icons
          let contentView = ContentView(isPanel: true)
              .edgesIgnoringSafeArea(.top)

          // Create the window and set the content view.
          newEntryPanel = FloatingPanel(contentRect: NSRect(x: 0, y: 0, width: 512, height: 80), backing: .buffered, defer: false)

          newEntryPanel.title = "Hidden SearchifyX"
          newEntryPanel.contentView = NSHostingView(rootView: contentView)
      }
}
