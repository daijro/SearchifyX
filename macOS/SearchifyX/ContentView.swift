import SwiftUI

struct ContentView: View {
    @State var question: String = ""
    @State var enableQuizizz: Bool = true
    @State var enableQuizlet: Bool = true
    @State var cards: [Flashcard] = []
    @State var selected: Flashcard.ID?
    @State var searching: Bool = false
    @State var engine: String = "google"
    @State var showingPanel: Bool = false
    
    @AppStorage("runAfterOcr") var runAfterOcr: Bool = false
    @AppStorage("runAfterPaste") var runAfterPaste: Bool = false
    
    var isPanel: Bool
    var hasShown: Bool?
    var skQuery: String?
    
    init(isPanel: Bool, question q: String?) {
        self.isPanel = isPanel
        if q != nil {
            skQuery = q!
            hasShown = true
        }
        else {
            hasShown = false
        }
    }
    
    var body: some View {
        VStack {
            HStack {
                if isPanel == false {
                    Button(action: {
                        Scraper.makeHiddenWindow(question: nil)
                    }, label: {
                        Image(systemName: "eye.slash")
                    })
                }
                TextField("Search a question here", text: $question)
                    .lineLimit(nil)
                Button(
                    action: {
                        searchQuestion(query: self.question)
                    },
                    label: {
                        Image(systemName: "magnifyingglass")
                        Text("Search")
                    }
                )
                Button(
                    action: {
                        question = Scraper.getClipboard()
                        
                        if runAfterPaste {
                            searchQuestion(query: self.question)
                        }
                    },
                    label: {
                        Image(systemName: "doc.on.clipboard")
                    }
                )
                Button(
                    action: {
                        DispatchQueue.global(qos: .userInitiated).async {
                            question = Scraper.ocr()
                            
                            if runAfterOcr {
                                searchQuestion(query: self.question)
                            }
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
        .onAppear {
            if hasShown! {
                self.question = skQuery!
                searchQuestion(query: skQuery!)
            }
        }
    }
    
    func searchQuestion(query: String) {
        searching = true
        
        var sites: [String] = []
        
        if enableQuizizz {
            sites.append("quizizz")
        }
        if enableQuizlet {
            sites.append("quizlet")
        }
        
        DispatchQueue.global(qos: .userInitiated).async {
                cards = Scraper.search(query: query, sites: sites.joined(separator: ","), engine: engine)
                searching = false
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView(isPanel: false, question: nil)
    }
}
