"""
A simple static site generator for mikidown.
"""
import os
import sys
import shutil
from multiprocessing import Process
from threading import Thread
from PyQt4.QtCore import QDir, QFile, QFileSystemWatcher, QIODevice, QSettings, QTextStream
from PyQt4.QtGui import QApplication
import markdown
from .config import readListFromSettings
from .utils import JSCRIPT_TPL


class Generator():

    def __init__(self, notebookPath):
        self.notebookPath = notebookPath
        self.notepath = os.path.join(notebookPath, "notes").replace(os.sep, '/')
        self.sitepath = os.path.join(notebookPath, "_site").replace(os.sep, '/')
        self.htmlpath = os.path.join(notebookPath, "_site/notes").replace(os.sep, '/')
        self.configfile = os.path.join(self.notebookPath, "notebook.conf").replace(os.sep, '/')
        self.qsettings = QSettings(self.configfile, QSettings.NativeFormat)
        self.extName = ['.md', '.mkd', '.markdown']
        if os.path.exists(self.configfile):
            extensions = readListFromSettings(self.qsettings,
                                                   "extensions")
            defExt = self.qsettings.value("fileExt")
            extCfg = self.qsettings.value("extensionsConfig")
            if defExt in self.extName:
                self.extName.remove(defExt)
                self.extName.insert(0, defExt)
                self.md = markdown.Markdown(extensions, extension_configs=extcfg)
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
        QDir().mkpath(self.htmlpath)
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
            fileList = QDir(filePath).entryInfoList(QDir.Dirs | QDir.Files | QDir.NoDotAndDotDot)
            for f in fileList:
                recursiveAddPath(f.absoluteFilePath())

        def directoryChanged(filePath):
            watchedFiles = watcher.directories() + watcher.files()
            fileList = QDir(filePath).entryInfoList(QDir.Dirs | QDir.Files | QDir.NoDotAndDotDot)
            for f in fileList:
                if f.absoluteFilePath() not in watchedFiles:
                    watcher.addPath(f.absoluteFilePath())

            self.generate()

        # QFileSystemWatcher won't work without a QApplication!
        app = QApplication(sys.argv)
        watcher = QFileSystemWatcher()
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
            self.convert(notefile, htmlfile, os.path.join(parent,name))
            self.initTree(path, os.path.join(parent,name))

            # append subpages to page
            savestream << '<li><a href="/notes/' + filename + '.html">' + name + '</a></li>'
        html.close()

    def convert(self, notefile, htmlfile, page):

        self.count += 1
        note = QFile(notefile)
        note.open(QIODevice.ReadOnly)
        html = QFile(htmlfile)
        html.open(QIODevice.WriteOnly)
        savestream = QTextStream(html)
        savestream << '<html><head>' \
                      '<meta charset="utf-8">' \
                      '<link rel="stylesheet" href="/css/notebook.css" type="text/css" />' \
                      '</head>'
        savestream << "<header>" + self.breadcrumb(page) + "</header>"
        # Note content
        if 'asciimathml' in self.md.registeredExtensions:
            savestream << JSCRIPT_TPL.format(self.qsettings.value('mathJax'))
        savestream << self.md.reset().convert(QTextStream(note).readAll())
        savestream << "</html>"
        note.close()
        html.close()

    def breadcrumb(self, page):
        """ Generate breadcrumb from page hierarchy.
            e.g. page github/mikidown will be shown as:
            <a>github</a> / <a>mikidown</a>
        """

        parts = page.split('/')
        crumb = '<a href="/">Index</a>'
        for i in range(len(parts)):
            crumb += ' / '
            crumb += '<a href="/notes/' + '/'.join(parts[0:i+1]) + '.html">' + parts[i] + '</a>'

        return crumb
