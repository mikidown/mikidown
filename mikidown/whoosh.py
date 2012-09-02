import os
from whoosh.fields import Schema, ID, TEXT
schema = Schema(path=ID(unique=True, stored=True), content=TEXT)
indexdir = 'indexdir'
