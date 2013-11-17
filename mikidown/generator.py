"""
A simple static site generator for mikidown.
"""
import os
import sys
import shutil
from multiprocessing import Process
from PyQt4.QtCore import QDir, QFile, QFileSystemWatcher, QIODevice, QSettings, QTextStream
from PyQt4.QtGui import QApplication
import markdown
from .config import readListFromSettings


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
        # QFileSystemWatcher won't work without a QApplication!
        app = QApplication(sys.argv)
        watcher = QFileSystemWatcher()
        watcher.addPath(self.notepath)
        watcher.directoryChanged.connect(self.generate)
        sys.exit(app.exec_())

    def preview(self, port=3131):
        processWatcher = Process(target=self.regenerate)
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
