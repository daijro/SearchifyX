from requests import Session
import logging
import orjson
from multiprocessing import Queue, Process
import re
import json
from threading import Thread
from mailtm import Email
import os
import logging
from bs4 import BeautifulSoup, SoupStrainer
from base64 import b64decode
import poe


# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S'))
logger.propagate = False
logger.addHandler(ch)
# poe logging
poe.logger.setLevel(logging.WARNING)


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
        return self.get(
            self.prompt.format(
                query=query,
                data=self.format_cards(cards)
            )
        )


class PoeAPI:
    def __init__(self, queue_in, queue_out, token):
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.client = poe.Client(token)
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
        for chunk in self.client.send_message("a2", prompt):
            if first_message or full_message.endswith(': '):  # remove leading whitespace
                chunk["text_new"] = chunk["text_new"].lstrip()
                first_message = False
            yield chunk["text_new"]
            full_message += chunk["text_new"]
        del full_message  # clear memory
        yield None


class PoeScraper(FlashcardGPT):
    domain = b64decode('cG9lLmNvbQ==').decode()
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
        self.sess.headers.update(self.headers)
        # Get previous session
        if prev_sess := self.getSavedSession():
            self.token = prev_sess
            logger.info(f"Using saved session: {self.token}")
        else:
            self.token = self.registerAccount()
        self.poe_queue_in, self.poe_queue_out = Queue(), Queue()
        Process(target=PoeAPI, args=(self.poe_queue_in, self.poe_queue_out, self.token), daemon=True).start()
    
    def async_start(self):
        s_thread = Thread(target=self.start, daemon=True)
        s_thread.start()
        return s_thread
    
    def getSavedSession(self):
        if os.path.exists("poe_token.json"):
            with open("poe_token.json", "r") as f:
                token = json.load(f)['token']
            return token

    def verifyEmailListener(self):
        listen_queue = Queue()
        def listener(message):
            html = message['html'][0]
            soup = BeautifulSoup(html, 'lxml', parse_only=SoupStrainer('table'))
            code = re.search(r'\d+', soup.text)[0]
            listen_queue.put(code)

        logger.info("Registering email")
        # Get Domains
        test = Email()

        # Make new email address
        test.register()
        logger.info(f"Email Adress: {str(test.address)}")
        self.email_queue.put(test.address)

        # Start listening
        test.start(listener)
        self.email_queue.put(listen_queue.get())
        test.stop(); exit()  # Stop listening
        
    def registerAccount(self):
        self.email_queue = Queue()
        Process(target=self.verifyEmailListener, daemon=True).start()

        # Fetching settings
        logger.info("Starting session")
        self.sess.get(f'https://{self.domain}/login')
        # Update headers for internal api access
        self.sess.headers.update({
            "Accept": "*/*",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": f"https://{self.domain}/login",
        })
        # Getting api settings
        logger.info("Getting API settings")
        api_settings = self.sess.get(f'https://{self.domain}/api/settings').json()
        self.sess.headers.update({
            'Content-Type': 'application/json',
            'Poe-Formkey': api_settings['formkey'],
            'Poe-Tchannel': api_settings['tchannelData']['channel'],
        })
        
        def check_error(resp_data, data_name):
            if resp_data['data'][data_name].get('errorMessage'):
                logging.error(f"Error: {resp_data['data']['sendVerificationCode']['errorMessage']}")
                exit()
        
        # Send confirmation email
        logger.info("Sending confirmation email")
        address = self.email_queue.get()
        data0 = {
            "queryName": "MainSignupLoginSection_sendVerificationCodeMutation_Mutation",
            "variables": {
                "emailAddress": address,
                "phoneNumber": None
            },
            "query": "mutation MainSignupLoginSection_sendVerificationCodeMutation_Mutation(\n  $emailAddress: String\n  $phoneNumber: String\n) {\n  sendVerificationCode(verificationReason: login, emailAddress: $emailAddress, phoneNumber: $phoneNumber) {\n    status\n    errorMessage\n  }\n}\n"
        }
        signup_confirmation1 = self.sess.post(f'https://{self.domain}/api/gql_POST', json=data0).json()
        check_error(signup_confirmation1, 'sendVerificationCode')
            
        # Verifying email
        otp = self.email_queue.get()
        logger.info(f"Found verification code: {otp}")
        data1 = {
            "queryName": "SignupOrLoginWithCodeSection_signupWithVerificationCodeMutation_Mutation",
            "variables": {
                "emailAddress": address,
                "phoneNumber": None,
                "verificationCode": otp
            },
            "query": "mutation SignupOrLoginWithCodeSection_signupWithVerificationCodeMutation_Mutation(\n  $verificationCode: String!\n  $emailAddress: String\n  $phoneNumber: String\n) {\n  signupWithVerificationCode(verificationCode: $verificationCode, emailAddress: $emailAddress, phoneNumber: $phoneNumber) {\n    status\n    errorMessage\n  }\n}\n",
        }
        signup_confirmation2 = self.sess.post(f'https://{self.domain}/api/gql_POST', json=data1).json()
        check_error(signup_confirmation2, 'signupWithVerificationCode')
        
        # Save "p-b" cookie to token
        token = self.sess.cookies.get('p-b')
        
        logger.info(f"Saving token to file: {token}")
        
        with open('poe_token.json', 'w') as f:
            f.write(json.dumps({
                'token': token,
            }))
        
        logger.info("Success!")
        return token

    def get(self, prompt):
        # {'capybara': 'Sage', 'beaver': 'GPT-4', 'a2_2': 'Claude+', 'a2': 'Claude-instant', 'chinchilla': 'ChatGPT', 'nutria': 'Dragonfly'}
        self.poe_queue_in.put(prompt)
        
        while (data := self.poe_queue_out.get()) is not None:
            yield data


if __name__ == '__main__':
    chatgpt = PoeScraper()
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
