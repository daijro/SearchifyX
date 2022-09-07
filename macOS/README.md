# SearchifyX for macOS

There now exists a native Swift app for macOS! It still uses Python for the scraping but the front-end/GUI is now native.
The only downsides to this version is that so far the stealth features are not available in this version.

## Building

To build this version of SearchifyX, you will need to only install the dependencies required for this version of SearchifyX listed in the [requirements.txt]() file:
```
$ python3 -m pip install -r requirements.txt
```

Then just run the build script from the macOS directory to build the latest version of [scraper.py]():
```
$ ./build.sh
```
> You may need to give the build and clean scripts the proper permissions to execute

That will build and compile the macOS app of scraper.py.
Now you can launch the Xcode project and build from there!