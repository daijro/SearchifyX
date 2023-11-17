import Foundation

struct Flashcard: Identifiable, Codable {
    let question: String
    let answer: String
    let url: String
    let similarity: String
    let id = UUID()
}
