"""
Poe account generator
Requires playwright, fake-useragent, requests

This project is made to be used with poe-api
https://github.com/ading2210/poe-api

== USAGE ==
1.  Imports:
    >>> import poe  # pip install poe-api
    >>> from poegen import generate_token  # this file
2.  Generate a token (PLEASE don't abuse this!)
    >>> token = generate_token()
3.  Use token in poe-api
    >>> client = poe.Client(token)
"""


import json
import logging
import os
import re
import time
from base64 import b64decode
from multiprocessing import Process, Queue
from threading import Thread

from fake_useragent import UserAgent
from playwright.sync_api import sync_playwright
from requests import Session


class PoeAccountGeneratorException(Exception):
    pass


class PoeAccountGenerator:
    domain = b64decode('cG9lLmNvbQ==').decode()

    def verifyEmailListener(self):
        logging.info("Registering email...")
        emailnator = Emailnator()
        address = emailnator.get_address()
        logging.info(f"Email Address: {address}")
        self.email_queue.put(address)
        # start listening
        otp = emailnator.get_verification_code()
        logging.info(f"Verification Code: {otp}")
        self.email_queue.put(otp)
        del emailnator  # cleanup

    def registerAccount(self, playwright):
        self.email_queue = Queue()
        Thread(target=self.verifyEmailListener, daemon=True).start()

        logging.info("Launching browser...")
        browser = playwright.firefox.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(f'https://{self.domain}/login')
        # Click "Use email"
        flat_btn = 'button.Button_flat__1hj0f.undefined'
        prim_btn = 'button.Button_primary__pIDjn.undefined'
        email_inp = 'input[type=email]'
        if not page.is_visible(email_inp):
            page.click(flat_btn)
        # Enter email and press Go
        page.type(email_inp, self.email_queue.get())
        page.click(prim_btn)
        # Enter verification code
        verif_inp = 'input.VerificationCodeInput_verificationCodeInput__YD3KV'
        logging.info("Waiting for verification code...")
        page.type(verif_inp, self.email_queue.get())
        page.click(prim_btn)  # login
        # Wait for navigation, save "p-b" cookie
        page.wait_for_load_state()
        cookies = context.cookies()
        # Find p-b cookie
        for cookie in cookies:
            if cookie['name'] == 'p-b':
                token = cookie['value']
                break
        else:
            raise PoeAccountGeneratorException("Could not find p-b cookie")
        browser.close()

        self.saveSession(token)
        logging.info("Success!")
        return token

    @staticmethod
    def saveSession(token):
        logging.info(f"Saving token to file: {token}")
        with open('poe_token.json', 'w') as f:
            f.write(json.dumps({
                'token': token,
            }))

    @staticmethod
    def getSavedSession():
        if os.path.exists("poe_token.json"):
            with open("poe_token.json", "r") as f:
                token = json.load(f)['token']
            return token

    def runEventLoop(self, out: Queue):
        with sync_playwright() as playwright:
            token = self.registerAccount(playwright)
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
            "user-agent": UserAgent().random,
            "x-xsrf-token": self.client.cookies.get("XSRF-TOKEN")[:-3] + "=",
        }
        self.email = None

    def get_address(self):
        resp = self.client.post(
            f"https://{self.domain}/generate-email",
            json={
                "email": ["domain", "plusGmail", "dotGmail"]
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


def generate_token():
    poegen = PoeAccountGenerator()
    if prev_sess := poegen.getSavedSession():
        return prev_sess
    else:
        return poegen.run()
