//
//  BrowserView.swift
//  SearchifyX
//
//  Created by Jose Molina on 11/17/22.
//

import SwiftUI

struct BrowserView: View {
    var urlStr: Binding<String> { Binding(
        get: { return Variables.wkModel.urlString }, set: {str in
            Variables.wkModel.urlString = str
        }
    )}
    
    var isPanel: Bool
    
    var body: some View {
        VStack {
            if (isPanel) {
                BrowserToolbar(url: urlStr)
                    .padding(.leading)
                    .padding(.trailing)
            }
            
            NSWebView(webkit: Variables.wkModel.instance)
        }
        .toolbar {
            ToolbarItemGroup(placement: .principal) {
                BrowserToolbar(url: urlStr)
            }
        }
        .onLoad {
            Variables.wkModel.loadUrl()
        }
    }
}

struct BrowserView_Previews: PreviewProvider {
    static var previews: some View {
        BrowserView(isPanel: false)
    }
}
