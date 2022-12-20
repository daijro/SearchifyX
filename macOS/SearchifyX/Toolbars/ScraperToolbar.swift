//
//  ScraperToolbar.swift
//  SearchifyX
//
//  Created by Jose Molina on 11/17/22.
//

import SwiftUI

struct ScraperToolbar: View {
    var question: Binding<String>
    var runAfterPaste: Binding<Bool>
    var searchQuestion: (String) -> Void
    var runAfterOcr: Binding<Bool>
    var searching: Binding<Bool>
    
    var body: some View {
        HStack {
            TextField("Search a question here", text: question)
                .lineLimit(nil)
                .frame(minWidth: 400)
                .textFieldStyle(.roundedBorder)
            Button(
                action: {
                    searchQuestion(self.question.wrappedValue)
                },
                label: {
                    Image(systemName: "magnifyingglass")
                    Text("Search")
                }
            )
            .buttonStyle(.borderless)
            Button(
                action: {
                    self.question.wrappedValue = Scraper.getClipboard()
                    
                    if runAfterPaste.wrappedValue {
                        searchQuestion(self.question.wrappedValue)
                    }
                },
                label: {
                    Image(systemName: "doc.on.clipboard")
                }
            )
            .buttonStyle(.borderless)
            Button(
                action: {
                    DispatchQueue.global(qos: .userInitiated).async {
                        question.wrappedValue = Scraper.ocr()
                        
                        if runAfterOcr.wrappedValue {
                            searchQuestion(self.question.wrappedValue)
                        }
                    }
                },
                label: {
                    Image(systemName: "eye")
                }
            )
            .buttonStyle(.borderless)
        }
        .disabled(searching.wrappedValue != false)
    }
}
