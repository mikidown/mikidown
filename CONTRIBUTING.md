MikiDown Contrib Quick rundown
================================

# Issues = Bugs+Nags+Features+All

Go and stick it in on the github issues..

# Code
Create a pull request
- master = the current release
- develop = well.. all hell breaks loose....

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
Please provide a backtrace of the relevant errors ..
please complain... 


