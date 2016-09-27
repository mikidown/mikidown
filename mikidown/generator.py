"""
A simple static site generator for mikidown.
"""
import os
import sys
import shutil
from multiprocessing import Process
from threading import Thread

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
#from PyQt4.QtCore import QDir, QFile, QFileSystemWatcher, QIODevice, QSettings, QTextStream
#from PyQt4.QtGui import QApplication

import markdown
from .config import readListFromSettings, readDictFromSettings
from .utils import JSCRIPT_TPL


class Generator():

    def __init__(self, notebookPath):
        self.notebookPath = notebookPath
        self.notepath = os.path.join(notebookPath, "notes").replace(os.sep, '/')
        self.sitepath = os.path.join(notebookPath, "_site").replace(os.sep, '/')
        self.htmlpath = os.path.join(notebookPath, "_site/notes").replace(os.sep, '/')
        self.configfile = os.path.join(self.notebookPath, "notebook.conf").replace(os.sep, '/')
        self.qsettings = QtCore.QSettings(self.configfile, QtCore.QSettings.NativeFormat)
        self.extName = ['.md', '.mkd', '.markdown']
        if os.path.exists(self.configfile):
            extensions = readListFromSettings(self.qsettings,
                                                   "extensions")
            defExt = self.qsettings.value("fileExt")
            extCfg = readDictFromSettings(self.qsettings, "extensionsConfig")
            if defExt in self.extName:
                self.extName.remove(defExt)
                self.extName.insert(0, defExt)
                self.exts = extensions
                self.md = markdown.Markdown(extensions, extension_configs=extCfg)
        else:
            print("ERROR: Not a valid mikidown notebook folder")
            sys.exit(1)

    def generate(self):
        # clear sitepath
        self.count = 0
        if os.path.exists(self.sitepath):
            for file_object in os.listdir(self.sitepath):
                file_object_path = os.path.join(self.sitepath, file_object)
                if os.path.isfile(file_object_path):
                    os.unlink(file_object_path)
                else:
                    shutil.rmtree(file_object_path)
        QtCore.QDir().mkpath(self.htmlpath)
        self.initTree(self.notepath, "")

        # copy css and attachments folder
        cssSrcPath = os.path.join(self.notebookPath, "css")
        cssDstPath = os.path.join(self.sitepath, "css")
        attachSrcPath = os.path.join(self.notebookPath, "attachments")
        attachDstPath = os.path.join(self.sitepath, "attachments")
        shutil.copytree(cssSrcPath, cssDstPath)
        if os.path.exists(attachSrcPath):
            shutil.copytree(attachSrcPath, attachDstPath)

        print('Finished: Processed', self.count, 'notes.')

    def regenerate(self):

        def recursiveAddPath(filePath):
            """ recursively add files and directories to watcher """
            watcher.addPath(filePath)
            fileList = QtCore.QDir(filePath).entryInfoList(QtCore.QDir.Dirs | QtCore.QDir.Files | QtCore.QDir.NoDotAndDotDot)
            for f in fileList:
                recursiveAddPath(f.absoluteFilePath())

        def directoryChanged(filePath):
            watchedFiles = watcher.directories() + watcher.files()
            fileList = QtCore.QDir(filePath).entryInfoList(QtCore.QDir.Dirs | QtCore.QDir.Files | QtCore.QDir.NoDotAndDotDot)
            for f in fileList:
                if f.absoluteFilePath() not in watchedFiles:
                    watcher.addPath(f.absoluteFilePath())

            self.generate()

        # QFileSystemWatcher won't work without a QApplication!
        app = QtWidgets.QApplication(sys.argv)
        watcher = QtCore.QFileSystemWatcher()
        recursiveAddPath(self.notepath)

        # add/remove file triggers this
        watcher.directoryChanged.connect(directoryChanged)
        # edit file triggers this
        watcher.fileChanged.connect(self.generate)
        sys.exit(app.exec_())

    def preview(self, port=3131):
        processWatcher = Thread(target=self.regenerate)
        processWatcher.start()
        self.generate()

        from http.server import HTTPServer, SimpleHTTPRequestHandler

        HandlerClass = SimpleHTTPRequestHandler
        HandlerClass.protocol_version = "HTTP/1.1"
        ServerClass = HTTPServer
        server_address = ('', port)
        httpd = ServerClass(server_address, HandlerClass)
        sa = httpd.socket.getsockname()
        os.chdir(self.sitepath)
        print("Serving HTTP on", sa[0], "port", sa[1], "...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
            processWatcher.terminate()
            httpd.server_close()
            sys.exit(0)

    def initTree(self, notepath, parent):
        if parent == "":
        # site wide index page
            htmlfile = os.path.join(self.sitepath, "index.html")
        else:
        # append subpages to page
            htmlfile = os.path.join(self.htmlpath, parent + ".html")

        noteDir = QtCore.QDir(notepath)
        notesList = noteDir.entryInfoList(['*.md', '*.mkd', '*.markdown'],
                                          QtCore.QDir.NoFilter,
                                          QtCore.QDir.Name|QtCore.QDir.IgnoreCase)
        nl = [note.completeBaseName() for note in notesList]
        noduplicate = list(set(nl))
        noduplicate.sort(key=str.lower)
        htmlDir = os.path.join(self.htmlpath, parent)
        if len(noduplicate) > 0 and not QtCore.QDir(htmlDir).exists():
            QtCore.QDir().mkdir(htmlDir)

        children=[]

        for name in noduplicate:
            path = notepath + '/' + name
            filename = os.path.join(parent, name)

            for ext in self.extName:
                notefile = os.path.join(self.notepath, filename + ext)
                if QtCore.QFile.exists(notefile):
                    break

            chtmlfile = os.path.join(self.htmlpath, filename + ".html")
            self.convert(notefile, chtmlfile, path, os.path.join(parent,name))

            children.append('<li><a href="/notes/' + filename + '.html">' + name + '</a></li>')
            # append subpages to page

        if parent == "":
            self.writeIndex(htmlfile, children)

        return children

    def writeIndex(self, htmlfile, children):
        print(htmlfile, children)
        html = QtCore.QFile(htmlfile)
        html.open(QtCore.QIODevice.WriteOnly)
        savestream = QtCore.QTextStream(html)
        savestream.setCodec("UTF-8")
        savestream << '<html>\n<head>\n' \
                      '<meta charset="utf-8">\n' \
                      '<link rel="stylesheet" href="/css/notebook.css" type="text/css" />\n' \
                      '</head>\n'
        savestream << "<body>\n"
        savestream << "<h1>"
        savestream << "Mikidown Index"
        savestream << "</h1>"
        savestream << "<ul>\n"
        savestream << "\n".join(children)
        savestream << "</ul>\n"
        savestream << "</body>\n"
        savestream << "</html>\n"

        html.close()

    def convert(self, notefile, htmlfile, path, page):
        self.count += 1
        note = QtCore.QFile(notefile)
        note.open(QtCore.QIODevice.ReadOnly)
        html = QtCore.QFile(htmlfile)
        html.open(QtCore.QIODevice.WriteOnly)
        savestream = QtCore.QTextStream(html)
        savestream.setCodec("UTF-8")

        children = self.initTree(path, page)

        note_ts = QtCore.QTextStream(note)
        note_ts.setCodec("UTF-8" )

        savestream << '<html>\n<head>\n' \
                      '<meta charset="utf-8">\n' \
                      '<link rel="stylesheet" href="/css/notebook.css" type="text/css" />\n' \
                      '</head>\n'
        savestream << "<body>\n"
        savestream << "<header>" + self.breadcrumb(page) + "</header>\n"
        savestream << "<ul>\n"
        savestream << "\n".join(children)
        savestream << "</ul>\n"
        # Note content
        if 'asciimathml' in self.exts:
            savestream << JSCRIPT_TPL.format(self.qsettings.value('mathJax'))
        savestream << self.md.reset().convert(note_ts.readAll())
        savestream << "</body>\n"
        savestream << "</html>\n"
        note.close()
        html.close()

    def breadcrumb(self, page):
        """ Generate breadcrumb from page hierarchy.
            e.g. page github/mikidown will be shown as:
            <a>github</a> / <a>mikidown</a>
        """

        parts = page.split('/')
        crumb = ['<a href="/">Index</a>']
        for i, part in enumerate(parts):
            crumb.append(' / ')
            crumb.append('<a href="/notes/' + '/'.join(parts[0:i+1]) + '.html">' + part + '</a>')

        return ''.join(crumb)
