"""
A simple static site generator for mikidown.
"""
import os
import sys
import shutil
from PyQt4.QtCore import *
import markdown
from mikidown.config import readListFromSettings


class Generator():

    def __init__(self, notebookPath):
        self.notebookPath = notebookPath
        self.notepath = os.path.join(notebookPath, "notes")
        self.sitepath = os.path.join(notebookPath, "_site")
        self.htmlpath = os.path.join(notebookPath, "_site/notes")
        self.configfile = os.path.join(self.notebookPath, "notebook.conf")
        self.qsettings = QSettings(self.configfile, QSettings.NativeFormat)
        self.extName = ['.md', '.mkd', '.markdown']
        if os.path.exists(self.configfile):
            self.count = 0
            extensions = readListFromSettings(self.qsettings,
                                                   "extensions")
            defExt = self.qsettings.value("fileExt")
            if defExt in self.extName:
                self.extName.remove(defExt)
                self.extName.insert(0, defExt)
                self.md = markdown.Markdown(extensions)
        else:
            print("ERROR: Not a valid mikidown notebook folder")
            sys.exit(1)

    def generate(self):
        if os.path.exists(self.sitepath):
            shutil.rmtree(self.sitepath)
        QDir().mkpath(self.htmlpath)
        self.initTree(self.notepath, "")

        # copy css and attachments folder
        cssSrcPath = os.path.join(self.notebookPath, "css")
        cssDstPath = os.path.join(self.sitepath, "css")
        attachSrcPath = os.path.join(self.notebookPath, "attachments")
        attachDstPath = os.path.join(self.sitepath, "attachments")
        shutil.copytree(cssSrcPath, cssDstPath)
        shutil.copytree(attachSrcPath, attachDstPath)

        print('Finished: Processed', self.count, 'notes.')

    def initTree(self, notepath, parent):
        if parent == "":
        # site wide index page
            htmlfile = os.path.join(self.sitepath, "index.html")
        else:
        # append subpages to page
            htmlfile = os.path.join(self.htmlpath, parent + ".html")
        html = QFile(htmlfile)
        html.open(QIODevice.Append)
        savestream = QTextStream(html)

        noteDir = QDir(notepath)
        notesList = noteDir.entryInfoList(['*.md', '*.mkd', '*.markdown'],
                                          QDir.NoFilter,
                                          QDir.Name|QDir.IgnoreCase)
        nl = [note.completeBaseName() for note in notesList]
        noduplicate = list(set(nl))
        noduplicate.sort(key=str.lower)
        htmlDir = os.path.join(self.htmlpath, parent)
        if len(noduplicate) > 0 and not QDir(htmlDir).exists():
            QDir().mkdir(htmlDir)

        for name in noduplicate:
            path = notepath + '/' + name 
            filename = os.path.join(parent, name)
            for ext in self.extName:
                notefile = os.path.join(self.notepath, filename + ext)
                if QFile.exists(notefile):
                    break
            htmlfile = os.path.join(self.htmlpath, filename + ".html")
            #print(notefile, htmlfile)
            self.convert(notefile, htmlfile)
            self.initTree(path, os.path.join(parent,name))

            # append subpages to page
            savestream << '<li><a href="/notes/' + filename + '.html">' + name + '</a></li>'
        html.close()

    def convert(self, notefile, htmlfile):
        self.count += 1
        note = QFile(notefile)
        note.open(QIODevice.ReadOnly)
        html = QFile(htmlfile)
        html.open(QIODevice.WriteOnly)
        savestream = QTextStream(html)
        savestream << """
                        <html><head>
                          <meta charset='utf-8'>
                          <link rel='stylesheet' href='/css/notebook.css' type='text/css' />
                        </head>
                      """
        # Note content
        savestream << self.md.convert(QTextStream(note).readAll())
        savestream << "</html>"
        note.close()
        html.close()
