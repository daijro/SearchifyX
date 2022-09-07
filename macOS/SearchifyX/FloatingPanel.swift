import SwiftUI
import Cocoa

class FloatingPanel: NSPanel {
    init(contentRect: NSRect, backing: NSWindow.BackingStoreType, defer flag: Bool) {
        super.init(contentRect: contentRect, styleMask: [.nonactivatingPanel, .titled, .resizable, .closable, .fullSizeContentView], backing: backing, defer: flag)
        self.isFloatingPanel = true
        self.level = .floating
        self.collectionBehavior.insert(.fullScreenAuxiliary)
        self.titleVisibility = .visible
        self.titlebarAppearsTransparent = false
        self.isMovableByWindowBackground = true
        self.isReleasedWhenClosed = false
        
        self.standardWindowButton(.closeButton)?.isHidden = false
        self.standardWindowButton(.miniaturizeButton)?.isHidden = true
        self.standardWindowButton(.zoomButton)?.isHidden = true
    }

    override var canBecomeKey: Bool {
        return true
    }

    override var canBecomeMain: Bool {
        return true
    }
}
