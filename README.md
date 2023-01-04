# SearchifyX


**SearchifyX**, predecessor to *[Searchify](https://www.reddit.com/user/daijro/comments/jg7wee/searchify_quizletbrainly_searcher/)*, is a ***fast*** Quizlet, Quizizz, and Brainly webscraper with various stealth features.

SearchifyX lets you easily query a question through different answer websites *(similar to Socratic on mobile)*, and sort them based on how similar they are to your query. It also includes a screen OCR scanner, hotkeys, and other features for stealthy use.


<hr width=30>

#### SearchifyX in action

![in action](https://user-images.githubusercontent.com/72637910/147515480-236fe392-6282-44bc-b888-54f15adeb523.gif)


---

## Download

### Binaries

Download Windows binaries [here](https://github.com/daijro/SearchifyX/releases)

### Running from source code

Install the [Python 3.8](https://www.python.org/downloads/release/python-389/) dependencies:

```
python -m pip install -r requirements.txt
```

You also need to [install](https://www.dropbox.com/s/abuo044ayx4vlex/tesseract-ocr.7z?dl=1) Tesseract to use the OCR tool, or *download and extract* the [portable archive](https://www.dropbox.com/s/abuo044ayx4vlex/tesseract-ocr.7z?dl=1) to the root directory.

<hr width=30>

## CLI usage

An alternative for Linux/Mac OS users is to use [`scraper.py`](https://github.com/daijro/SearchifyX/blob/main/scraper.py) as a CLI tool.

Usage:
```
scraper.py [-h] [--query QUERY] [--output OUTPUT] [--sites SITES] [--engine {google,bing,startpage,duckduckgo}]
```

Required arguments:

```
--query QUERY, -q QUERY
                      query to search for
```

Optional arguments:

```
-h, --help            show this help message and exit

--output OUTPUT, -o OUTPUT
                      output file (optional)
--sites SITES, -s SITES
                      question sources quizlet,quizizz (comma seperated list)
--engine ENGINE, -e ENGINE
                      search engine to use
```

---


## What it does

-   Searches online for Quizlet and Quizizz results

-   Sort results by how similar the identified question is to the input question

<hr width=30>

### Stealth options

- Prevent window switching

- Customizable global hotkeys

    - Hide/show window hotkey

    - OCR & search hotkey

    - Paste & search hotkey

    - Quickly change window opacity hotkey

- Change window opacity (slider in title bar)

- Option to not show in taskbar

<hr width=30>


### Window switching safety lock

Many websites can detect when the window focus is lost. SearchifyX includes a __window switching safety lock__ to prevent websites from knowing you are using a different window.


Here is a [demo website](https://www.codingwithjesse.com/demo/2007-05-16-detect-browser-window-focus/) that turns black when the window is out of focus:

![window safety lock](https://i.imgur.com/mGBAV1K.gif)

<hr width=30>

### Improvements from *Searchify*

- Completely rewritten from scratch

- Added stealth features ([listed above](https://github.com/daijro/SearchifyX#stealth-options))

- Added screen OCR scanner

- Added global hotkeys

- *Major* changes to UI

- *Major* changes web scraper code (averages 1-2 seconds now; uses significantly less CPU)

- Completely fixed the "Too many requests" error

- Significantly more stable & returns better results

---

## Interface


#### Dark theme

![dark mode](https://i.imgur.com/AjFaiJY.png)

<hr width=30>

#### Light theme

![light mode](https://i.imgur.com/NISQ8oX.png)

<hr width=30>

#### Settings page

![settings](https://i.imgur.com/iOciyxd.png)


---

### Disclaimer

The purpose of this program is to provide an example of asynchronous webscraping and data gathering in Python. I am not in any way attempting to promote cheating, and I am not responsible for any misuse of this tool. This tool was created strictly for educational purposes only.
