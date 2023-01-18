//
//  WebViewModel.swift
//  SearchifyX
//
//  Created by Jose Molina on 11/17/22.
//

import Foundation
import WebKit

class WebViewModel: ObservableObject {
    @Published var urlString: String = "https://google.com"
    
    let instance: WKWebView
    var cord: Coordinator?
    var bindingsInit: Bool
    
    init() {
        instance = WKWebView(frame: .zero);
        bindingsInit = false
        cord = nil
    }
    
    func loadUrl() {
        createBindings()
        
        if !urlString.starts(with: "http") {
            urlString = "https://" + urlString
        }
        
        var req = URLRequest(url: URL(string: urlString)!)
        instance.load(req)
    }
    
    func createBindings() {
        if bindingsInit == true {
            return
        }
        cord = Coordinator(self)
        instance.navigationDelegate = cord
        bindingsInit = true
    }
        
    class Coordinator: NSObject, WKNavigationDelegate {
        let parent: WebViewModel
        
        init(_ parent: WebViewModel) {
            self.parent = parent
        }

        func webView(_ webView: WKWebView,
                     didStartProvisionalNavigation navigation: WKNavigation!) {
            print(webView.url!.absoluteString)
            parent.urlString = webView.url!.absoluteString
        }
        
    }
}
