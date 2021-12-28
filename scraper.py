import json
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import json
import grequests
import re
import sys
import time
from urllib.parse import urlencode
from threading import Thread


headers = {
    "Connection": "keep-alive",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.53',
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Referer": "https://www.bing.com/",
    "Accept-Language": "en-US,en;q=0.9"
}


get_text  = lambda x: BeautifulSoup(x, features='lxml').get_text().strip()
sluggify  = lambda a: ' '.join(re.sub(r'[^\\sa-z0-9\\.,\\(\\)]+', ' ', a.lower()).split())
similar   = lambda a, b: SequenceMatcher(None, sluggify(a), sluggify(b)).ratio()
remove_duplicates = lambda a: list(set(a))



class SearchBing:
    """
    search bing for query
    """
    def __init__(self, query, sites):
        self.query = query
        self.links = None
        self.sites = sites
        self._regex_objs = {
            'quizlet': re.compile('https?://quizlet.com/\d+/[a-z0-9\\-]+/'),
            'quizizz': re.compile('https?://quizizz.com/admin/quiz/[a-f0-9]+/[a-z\\-]+'),
            'brainly': re.compile('https?://brainly.com/question/\d+'),
        }

    def search(self):
        """
        search bing for query
        """
        resps = dict(zip(
            self.sites,
            grequests.map([
                grequests.get(
                    'https://www.bing.com/search?'
                    + urlencode({'q': self.query + f' site:{site}.com'}),
                    headers=headers,
                )
                for site in self.sites
            ], size=len(self.sites))
        ))

        self.links = {
            site: remove_duplicates(re.findall(self._regex_objs[site], resps[site].text))
            for site in self.sites
        }
        


class QuizizzScraper:
    def __init__(self, links, query):
        self.links = links
        self.resps = None
        self.quizizzs = []
        self.query = query
    
    def async_requests(self, links):
        reqs = [grequests.get(u, headers=headers) for u in links]
        self.resps = grequests.map(reqs, size=len(reqs))

    def parse_links(self):
        links = ['https://quizizz.com/quiz/' + u.split('/')[-2] for u in self.links]
        self.async_requests(links)
        for resp in self.resps:
            try:
                self.quizizzs.append(self.quizizz_parser(resp))
            except Exception as e:
                print('exception', e, resp.url)
        return self.quizizzs


    def quizizz_parser(self, resp):
        data = resp.json()['data']['quiz']['info']
        return max(
            (
                {
                    'question': questr,
                    'answer': get_text(
                        question["structure"]["options"][
                            int(question["structure"]["answer"])
                        ]["text"]
                    )
                    or question["structure"]["options"][
                        int(question["structure"]["answer"])
                    ]["media"][0]["url"]
                    if question["type"] == "MCQ"
                    else ', '.join(
                        [
                            get_text(
                                question["structure"]["options"][int(answerC)]["text"]
                            )
                            or question["structure"]["options"][int(answerC)]["media"][0]["url"]
                            for answerC in question["structure"]["answer"]
                        ]
                    )
                    if question["type"] == "MSQ"
                    else None,
                    'similarity': (similar(questr, self.query), True),
                    'url': resp.url,
                }
                for questr, question in [
                    (get_text(x["structure"]["query"]["text"]), x)
                    for x in data["questions"]
                ]
            ),
            key=lambda x: x['similarity'],
        )



class QuizletScraper:
    def __init__(self, links, query):
        self.links = links
        self.resps = None
        self.quizlets = []
        self.query = query
        self._regex_obj = re.compile('\\= \\{"alphabeticalIsDifferent.*\\}; QLoad\\(')

    def async_requests(self, links):
        reqs = [grequests.get(u, headers=headers) for u in links]
        self.resps = grequests.map(reqs, size=len(reqs))

    def parse_links(self):
        self.async_requests(self.links)
        for resp in self.resps:
            try:
                self.quizlets.append(self.quizlet_parser(resp))
            except Exception as e:
                print('exception', e, resp.url)
                # pass # skip over any errors
        return self.quizlets


    def quizlet_parser(self, resp):
        data = json.loads(re.findall(self._regex_obj, resp.text)[0][2:-8]) # get quizlet headerData
        return max(
            (
                {
                    'question': i['word'].strip(),
                    'answer': i['definition'].strip(),
                    'similarity': max(
                        (similar(i[x], self.query), x == 'word')
                        # (similarity: float, is_term: bool)
                        for x in ['word', 'definition']
                    ),
                    'url': resp.url,
                }
                for i in data['termIdToTermsMap'].values()
            ),
            key=lambda x: x['similarity'],
        )



class BrainlyScraper:
    def __init__(self, links, query):
        self.links = links
        self.resps = None
        self.brainlys = []
        self.query = query

    def async_requests(self, links):
        reqs = [grequests.get(u, headers=headers) for u in links]
        self.resps = grequests.map(reqs, size=len(reqs))

    def parse_links(self):
        self.async_requests(self.links)
        for resp in self.resps:
            try:
                self.brainlys.append(self.brainly_parser(resp))
            except Exception as e:
                print('exception', e, resp.url)
                # pass # skip over any errors
        return self.brainlys


    def brainly_parser(self, resp):
        data = json.loads(BeautifulSoup(resp.text, features='lxml').find('script', type="application/ld+json").string)[0]
        answers = []
        if 'acceptedAnswer' in data['mainEntity']:
            answers += data['mainEntity']['acceptedAnswer']
        if 'suggestedAnswer' in data['mainEntity']:
            answers += data['mainEntity']['suggestedAnswer']

        return max(
            (
                {
                    'question': data['name'].strip(),
                    'answer': get_text(i['text'])
                        .replace('Answer:', 'Answer: ')
                        .replace('Explanation:', '\nExplanation: ')
                        + '\nUpvotes: '
                        + str(i['upvoteCount']),
                    'similarity': (
                        similar(data['name'], self.query),
                        True,
                        i['upvoteCount'],
                    ),
                    'url': resp.url,
                }
                for i in answers
            ),
            key=lambda x: x['similarity'],
        )




class TimeLogger:
    def __init__(self):
        self.elapsed_total = time.time()
        self.ongoing           = {}
        self.finished          = {}
        self.finished_threads  = {}

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
            print(
                '> Threads'.ljust(longest_len, " ") +
                ' \t= ' +
                (',\n'+longest_len*' ' + '  \t  ').join([
                    ': '.join([name.title(), str(round(time, 5))])
                    for name, time in self.finished_threads.items()
                ])
            )
        print('TOTAL ELAPSED'.ljust(longest_len, " ") + ' \t= ' + str(round(time.time() - self.elapsed_total, 5)))





class Searchify:
    def __init__(self, query, sites):
        self.query = query
        self.sites = sites
        self.timer = TimeLogger()
        self.flashcards = []
        self.links = []
        self.site_scrapers = {
            'quizlet': QuizletScraper,
            'quizizz': QuizizzScraper,
            'brainly': BrainlyScraper,
        }

    def main(self):
        self.get_links()
        threads = []
        for site in self.sites:
            threads.append(Thread(
                target=self._flashcard_thread,
                args=(
                    self.site_scrapers[site],
                    self.links[site],
                    site,
                )
            ))
            threads[-1].daemon = True
            self.timer.start(site)
            threads[-1].start()

        for n, T in enumerate(threads):
            T.join()
            print(f'Thread {n} finished')

        self.sort_flashcards()
        self.stop_time = time.time() - self.timer.elapsed_total
        

    def _flashcard_thread(self, site_scraper, links, site_name):
        self.flashcards += site_scraper(links, self.query).parse_links()
        self.timer.end(site_name, _thread_flag=True)


    def get_links(self):
        self.timer.start('bing search')
        search_bing = SearchBing(self.query, self.sites)
        search_bing.search()
        self.timer.end()
        self.links = search_bing.links


    def sort_flashcards(self):  # sourcery skip: for-index-replacement
        self.flashcards.sort(key=lambda x: x['similarity'], reverse=True)

        for card in range(len(self.flashcards)):
            if not self.flashcards[card]['similarity'][1]: # if cards and terms are swapped
                self.flashcards[card]['question'],  self.flashcards[card]['answer']   = (
                self.flashcards[card]['answer'],    self.flashcards[card]['question']   )

            self.flashcards[card]['similarity'] = str(round(self.flashcards[card]['similarity'][0] * 100, 2)) + '%'



if __name__ == '__main__' and len(sys.argv) > 1:
    # argument parsing
    import argparse
    parser = argparse.ArgumentParser(description='Search Bing for flashcards')
    parser.add_argument('--query',  '-q', help='query to search for',  default=None)
    parser.add_argument('--output', '-o', help='output file',          default=None)
    parser.add_argument('--sites',  '-s', help='question sources quizlet,quizizz,brainly (comma seperated list)', default='quizlet,quizizz,brainly')
    args = parser.parse_args()

    if args.output:
        f = open(args.output, 'w')
        write = f.write
    else:
        write = print

    if not args.query:
        print('No input specified')
        exit()

    # main program
    flashcards = [] # create flashcard list

    sites = args.sites.lower().split(',') # get list of sites

    # run search
    s = Searchify(
        query=args.query,
        sites=sites,
    )
    s.main()

    write(json.dumps(s.flashcards, indent=4))
    print(str(len(s.flashcards))+ ' flashcards found')

    s.timer.print_timers()