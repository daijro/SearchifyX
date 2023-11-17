//
//  WebView.swift
//  SearchifyX
//
//  Created by Jose Molina on 10/20/22.
//

import Foundation
import WebKit
import SwiftUI

struct NSWebView: NSViewRepresentable {
    let webkit: WKWebView
    
    func makeNSView(context: Context) -> WKWebView {
        webkit
    }
    
    func updateNSView(_ nsView: WKWebView, context: Context) {
    }
}
