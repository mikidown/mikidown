import os
from whoosh.fields import *
schema = Schema(path=TEXT(stored=True), content=TEXT)
indexdir = 'indexdir'
