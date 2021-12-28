# SearchifyX


**SearchifyX**, predecessor to *[Searchify](https://www.reddit.com/user/daijro/comments/jg7wee/searchify_quizletbrainly_searcher/)*, is a ***fast*** Quizlet, Quizizz, and Brainly webscraper with various stealth features.

<hr width=30>

#### SearchifyX in action

![in action](https://user-images.githubusercontent.com/72637910/147515480-236fe392-6282-44bc-b888-54f15adeb523.gif)


<hr width=30>

## Download

Windows binaries are not avaliable yet at this moment.

Here are the [python 3.8](https://www.python.org/downloads/release/python-389/) dependencies:

```
PyQt5
pywin32
keyboard
grequests
beautifulsoup4
pytesseract
pyperclip
```

You also need to download [tesseract-ocr](https://cdn.discordapp.com/attachments/714922631693860956/925180968808087572/tesseract-ocr.7z) and extract it to the root directory to use OCR.

<hr width=30>

## CLI usage

An alternative for Linux/Mac OS users is to use [`scraper.py`](https://github.com/daijro/SearchifyX/blob/main/scraper.py) as a CLI tool.

Usage:
```
scraper.py [-h] [--query QUERY] [--output OUTPUT] [--sites SITES]
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
                      question sources quizlet,quizizz,brainly (comma seperated list)
```

---


### What it does

-   Searches Bing for Quizlet, Quizizz, and Brainly results

-   Sort results by how similar the identified question is to the input question

-   Various different options for input for stealthy use

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

Many websites can detect when the window focus is lost. SearchifyX includes features such as hotkeys and a __window switching safety lock__ to prevent websites from knowing your are using a differenty window.

*Note: The text search bar does not work when the Window switch safety lock is enabled. It is designed to be used with the OCR tool and Paste & Search tool.*

Here is a [demo website](https://www.codingwithjesse.com/demo/2007-05-16-detect-browser-window-focus/) that turns black when the window is out of focus:

![window safety lock](https://i.imgur.com/mGBAV1K.gif)


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
