import SwiftUI

struct ScraperView: View {
    @State var question: String = ""
    @State var enableQuizizz: Bool = true
    @State var enableQuizlet: Bool = true
    @State var cards: [Flashcard] = []
    @State var selected: Flashcard.ID?
    @State var searching: Bool = false
    @State var engine: String = "google"
    
    @AppStorage("runAfterOcr") var runAfterOcr: Bool = false
    @AppStorage("runAfterPaste") var runAfterPaste: Bool = false
    
    var hasShown: Bool?
    var skQuery: String?
    
    var isPanel: Bool
    
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
            if isPanel {
                ScraperToolbar(question: $question, runAfterPaste: $runAfterPaste, searchQuestion: searchQuestion(query:), runAfterOcr: $runAfterOcr, searching: $searching)
                    .padding(.leading)
                    .padding(.trailing)
            }
            
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
                    Variables.wkModel.urlString = url.absoluteString
                    
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
        .toolbar {
            ToolbarItemGroup(placement: .principal) {
                ScraperToolbar(question: $question, runAfterPaste: $runAfterPaste, searchQuestion: searchQuestion(query:), runAfterOcr: $runAfterOcr, searching: $searching)
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

struct ScraperView_Previews: PreviewProvider {
    static var previews: some View {
        ScraperView(isPanel: false, question: nil)
    }
}
