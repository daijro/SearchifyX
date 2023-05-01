from requests import Session
import logging
import orjson
from multiprocessing import Queue, Process
import re
import json
from threading import Thread
import os
import logging
from base64 import b64decode
import poe
import asyncio
from pyppeteer import launch
from fake_headers import Headers
import time


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
        self.client.send_chat_break('a2')  # clear context
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


class PoeAccountGenerator:
    domain = b64decode('cG9lLmNvbQ==').decode()

    def verifyEmailListener(self):
        logger.info("Registering email...")
        emailnator = Emailnator()
        address = emailnator.get_address()
        logger.info(f"Email Address: {address}")
        self.email_queue.put(address)
        # start listening
        otp = emailnator.get_verification_code()
        logger.info(f"Verification Code: {otp}")
        self.email_queue.put(otp)
        del emailnator  # cleanup
        
    async def registerAccount(self):
        self.email_queue = Queue()
        Thread(target=self.verifyEmailListener, daemon=True).start()

        logger.info("Launching browser...")
        browser = await launch(options={'args': ['--no-sandbox']})
        page = (await browser.pages())[0]
        
        await page.goto(f'https://{self.domain}/login')
        # Click "Use email"
        flat_btn = 'button.Button_flat__1hj0f.undefined'
        prim_btn = 'button.Button_primary__pIDjn.undefined'
        await page.waitForSelector(flat_btn)
        await page.click(flat_btn)
        # Enter email and press Go
        await page.type('input[type=email]', self.email_queue.get())
        await page.click('button.Button_primary__pIDjn.undefined')
        # Enter verification code
        verif_inp = 'input.VerificationCodeInput_verificationCodeInput__YD3KV'
        await page.waitForSelector(verif_inp)
        logger.info("Waiting for verification code...")
        await page.type(verif_inp, self.email_queue.get())
        await page.click(prim_btn)  # login
        # Wait for navigation, save "p-b" cookie
        await page.waitForNavigation()
        cookies = await page.cookies()
        # Find p-b cookie
        for cookie in cookies:
            if cookie['name'] == 'p-b':
                token = cookie['value']
                break
        else:
            raise Exception("Could not find p-b cookie")
        await browser.close()
        logger.info(f"Saving token to file: {token}")
        
        with open('poe_token.json', 'w') as f:
            f.write(json.dumps({
                'token': token,
            }))
        logger.info("Success!")
        return token

    def runEventLoop(self, out: Queue):
        token = asyncio.get_event_loop().run_until_complete(self.registerAccount())
        out.put(token)

    def run(self):
        queue = Queue(maxsize=1)
        Process(target=self.runEventLoop, args=(queue,), daemon=True).start()
        return queue.get()


class Emailnator:
    domain = b64decode("d3d3LmVtYWlsbmF0b3IuY29t").decode()

    def __init__(self):
        self.client = Session()
        self.client.get(f"https://{self.domain}/", timeout=6)
        self.cookies = self.client.cookies.get_dict()
        self.client.headers = {
            "authority": self.domain,
            "origin": f"https://{self.domain}",
            "referer": f"https://{self.domain}/",
            "user-agent": Headers().generate()['User-Agent'],
            "x-xsrf-token": self.client.cookies.get("XSRF-TOKEN")[:-3] + "=",
        }
        self.email = None

    def get_address(self):
        resp = self.client.post(
            f"https://{self.domain}/generate-email",
            json={
                "email": ["plusGmail", "dotGmail"]
            },
        )
        self.email = resp.json()["email"][0]
        return self.email

    def get_message(self):
        while True:
            time.sleep(1.5)
            mail_token = self.client.post(
                f"https://{self.domain}/message-list", json={"email": self.email}
            )
            mail_token = mail_token.json()["messageData"]
            if len(mail_token) == 2:
                break
        mail_context = self.client.post(
            f"https://{self.domain}/message-list",
            json={
                "email": self.email,
                "messageID": mail_token[1]["messageID"],
            },
        )
        return mail_context.text

    def get_verification_code(self):
        message = self.get_message()
        code = re.findall(r';">(\d{6,7})</div>', message)[0]
        logging.info(f"Verification code: {code}")
        return code

    def clear_inbox(self):
        self.client.post(
            f"https://{self.domain}/delete-all",
            json={"email": self.email},
        )

    def __del__(self):
        if self.email:
            self.clear_inbox()


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
        if prev_sess := self.getSavedSession():
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
    
    def getSavedSession(self):
        if os.path.exists("poe_token.json"):
            with open("poe_token.json", "r") as f:
                token = json.load(f)['token']
            return token

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
