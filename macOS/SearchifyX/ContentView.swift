//
//  ContentView.swift
//  SearchifyX
//
//  Created by Jose Molina on 9/2/22.
//

import SwiftUI

let scraper = Scraper()

struct ContentView: View {
    @State var question: String = ""
    @State var enableQuizizz: Bool = true
    @State var enableQuizlet: Bool = true
    @State var cards: [Flashcard] = []
    @State var selected: Flashcard.ID?
    @State var searching: Bool = false
    @State var engine: String = "google"
    @State var showingPanel: Bool = false
    
    var isPanel: Bool
    
    var body: some View {
        VStack {
            HStack {
                if isPanel == false {
                    Button(action: {
                        let ep = FloatingPanel(contentRect: NSRect(x: 0, y: 0, width: 900, height: 450), backing: .buffered, defer: false)
                        
                        ep.title = "Hidden SearchifyX"
                        ep.contentView = NSHostingView(rootView: ContentView(isPanel: true))
                        
                        ep.center()
                        ep.orderFront(nil)
                        ep.makeKey()
                    }, label: {
                        Image(systemName: "eye.slash")
                    })
                }
                TextField("Search a question here", text: $question)
                    .lineLimit(nil)
                Button(
                    action: {
                        searching = true
                        print(engine)
                        
                        var sites: [String] = []
                        
                        if enableQuizizz {
                            sites.append("quizizz")
                        }
                        if enableQuizlet {
                            sites.append("quizlet")
                        }
                        
                        DispatchQueue.global(qos: .userInitiated).async {
                                cards = scraper.search(query: question, sites: sites.joined(separator: ","), engine: engine)
                                searching = false
                        }
                    },
                    label: {
                        Image(systemName: "magnifyingglass")
                        Text("Search")
                    }
                )
                Button(
                    action: {
                        var clipboardItems: [String] = []
                        for element in NSPasteboard.general.pasteboardItems! {
                            if let str = element.string(forType: NSPasteboard.PasteboardType(rawValue: "public.utf8-plain-text")) {
                                clipboardItems.append(str)
                            }
                        }
                        
                        question = clipboardItems[0]
                    },
                    label: {
                        Image(systemName: "doc.on.clipboard")
                    }
                )
                Button(
                    action: {
                        DispatchQueue.global(qos: .userInitiated).async {
                            question = scraper.ocr()
                        }
                    },
                    label: {
                        Image(systemName: "eye")
                    }
                )
            }
            .disabled(searching != false)
            .padding()
            
            ZStack {
                Table(cards, selection: $selected) {
                    TableColumn("Question", value: \.question)
                    TableColumn("Answer", value: \.answer)
                    TableColumn("Similarity", value: \.similarity)
                    TableColumn("URL", value: \.url)
                }
                
                if searching {
                    ProgressView()
                }
            }
            
            HStack {
                Spacer()
                Picker("Search Engine", selection: $engine) {
                    Text("Google").tag("google")
                    Text("Bing").tag("bing")
                    Text("Startpage").tag("startpage")
                }
                Button(action: {
                    var original: Flashcard?
                    
                    for item in cards {
                        if (item.id == selected) {
                            original = item
                            break
                        }
                    }
                    
                    let url = URL(string: original!.url)!
                    NSWorkspace.shared.open(url)
                    
                }, label: {
                    Text("Open question")
                })
                .disabled(selected == nil)
                Toggle(isOn: $enableQuizizz) {
                    Image("QuizizzIcon")
                        .resizable()
                        .frame(width: 16, height: 16)
                    Text("Quizizz")
                }
                Toggle(isOn: $enableQuizlet) {
                    Image("QuizletIcon")
                        .resizable()
                        .frame(width: 16, height: 16)
                    Text("Quizlet")
                }
            }
            .padding()
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView(isPanel: false)
    }
}
