import logging
import os
import re
import sqlite3
import sys
import time
from contextlib import suppress
from itertools import chain
from random import choice, randint
from socket import inet_ntoa
from struct import pack
from threading import Thread

import hrequests
import orjson
import regex
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from jellyfish import jaro_distance as similar

# set logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S'))
logger.propagate = False
logger.addHandler(ch)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


google_domains = tuple(orjson.loads(open(resource_path('domains.json'), 'r').read()))


class _Utils:
    @staticmethod
    def get_text(s):
        with suppress(MarkupResemblesLocatorWarning):
            return BeautifulSoup(s, features='lxml').get_text().strip()

    @staticmethod
    def remove_duplicates(a):
        return list(set(a))

    @staticmethod
    def newIp():
        return {'X-Forwarded-For': inet_ntoa(pack(">I", randint(0x1000000, 0xDFA57FFF)))}


_web_engines = {
    'google': {
        'domain': 'https://www.google.com/',
        'query': 'q',
        'args': {'aqs': 'chrome..69i57.888j0j1', 'sourceid': 'chrome', 'ie': 'UTF-8'},
        'limit': 2038,
        'verify': False,
        'start_sess': False,
    },
    'bing': {
        'domain': 'https://www.bing.com/',
        'query': 'q',
        'args': {'lq': '0', 'ghsh': '0', 'ghacc': '0', 'ghpl': ''},
        'limit': 990,
        'verify': True,
        'start_sess': True,
    },
    'duckduckgo': {
        'domain': 'https://ddg-api.herokuapp.com/',
        'query': 'query',
        'args': {'limit': '10'},
        'limit': 490,
        'verify': False,
        'start_sess': False,
    },
}


class SearchEngine:
    def __init__(self, engine_name):
        self.engine_name = engine_name
        self.engine_data = _web_engines[engine_name]
        self.sess = hrequests.Session(verify=self.engine_data['verify'])
        self.sess.headers.update(
            {
                "Sec-Fetch-Site": "same-origin",
                'Referer': self.engine_data['domain'],
            }
        )
        logger.info('Starting instance...')
        self.t = None
        self.start_session()

    def start_session(self):
        if not self.engine_data['start_sess']:
            return
        self.t = self.sess.get(self.engine_data['domain'], nohup=True)

    def get_page(self, query, sites):
        if self.t is not None:
            self.t.join()
        # escape query sequence
        query = re.escape(query)
        if self.engine_name == 'google':
            self.sess.headers['Referer'] = self.engine_data[
                'domain'
            ] = f'https://www.google.{choice(google_domains)}/'

        reqs = [
            self.sess.async_get(
                (web_engine := self.engine_data)['domain'] + 'search',
                params={
                    web_engine[
                        'query'
                    ]: f"{query[:self.engine_data['limit']-len(site)]} site:{site}.com",
                    **web_engine['args'],
                },
            )
            for site in sites
        ]

        return dict(zip(sites, hrequests.map(reqs, size=len(sites))))


class SearchWeb:
    '''
    search web for query
    '''

    def __init__(self, query, sites, engine):
        self.query = query
        self.links = None
        self.sites = sites
        self.engine = engine
        self._regex_objs = {
            'quizlet': re.compile('https?://quizlet.com/\d+/[a-z\d\\-]+/'),
            'quizizz': re.compile('https?://quizizz.com/admin/quiz/[a-f0-9]+/[a-z\\-]+'),
        }

    def search(self):
        '''
        search web for query
        '''
        resps = self.engine.get_page(self.query, self.sites)
        if None in resps.values():
            raise Exception('Error searching web')
        self.links = {
            site: _Utils.remove_duplicates(re.findall(self._regex_objs[site], resps[site].text))
            for site in self.sites
        }


class QuizizzScraper:
    def __init__(self, links, query):
        self.links = links
        self.quizizzs = []
        self.query = query
        self.session = hrequests.Session()

    def async_requests(self):
        links = ['https://quizizz.com/quiz/' + u.split('/')[-2] for u in self.links]
        reqs = [self.session.async_get(u, headers=_Utils.newIp()) for u in links]
        return hrequests.imap_enum(reqs, size=len(reqs))

    def parse_links(self):
        resps = self.async_requests()
        for index, resp in resps:
            try:
                self.quizizzs.append(self.quizizz_parser(self.links[index], resp))
            except Exception as e:
                logger.info(f'Quizizz exception: {e} {resp.url}')
        return self.quizizzs

    def _get_answer(self, ans_item):
        answer = None
        if ans_item["text"]:
            answer = _Utils.get_text(ans_item["text"])
        elif not answer and ans_item.get("media"):
            answer = ans_item["media"][0]["url"]
        return answer

    def quizizz_parser(self, link, resp):
        data = resp.json()['data']['quiz']['info']
        questions = []
        for x in data["questions"]:
            if "query" not in x["structure"]:
                return questions
            questr = _Utils.get_text(x["structure"]["query"]["text"])
            question = x["structure"]
            if question["kind"] == "MCQ":
                ans_item = question["options"][int(question["answer"])]
                answer = self._get_answer(ans_item)
            elif question["kind"] == "MSQ":
                answers = []
                for answerC in question["answer"]:
                    ans_item = question["options"][int(answerC)]
                    answers.append(self._get_answer(ans_item))
                answer = ', '.join(answers)
            else:
                answer = "None"
            questions.append(
                {
                    'question': questr,
                    'answer': answer,
                    'similarity': (similar(questr, self.query), True),
                    'url': link,
                }
            )
        return questions


class QuizletScraper:
    def __init__(self, links, query):
        self.links = links
        self.quizlets = []
        self.query = query
        self.session = hrequests.Session()
        self._regex_obj = regex.compile(r"\[(?:[^\[\]]|(?R))*\]")

    def async_requests(self):
        reqs = [self.session.async_get(u, headers=_Utils.newIp()) for u in self.links]
        return hrequests.imap_enum(reqs, size=len(reqs))

    def parse_links(self):
        resps = self.async_requests()
        for index, resp in resps:
            try:
                self.quizlets.append(self.quizlet_parser(self.links[index], resp))
            except Exception as e:
                logger.info(f'Quizlet exception: {e} {resp.url}')
        return self.quizlets

    def quizlet_parser(self, link, resp):
        text = self._regex_obj.search(resp.text, pos=resp.text.index('hasPart'))[0]
        data = orjson.loads(text.encode('utf-8').decode('unicode_escape'))
        return [
            {
                'question': i['text'].strip(),
                'answer': i['acceptedAnswer']['text'].strip(),
                'similarity': max(
                    (similar(x, self.query), n == 0)
                    # (similarity: float, is_term: bool)
                    for n, x in enumerate((i['text'], i['acceptedAnswer']['text']))
                ),
                'url': link,
            }
            for i in data
        ]


class TimeLogger:
    def __init__(self):
        self.elapsed_total = time.time()
        self.ongoing = {}
        self.finished = {}
        self.finished_threads = {}

    def start(self, item):
        self.ongoing[item] = time.time()

    def end(self, item=-1, _thread_flag=False):
        if type(item) == int:
            item = list(self.ongoing)[item]
        if _thread_flag:
            self.finished_threads[item] = time.time() - self.ongoing.pop(item)
        else:
            self.finished[item] = time.time() - self.ongoing.pop(item)

    def print_timers(self):
        print('ELAPSED RUN TIMES:')
        longest_len = len(max(list(self.finished), key=lambda x: len(x)))
        for k, v in self.finished.items():
            print(f'> {k.title().ljust(longest_len, " ")} \t= {round(v, 5)}')
        if self.finished_threads:
            # fancy terminal printing
            print(
                '> Threads'.ljust(longest_len, " ")
                + ' \t= '
                + (',\n' + longest_len * ' ' + '  \t  ').join(
                    [
                        ': '.join([name.title(), str(round(time, 5))])
                        for name, time in self.finished_threads.items()
                    ]
                )
            )
        print(
            'TOTAL ELAPSED'.ljust(longest_len, " ")
            + ' \t= '
            + str(round(time.time() - self.elapsed_total, 5))
        )


class Searchify:
    def __init__(self, query, sites, engine=None):
        self.query = query
        self.sites = sites
        self.engine = engine  # optional if using offline mode
        self.timer = TimeLogger()
        self.flashcards = []
        self.unsaved_cards = []
        self.links = []
        self.site_scrapers = {
            'quizlet': QuizletScraper,
            'quizizz': QuizizzScraper,
        }
        # create database for saving flashcards
        self.con = sqlite3.connect(resource_path('flashcards.db'), check_same_thread=False)
        self.cur = self.con.cursor()
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS flashcards (question TEXT, answer TEXT, url TEXT, "
            "UNIQUE(question, answer, url) ON CONFLICT IGNORE)"
        )
        self.con.commit()
        # add function for character distance
        self.con.create_function("similar", 2, similar)
        self.con.commit()

    def main(self):
        self.get_links()
        threads = []
        for site in self.sites:
            thread = Thread(
                target=self._flashcard_thread,
                args=(
                    self.site_scrapers[site],
                    self.links[site],
                    site,
                ),
            )
            threads.append(thread)
            thread.daemon = True
            self.timer.start(site)
            thread.start()

        for n, T in enumerate(threads):
            T.join()
            logger.info(f'Thread finished ({n+1}/2)')

        self.sort_flashcards()
        self.stop_time = time.time() - self.timer.elapsed_total
        Thread(target=self.save_flashcards).start()  # save flashcards in background

    def _flashcard_thread(self, site_scraper, links, site_name):
        if items := site_scraper(links, self.query).parse_links():
            self.flashcards += [max(f, key=lambda x: x['similarity'][0]) for f in items if f]
            self.unsaved_cards += items
        self.timer.end(site_name, _thread_flag=True)

    def get_links(self):
        self.timer.start('web search')
        search_bing = SearchWeb(self.query, self.sites, self.engine)
        search_bing.search()
        self.timer.end()
        self.links = search_bing.links
        self.match_db()

    def match_db(self):
        # check if links are already in database
        for site in self.links:
            for url in self.links[site][:]:
                self.cur.execute("SELECT * FROM flashcards WHERE url=?", (url,))
                if not self.cur.fetchone():
                    continue  # skip if not in database
                self.links[site].remove(url)
                # get the top similar flashcard from the database
                self.cur.execute(
                    "SELECT * FROM flashcards WHERE url=? ORDER BY similar(question, ?) DESC LIMIT 1",
                    (url, self.query),
                )
                i = self.cur.fetchone()
                similar_score = (similar(i[0], self.query), True)
                self.flashcards.append(
                    dict(zip(('question', 'answer', 'url', 'similarity'), (*i, similar_score)))
                )

    def main_offline(self, amount=20):
        # drop in replacement for main() when offline. timers not supported
        self.cur.execute(
            f"SELECT * FROM flashcards ORDER BY similar(question, ?) DESC LIMIT {amount}",
            (self.query,),
        )
        self.flashcards = [
            {
                'question': i[0],
                'answer': i[1],
                'url': i[2],
                'similarity': f"{round(similar(i[0], self.query) * 100, 2)}%",
            }
            for i in self.cur.fetchall()
        ]

    def save_flashcards(self):
        self.cur.executemany(
            "INSERT INTO flashcards VALUES (?, ?, ?)",
            [
                (i['question'], i['answer'], i['url'])
                for i in chain.from_iterable(self.unsaved_cards)
            ],
        )
        self.con.commit()
        del self.unsaved_cards

    def sort_flashcards(self):  # sourcery skip: for-index-replacement
        self.flashcards.sort(key=lambda x: x['similarity'], reverse=True)

        for card in range(len(self.flashcards)):
            if not self.flashcards[card]['similarity'][1]:  # if cards and terms are swapped
                self.flashcards[card]['question'], self.flashcards[card]['answer'] = (
                    self.flashcards[card]['answer'],
                    self.flashcards[card]['question'],
                )

            self.flashcards[card]['similarity'] = (
                str(round(self.flashcards[card]['similarity'][0] * 100, 2)) + '%'
            )


if __name__ == '__main__' and len(sys.argv) > 1:
    # argument parsing
    import argparse

    parser = argparse.ArgumentParser(description='Search the web for flashcards')
    parser.add_argument('--query', '-q', help='query to search for', default=None)
    parser.add_argument('--output', '-o', help='output file', default=None)
    parser.add_argument(
        '--sites',
        '-s',
        help='question sources quizlet,quizizz (comma seperated list)',
        default='quizlet,quizizz',
    )
    parser.add_argument(
        '--engine', '-e', help='search engine to use', default='google', choices=_web_engines.keys()
    )
    parser.add_argument(
        '--chatgpt',
        '-gpt',
        help='summarize the results in ChatGPT (expiremental)',
        action='store_true',
    )
    parser.add_argument(
        '--search-db',
        '-db',
        help='search database n amount for flashcards. works offline',
        type=int,
        default=None,
    )
    args = parser.parse_args()

    if args.output:
        f = open(args.output, 'w')
        write = f.write
    else:
        write = print

    if not args.query:
        print('No input specified')
        exit()

    if args.chatgpt:
        from gpt.flashcardgpt import FlashcardGPT

        chatgpt = FlashcardGPT()
        s_thread = chatgpt.async_start()

    # main program
    flashcards = []  # create flashcard list

    sites = args.sites.lower().split(',')  # get list of sites
    engine_name = args.engine.lower().strip()  # get search engine

    # start search engine
    if args.search_db:
        s = Searchify(query=args.query, sites=sites)
        s.main_offline(args.search_db)
    else:
        engine = SearchEngine(engine_name)
        # run search
        s = Searchify(
            query=args.query,
            sites=sites,
            engine=engine,
        )
        s.main()

    write(orjson.dumps(s.flashcards, option=orjson.OPT_INDENT_2).decode())
    print(f'{len(s.flashcards)} flashcards found')

    not args.search_db and s.timer.print_timers()

    # get best answer with chatgpt
    if args.chatgpt and s.flashcards:
        print('\n' + '-' * 20 + '\nCHATGPT SUMMARIZATION:')
        s_thread.join()
        for chunk in chatgpt.run(args.query, s.flashcards[:10]):
            print(chunk, end='')
        print('')
