"""
Poe account generator
Requires hrequests, mailtm

This project is made to be used with poe-api
https://github.com/ading2210/poe-api

== USAGE ==
1.  Imports:
    >>> import poe  # pip install poe-api
    >>> from poegen import generate_token  # this file
2.  Generate a token
    >>> token = generate_token()
3.  Use token in poe-api
    >>> client = poe.Client(token)
"""


import json
import logging
import os
import re
import sys
from base64 import b64decode
from queue import Queue
from threading import Thread

import hrequests
from mailtm import Email


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


class PoeAccountGeneratorException(Exception):
    pass


class PoeAccountGenerator:
    domain = b64decode('cG9lLmNvbQ==').decode()
    flat_btn = 'button.Button_flat__1hj0f.undefined'
    prim_btn = 'button.Button_primary__pIDjn.undefined'
    email_inp = 'input[type=email]'

    def __init__(self):
        # logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S'))
        self.logger.addHandler(ch)

    def verifyEmailListener(self, email_queue: Queue):
        listen_queue = Queue()

        def listener(message):
            txt = message['html'][0] or message['text']
            otp = re.search(r';">(\d{6,7})</div>', txt)[1]
            self.logger.info(f"Verification Code: {otp}")
            listen_queue.put(otp)

        # create new email
        test = Email()
        test.register()
        self.logger.info(f"Email Address: {str(test.address)}")
        email_queue.put(test.address)

        # start listening
        test.start(listener)
        email_queue.put(listen_queue.get())
        test.stop()  # stop

    def registerAccount(self):
        email_queue = Queue()
        Thread(target=self.verifyEmailListener, args=(email_queue,), daemon=True).start()

        self.logger.info("Launching browser...")
        page = hrequests.BrowserSession(mock_human=True, headless=True)
        page.url = f'https://{self.domain}/login'
        # Click "Use email"
        if not page.isVisible(self.email_inp):
            page.click(self.flat_btn)
        # Enter email and press Go
        page.type(self.email_inp, email_queue.get(), delay=15)
        page.awaitEnabled(self.prim_btn)
        page.click(self.prim_btn)
        # Enter verification code
        verif_inp = 'input.VerificationCodeInput_verificationCodeInput__YD3KV'
        self.logger.info("Waiting for verification code...")
        page.type(verif_inp, email_queue.get())
        page.click(self.prim_btn)  # login
        # Wait for navigation, save "p-b" cookie
        page.awaitNavigation()
        cookies = page.cookies
        # Find p-b cookie
        for cookie in cookies:
            if cookie.name == 'p-b':
                token = cookie.value
                break
        else:
            raise PoeAccountGeneratorException("Could not find p-b cookie")
        page.close()

        self.logger.info(f"Saving token to file: {token}")
        self.saveSession(token)
        self.logger.info("Success!")
        return token

    @staticmethod
    def saveSession(token):
        with open(resource_path('poe_token.json'), 'w') as f:
            f.write(json.dumps({
                'token': token,
            }))

    @staticmethod
    def getSavedSession():
        path = resource_path('poe_token.json')
        if os.path.exists(path):
            with open(path, "r") as f:
                token = json.load(f)['token']
            return token

    def runEventLoop(self, out: Queue):
        token = self.registerAccount()
        out.put(token)

    def run(self):
        queue = Queue(maxsize=1)
        Thread(target=self.runEventLoop, args=(queue,)).start()
        return queue.get()


def generate_token():
    poegen = PoeAccountGenerator()
    if prev_sess := poegen.getSavedSession():
        return prev_sess
    else:
        return poegen.run()


if __name__ == '__main__':
    generate_token()