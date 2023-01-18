//
//  BrowserToolbar.swift
//  SearchifyX
//
//  Created by Jose Molina on 11/17/22.
//

import SwiftUI

struct BrowserToolbar: View {
    var url: Binding<String>
    
    var body: some View {
        HStack {
            Button(action: {
                Variables.wkModel.instance.goBack()
            }, label: {
                Image(systemName: "chevron.left")
            })
            .buttonStyle(.borderless)
            Button(action: {
                Variables.wkModel.instance.goBack()
            }, label: {
                Image(systemName: "chevron.right")
            })
            .buttonStyle(.borderless)
            TextField("Enter URL", text: url)
                .frame(minWidth: 400, maxWidth: 400)
                .textFieldStyle(.roundedBorder)
            Button(action: {
                Variables.wkModel.loadUrl()
            }, label: {
                Text("Go")
            })
            .buttonStyle(.borderless)
            Spacer()
        }
    }
}
