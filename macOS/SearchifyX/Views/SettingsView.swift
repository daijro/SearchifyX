import SwiftUI
import KeyboardShortcuts

struct SettingsView: View {
    @AppStorage("runAfterOcr") var runAfterOcr: Bool = false
    @AppStorage("runAfterPaste") var runAfterPaste: Bool = false
    @AppStorage("showOnNotificationCenter") var showOnNotificationCenter: Bool = false
    
    var body: some View {
        VStack {
            Toggle(isOn: $runAfterOcr) {
                Text("Search after OCR text is pasted")
            }
            Toggle(isOn: $runAfterPaste) {
                Text("Search after text is pasted")
            }
            Toggle(isOn: $showOnNotificationCenter) {
                Text("Send answer as notification instead of showing window")
            }
            KeyboardShortcuts.Recorder("Open Hidden SearchifyX", name: .openSearchify)
            KeyboardShortcuts.Recorder("OCR and search", name: .ocrAndSearch)
            KeyboardShortcuts.Recorder("Paste and search", name: .pasteAndSearch)
        }
        .padding()
    }
}

struct SettingsView_Previews: PreviewProvider {
    static var previews: some View {
        SettingsView()
    }
}
