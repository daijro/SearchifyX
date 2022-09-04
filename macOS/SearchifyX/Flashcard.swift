//
//  Flashcard.swift
//  SearchifyX
//
//  Created by Jose Molina on 9/2/22.
//

import Foundation

struct Flashcard: Identifiable, Codable {
    let question: String
    let answer: String
    let url: String
    let similarity: String
    var id = UUID()
}
