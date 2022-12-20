//
//  ContentView.swift
//  SearchifyX
//
//  Created by Jose Molina on 11/17/22.
//

import SwiftUI

struct ContentView: View {
    var isPanel: Bool
    var question: String?
    
    var body: some View {
        NavigationView() {
            List() {
                NavigationLink(destination: ScraperView(isPanel: isPanel, question: question)) {
                    HStack {
                        Image(systemName: "magnifyingglass")
                        Text("Search")
                    }
                }
                .navigationTitle("Search")
                NavigationLink(destination: BrowserView(isPanel: isPanel)) {
                    HStack {
                        Image(systemName: "globe.americas")
                        Text("Browser")
                    }
                }
                .navigationTitle("Browser")
                NavigationLink(destination: NotesView()) {
                    HStack {
                        Image(systemName: "note.text")
                        Text("Notes")
                    }
                }
                .navigationTitle("Notes")
                NavigationLink(destination: SettingsView()) {
                    HStack {
                        Image(systemName: "gear")
                        Text("Settings")
                    }
                }
                .navigationTitle("Settings")
            }
            .toolbar {
                ToolbarItemGroup(placement: .navigation) {
                    if !isPanel {
                        Button(action: {
                            Scraper.makeHiddenWindow(question: nil)
                        }, label: {
                            Image(systemName: "eye.slash.fill")
                        })
                    }
                }
            }
            .frame()
            .listStyle(.sidebar)
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView(isPanel: false)
    }
}
