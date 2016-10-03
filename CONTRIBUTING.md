# Translating
* Change into the directory where the mikidown source code is
* Run ```pylupdate4 -verbose mikidown.pro```
* Replace all instances of ```filename="mikidown``` with ```filename="../mikidown``` 
in the generated locale/*.ts files
* Open Qt Linguist with those *.ts files.
* Start translating!
* Alternatively, you can visit <https://www.transifex.com/projects/p/mikidown/resources/> 
to see what needs to be translated. Any translations there will be pulled back into 
the github repo.

# Bug Reporting
Please provide a backtrace of the relevant errors like in #43. If it's a logic 
error (as in a variable's set to a wrong value), here's what you can do to help me
find the error (if I haven't found it yet):
* Find all of the relevant files you want to set breakpoints at
* Type this somewhere in that file, properly indented: `from .utils import debugTrace`
* Set some breakpoints by adding `debugTrace()` in said files. These should be placed just before the relevant variable changes to an unexpected value.
* Run the program with `python ./mikidown.py`
* When you get to the breakpoint, print out the variable values with `p ${relevantvariable}`

If you don't know how to do this, please describe in detail what you did in the GUI to
trigger the error (as in what buttons you pressed, etc.).

# Feature Requests
Stick them over in the github issues. It greatly helps if you have a detailed
list of steps and any mockups for the wanted changes.

Or if you prefer instant messaging of some sort, you can join the chat at
https://gitter.im/ShadowKyogre/mikidown

# Coding
Ideally, you should create a pull request so I can see what kinds of changes
you are making. Otherwise, you can put the patch in a pastebin so I can pick it
up from there. If you pick the pastebin option, please link to a pastebin that
has syntax highlighting. Also, here's a detailed list of branches and what they're for:

- master = The current release
- develop = Experimental features and fixes are here. Tread with caution, unless you like breaking stuff.

When you create a pull request, it should be based on `develop` since that's my main sandbox.

To avoid creating miscellaneous merge commit notes, you can follow the following steps
to always get the latest updates in your local working space
(( even if you've written on the `master` branch of your copy )).

~~~~
# get your repo
git clone https://github.com/${you}/mikidown

# add the upstream repo as an easily referrable remote
git remote add upstream https://github.com/shadowkyogre/mikidown

# if you want to pull commits from upstream master into your master 
# assuming you're currently on your master
git pull upstream master

# if you want to track upstream master separately
git checkout -b upmaster upstream/master

# if you want to track upstream develop separately
git checkout -b updevel upstream/develop
~~~~
