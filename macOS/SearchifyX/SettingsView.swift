//
//  SettingsView.swift
//  SearchifyX
//
//  Created by Jose Molina on 9/6/22.
//

import SwiftUI
import KeyboardShortcuts

struct SettingsView: View {
    @AppStorage("runAfterOcr") var runAfterOcr: Bool = false
    @AppStorage("runAfterPaste") var runAfterPaste: Bool = false
    
    var body: some View {
        VStack {
            Toggle(isOn: $runAfterOcr) {
                Text("Search after OCR text is pasted")
            }
            Toggle(isOn: $runAfterPaste) {
                Text("Search after text is pasted")
            }
            KeyboardShortcuts.Recorder("Open Hidden SearchifyX", name: .openSearchify)
        }
        .padding()
    }
}

struct SettingsView_Previews: PreviewProvider {
    static var previews: some View {
        SettingsView()
    }
}
