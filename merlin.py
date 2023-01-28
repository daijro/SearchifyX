import requests
import re
import json
import os
from random import randint
import logging
from queue import Queue

# logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')

# headers
class MerlinScraper:
    headers = {
        'authority': 'openai-api-yak3s7dv3a-ue.a.run.app',
        'accept': 'text/event-stream',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'dnt': '1',
        'origin': 'https://www.google.com',
        'referer': 'https://www.google.com/',
        'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }
    
    def __init__(self):
        self.setAccount()
    
    def setAccount(self):
        # make account
        if os.path.exists('merlin_id.bin'):
            with open('merlin_id.bin', 'r') as f:
                self.userid = f.read().strip()
            logging.debug(f'Account loaded from merin_id.bin: {self.userid}')
        else:
            self.userid = self.generateAccount()

    def generateAccount(self):  # sourcery skip: raise-specific-error
        logging.info('Generating Merlin account...')
        url = "https://us-central1-foyer-work.cloudfunctions.net:443/createMerlinFreeUser"
        acc_headers = {
            **self.headers,
            "content-type": "text/plain;charset=UTF-8",
            "accept": "*/*",
            "origin": "chrome-extension://camppjleccjaphfdbohjdohecfnoikec",
            "connection": "close"
        }
        userid = ''.join([hex(randint(0, 16))[-1] for _ in range(60)])
        payload = {"segmentation": "OPENAI_CHATGPT_VERSION", "userid": userid}
        r = requests.post(url, headers=acc_headers, json=payload)
        if r.status_code != 200:
            logging.critical('Error making account.')
            raise Exception(r.text)
        else:
            logging.info(f'Account created: {userid}')
            with open('merlin_id.bin', 'w') as f:
                f.write(userid)
        return userid

    def prompt(self, prompt, queue: Queue=None):
        assert self.userid is not None
        r = requests.get(
            "https://openai-api-yak3s7dv3a-ue.a.run.app/",
            headers=self.headers,
            params={
                'q': prompt.strip(),
                'userid': self.userid,
                'segmentation': 'OPENAI_CHATGPT_VERSION'
            },
            stream=True
        )
        all_text = ''
        for chunk in r.iter_content(chunk_size=1024):
            resp = re.search('{.*}', chunk.decode())
            if not resp:
                continue
            try:
                data = json.loads(resp[0])
            except json.decoder.JSONDecodeError:
                logging.critical(f'Error decoding JSON:\n{resp[0]}')
                continue
            if 'choices' not in data:
                continue
            if 'text' not in data['choices'][0]:
                continue
            text = data['choices'][0]['text']
            if not all_text:
                text = text.lstrip()
            queue and queue.put(text)
            print(text, end='')
            all_text += text
        queue and queue.put(None)
        print('')
        return all_text


if __name__ == "__main__":
    chatgpt = MerlinScraper()
    chatgpt.prompt('Hello, how are you?')