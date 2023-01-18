//
//  BrowserView.swift
//  SearchifyX
//
//  Created by Jose Molina on 11/17/22.
//

import SwiftUI

struct BrowserView: View {
    var isPanel: Bool
    
    @EnvironmentObject var wkvm: WebViewModel
    
    var body: some View {
        VStack {
            if (isPanel) {
                BrowserToolbar(url: $wkvm.urlString)
                    .padding(.leading)
                    .padding(.trailing)
            }
            
            NSWebView(webkit: Variables.wkModel.instance)
        }
        .toolbar {
            ToolbarItemGroup(placement: .principal) {
                BrowserToolbar(url: $wkvm.urlString)
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
