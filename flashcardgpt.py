from requests import Session
import logging
import orjson
from multiprocessing import Queue, Process
import re
import json
from threading import Thread, Lock
from mailtm import Email
import pickle
import os
import logging
import time
from base64 import b64decode

# logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')

# base64 decode
def atob(s):
    return b64decode(s).decode()


class FlashcardGPT:    
    prompt = "Instuctions: You are now FlashcardGPT. A student queries a quiz question into the web search. Using the " \
             "provided data from FlashcardSearch, which flashcard most likely answers to the student's query? Return the most frequent " \
             "and similar answer.\n\nStart with \"Best Answer:\", and briefly explain how the answer is correct. " \
             "Example:\n\nBest Answer: X\nExplanation: ...\n\n" \
             "Query: {query}\n\nData collected from FlashcardSearch, a web scraper that searches the internet for flashcards:\n{data}\n\n" \
    
    def __init__(self):
        self.sess = Session()
    
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
        logging.info('Loading result from claude-instant-v1.0 api')
        return self.get(
            self.prompt.format(
                query=query,
                data=self.format_cards(cards)
            )
        )


class NatScraper(FlashcardGPT):
    domain = atob('bmF0LmRldg==')
    headers = {
        "Sec-Ch-Ua": "\"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"108\"",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Origin": atob("aHR0cHM6Ly9hY2NvdW50cy5uYXQuZGV2"),
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    def start(self):
        self.sess.headers.update(self.headers)
        # Get previous session
        if prev_sess := self.getSavedSession():
            self.sua_id, self.sess_id = prev_sess
            logging.info(f"Using saved session: {self.sess_id}")
        else:
            self.sua_id, self.sess_id = self.registerAccount()
        # Update header origin
        self.sess.headers.update({
            'Origin': f'https://{self.domain}',
            'Referer': f'https://{self.domain}/'
        })
        # Start token refresher
        Thread(target=self.token_refresher, daemon=True).start()
    
    def async_start(self):
        s_thread = Thread(target=self.start, daemon=True)
        s_thread.start()
        return s_thread
    
    def token_refresher(self):
        while True:
            time.sleep(50)
            self.refresh_jwt()
    
    def getSavedSession(self):
        if os.path.exists("pickle.bin"):
            with open("pickle.bin", "rb") as f:
                self.sess.cookies.update(pickle.load(f))
            with open("session_id.json", "r") as f:
                self.sua_id, self.sess_id = json.load(f).values()
            self.refresh_jwt()
            return self.sua_id, self.sess_id

    def verifyEmailListener(self):
        listen_queue = Queue()
        def listener(message):
            txt = message['text'] or message['html']
            listen_queue.put(re.search('https://[^\s]+', txt)[0])

        logging.info("Registering email")
        # Get Domains
        test = Email()

        # Make new email address
        test.register()
        logging.info(f"Email Adress: {str(test.address)}")
        self.email_queue.put(test.address)

        # Start listening
        test.start(listener)
        self.email_queue.put(listen_queue.get())
        test.stop(); exit()  # Stop listening
        
    def registerAccount(self):
        self.email_queue = Queue()
        Process(target=self.verifyEmailListener, daemon=True).start()

        # Get sign up request
        logging.info("Sending sign up request")
        resp0_url = f"https://clerk.{self.domain}/v1/client/sign_ups?_clerk_js_version=4.32.6"
        resp0_cookies = {"__client_uat": "0"}
        resp0_data = {"email_address": self.email_queue.get()}
        resp0 = self.sess.post(resp0_url, cookies=resp0_cookies, data=resp0_data)

        self.sua_id = resp0.json()['response']['id']
        logging.info(f"Session ID: {self.sua_id}")

        # POST /v1/client/sign_ups/sua/prepare_verification?_clerk_js_version=4.32.6 - send email
        logging.info("Sending verification email")
        resp1_url = f"https://clerk.{self.domain}/v1/client/sign_ups/{self.sua_id}/prepare_verification?_clerk_js_version=4.32.6"
        resp1_data = {"strategy": "email_link", "redirect_url": f"https://accounts.{self.domain}/sign-up/verify?redirect_url=https%3A%2F%2F{self.domain}%2F"}
        self.sess.post(resp1_url, data=resp1_data)

        # LINK THROUGH EMAIL
        logging.info("Waiting for email")
        email_url = self.email_queue.get()
        logging.info("Email recieved. Closing email listener")

        # GET  v1/verify?token=TOKEN_HERE - sets cookie, returns "Location" header (follow)
        logging.info("Verifying email")
        self.sess.get(email_url)

        logging.info("Retrieving JWT")
        resp2 = self.sess.get(f"https://clerk.{self.domain}/v1/client?_clerk_js_version=4.32.6")
        self.sess_id = resp2.json()['response']['sessions'][0]['id']
        # self.sess.post(f"https://clerk.{self.domain}/v1/client/sessions/{self.sess_id}/touch?_clerk_js_version=4.32.6")
        # resp3 = self.sess.get(f"https://clerk.{self.domain}/v1/client?_clerk_js_version=4.32.6")
        # jwt = resp3.json()['response']['sessions'][0]['last_active_token']['jwt']
        # self.sess.cookies.set('_session', jwt)

        self.refresh_jwt()
        
        with open('session_id.json', 'w') as f:
            f.write(json.dumps({
                'sua_id': self.sua_id,
                'sess_id': self.sess_id,
            }))
        return self.sua_id, self.sess_id

    def refresh_jwt(self):
        with Lock():
            logging.info('Refreshing JWT')
            if 'Authorization' in self.sess.headers:
                del self.sess.headers['Authorization']
            url = f"https://clerk.{self.domain}/v1/client/sessions/{self.sess_id}/tokens?_clerk_js_version=4.32.6"
            resp = self.sess.post(url)
            jwt = resp.json()['jwt']
            self.sess.headers['Authorization'] = f"Bearer {jwt}"
            self.sess.cookies.set('_session', jwt)
            self.save_cookies()

    def save_cookies(self):
        # save cookies to file
        with open('pickle.bin', 'wb') as f:
            pickle.dump(self.sess.cookies, f)

    def get(self, prompt):
        # print(self.sess.get(f"https://{self.domain}/api/all_models").json())
        data = {
            "prompt": prompt,
            "models": [{
                "name": "anthropic:claude-instant-v1.0",
                "enabled": True,
                "selected": True,
                "provider": "anthropic",
                "tag": "anthropic:claude-instant-v1.0",
                "parameters": {
                    "temperature": 1,
                    "maximumLength": 200,
                    "topP": 1,
                    "topK": 1,
                    "presencePenalty": 1,
                    "frequencyPenalty": 1,
                    "stopSequences": []
                }
            }]
        }
        resp = self.sess.post(f"https://{self.domain}/api/stream", json=data, stream=True)
        status_event = False
        first_message = True
        for line in resp.iter_lines():
            line = line.decode()
            if line.startswith('event:'):
                status_event = line[6:] == 'status'
            elif status_event:
                continue
            elif line.startswith('data:'):
                data = json.loads(line[5:])
                if first_message or last_message.endswith(': '):  # remove leading whitespace
                    data['message'] = data['message'].lstrip()
                    first_message = False
                yield data['message']
                last_message = data['message']


if __name__ == '__main__':
    chatgpt = NatScraper()
    thread = chatgpt.async_start()
    thread.join()
    try:
        while True:
            inp = input('>> ')        
            for chunk in chatgpt.get(inp):
                print(chunk, end='')
            print('')
    except KeyboardInterrupt:
        logging.info('Exiting')
        exit()
