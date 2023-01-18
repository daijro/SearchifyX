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
    
    @State var selection: Int?
    @EnvironmentObject var wkvm: WebViewModel
    
    var body: some View { 
        NavigationView() {
            List() {
                NavigationLink(destination: ScraperView(isPanel: isPanel, question: question), tag: 0, selection: $selection) {
                    HStack {
                        Image(systemName: "magnifyingglass")
                        Text("Search")
                    }
                }
                .navigationTitle("Search")
                NavigationLink(destination: BrowserView(isPanel: isPanel).environmentObject(wkvm), tag: 1, selection: $selection) {
                    HStack {
                        Image(systemName: "globe.americas")
                        Text("Browser")
                    }
                }
                .navigationTitle("Browser")
                NavigationLink(destination: NotesView(), tag: 2, selection: $selection) {
                    HStack {
                        Image(systemName: "note.text")
                        Text("Notes")
                    }
                }
                .navigationTitle("Notes")
                NavigationLink(destination: SettingsView(), tag: 3, selection: $selection) {
                    HStack {
                        Image(systemName: "gear")
                        Text("Settings")
                    }
                }
                .navigationTitle("Settings")
            }
            .onAppear() {
                self.selection = 0
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
