//
//  FlashcardRow.swift
//  SearchifyX
//
//  Created by Jose Molina on 9/6/22.
//

import SwiftUI

struct FlashcardRow: View {
    let card: Flashcard
    
    var body: some View {
        HStack {
            ProgressView(value: Scraper.convertPercent(from: card.similarity))
            Text(card.question)
                .fixedSize(horizontal: true, vertical: false)
            Text(card.answer)
            
        }
    }
}

struct FlashcardRow_Previews: PreviewProvider {
    static var previews: some View {
        FlashcardRow(card: Flashcard(question: "What is biology?", answer: "Biology is the study of life", url: "https://google.com", similarity: "100%"))
    }
}
