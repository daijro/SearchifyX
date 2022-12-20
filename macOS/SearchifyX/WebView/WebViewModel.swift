//
//  WebViewModel.swift
//  SearchifyX
//
//  Created by Jose Molina on 11/17/22.
//

import Foundation
import WebKit

class WebViewModel: ObservableObject {
    @Published var urlString: String = "https://google.com/"
    
    let instance: WKWebView
    
    init() {
        instance = WKWebView(frame: .zero);
    }
    
    func loadUrl() {
        guard let url = URL(string: urlString) else {
            return
        }
        
        instance.load(URLRequest(url: url))
    }
}
