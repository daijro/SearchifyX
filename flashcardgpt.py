import logging
import orjson
from multiprocessing import Queue, Process
import json
from threading import Thread
import os
import logging
import poe
from poegen import PoeAccountGenerator


# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S'))
logger.propagate = False
logger.addHandler(ch)
# poe logging
poe.logger.setLevel(logging.WARNING)


class PoeAPI:
    def __init__(self, queue_in, queue_out, token):
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.client = poe.Client(token)
        # this seems to be broken for now
        # self.client.send_chat_break('a2')  # clear context
        self.manager()
    
    def manager(self):
        while True:
            prompt = self.queue_in.get()
            for chunk in self.get(prompt):
                self.queue_out.put(chunk)
    
    def get(self, prompt):
        logger.info('Loading result from claude-instant-v1.0 api')
        first_message = True
        full_message = ''
        for chunk in self.client.send_message('a2', prompt):
            if first_message or full_message.endswith(': '):  # remove leading whitespace
                chunk["text_new"] = chunk["text_new"].lstrip()
                first_message = False
            yield chunk["text_new"]
            full_message += chunk["text_new"]
        del full_message  # clear memory
        yield None


class PoeScraper:
    headers = {
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": "\"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"108\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    def start(self):
        # Get previous session
        if prev_sess := PoeAccountGenerator.getSavedSession():
            self.token = prev_sess
            logger.info(f"Using saved session: {self.token}")
        else:
            self.token = PoeAccountGenerator().run()
        self.poe_queue_in, self.poe_queue_out = Queue(), Queue()
        Process(target=PoeAPI, args=(self.poe_queue_in, self.poe_queue_out, self.token), daemon=True).start()
    
    def async_start(self):
        s_thread = Thread(target=self.start, daemon=True)
        s_thread.start()
        return s_thread

    def get(self, prompt):
        # {'capybara': 'Sage', 'beaver': 'GPT-4', 'a2_2': 'Claude+', 'a2': 'Claude-instant', 'chinchilla': 'ChatGPT', 'nutria': 'Dragonfly'}
        self.poe_queue_in.put(prompt)
        
        while (data := self.poe_queue_out.get()) is not None:
            yield data


class FlashcardGPT(PoeScraper):    
    prompt = "Instuctions: You are now FlashcardGPT. A student queries a quiz question into the web search. Using the " \
             "provided data from FlashcardSearch, which flashcard most likely answers to the student's query? Return the most frequent " \
             "and similar answer.\n\nStart with \"Best Answer:\", and briefly explain how the answer is correct. Keep responses short. " \
             "Example:\n\nBest Answer: X\nExplanation: ...\n\n" \
             "Query: {query}\n\nData collected from FlashcardSearch, a web scraper that searches the internet for flashcards:\n{data}\n\n" \
    
    def format_cards(self, cards):
        formatted_list = [
            {
                'Question': card['question'],
                'Answer': card['answer'],
                'Similarity': card['similarity'],
            }
            for card in cards
        ]
        return orjson.dumps(formatted_list, option=orjson.OPT_INDENT_2).decode()

    def run(self, query, cards):
        return self.get(
            self.prompt.format(
                query=query,
                data=self.format_cards(cards)
            )
        )


if __name__ == '__main__':
    chatgpt = FlashcardGPT()
    thread = chatgpt.async_start()
    thread.join()
    prompt = ''
    try:
        while True:
            inp = input('>> ')
            prompt += f'User: {inp}\n\nAssistant: '
            for chunk in chatgpt.get(prompt):
                print(chunk, end='')
                prompt += chunk
            prompt += '\n\n'
            print('')
    except KeyboardInterrupt:
        logger.info('Exiting')
        exit()
