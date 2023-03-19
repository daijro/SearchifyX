from requests import Session
import yaml


class FlashcardGPT:
    headers = {
        'authority': 'gpt-4-chat-ui.techwithanirudh.repl.co',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://gpt-4-chat-ui.techwithanirudh.repl.co',
        'referer': 'https://gpt-4-chat-ui.techwithanirudh.repl.co/',
        'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }
    
    prompt = "Instuctions: You are now FlashcardGPT. A student queries a quiz question into the web search. Using the " \
             "provided data from FlashcardSearch, which flashcard most likely answers to the student's query? Return the most frequent " \
             "and similar answer.\n\nStart with \"Best Answer:\", and briefly explain to the student how the answer is correct. Only choose one answer." \
             "Example:\nBest Answer: ...\nExplanation: ...\n" \
             "Query: {prompt}\n\nData collected from FlashcardSearch, a web scraper that searches the internet for flashcards:\n{cards}"

    def __init__(self):
        self.sess = Session()
        self.sess.headers.update(self.headers)
    
    def _format_cards(self, cards):
        formatted_list = [
            {
                'Question': card['question'],
                'Answer': card['answer'],
                'Similarity': card['similarity'],
            }
            for card in cards
        ]
        return yaml.dump(formatted_list)
    
    def run(self, prompt, cards):
        cards = self._format_cards(cards)
        payload = {
            'messages': [
                {
                    'role': 'user',
                    'content': self.prompt.format(prompt=prompt, cards=cards),
                }
            ],
            'model': 'gpt-3.5-turbo',
        }
        resp = self.sess.post('https://gpt-4-chat-ui.techwithanirudh.repl.co/api/chat', json=payload)
        try:
            return resp.json()['result']['content']
        except Exception:
            return f'Could not parse output: {resp.text}'
