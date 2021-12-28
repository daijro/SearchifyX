# SearchifyX


**SearchifyX**, predecessor to *[Searchify](https://www.reddit.com/user/daijro/comments/jg7wee/searchify_quizletbrainly_searcher/)*, is a ***fast*** Quizlet, Quizizz, and Brainly webscraper with various stealth features.

<hr width=30>

#### SearchifyX in action

![in action](https://media.discordapp.net/attachments/714922631693860956/925164698058502175/ta1Y74Ehy8.gif)

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

---


### What it does

-   Searches Bing for Quizlet, Quizizz, and Brainly results

-   Sort results by how similar the identified question is to the input question

-   Various different options for input for stealthy use


### Stealth options

- Prevent window switching

- Customizable global hotkeys

    - Hide/show window hotkey

    - OCR & search hotkey

    - Paste & search hotkey

    - Quickly change window opacity hotkey

- Option to not show in taskbar


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