# -*- coding: utf-8 -*-

import os
import glob

from fabric.api import env, local, run, cd, lcd, sudo, warn_only, prompt

HERE_PATH =  os.path.abspath( os.path.dirname( __file__ ))

def docs_build():
    """Build the documentation to temp/docs_build"""

    # copy some stuff
    #local("cp ./images/favicon.* ./api_docs/_static/")

    ## run build
    local("/usr/bin/python3 /usr/local/bin/sphinx-build -a  -b html ./api_docs/ ./build/api_docs")

def docs_gen_rst_index():
    """Generetes an .rst files for each py file in source cos sphinx is stupid"""

    ## The "files" and "namespace" we do not want to document
    no_docs = [
        "Qt", 
        "mikidown_rc"
    ]

    mikidown_api = []
    mdx = []

    ## Get a list of all the files in the mikidown/ dir
    ## Then generate and write the "automodule" .rst "index" stuff for sphinx
    for file in sorted(os.listdir("%s/mikidown" % HERE_PATH)):
        if file.endswith(".py"):
            fn = file[0:-3]

            if not fn in no_docs:
                
                s = "%s.*\n" % fn
                s += "===================================\n"
                s += ".. automodule:: mikidown.%s\n\n" % fn
                
                target = "%s/api_docs/api/%s.rst" % (HERE_PATH, fn)
                rstfile = open(target, "w")
                rstfile.write(s)
                rstfile.close()
                
                if fn[0:4] == "mdx_":
                    mdx.append(fn)
                else:
                    mikidown_api.append(fn)
                
    def make_write_toc(file_name, head, lst):
        s = "\n%s\n===================================\n\n" % head
        s += ".. toctree::\n"
        s += "\t:maxdepth: 1\n\n"
        
        for i in lst:
            s += "\tapi/%s.rst\n" % i
            
        s += "\n"
        
        f = open("%s/api_docs/%s" % (HERE_PATH, file_name), "w")
        f.write(s)
        f.close()
        
    make_write_toc("api_mikidown.rst", "Mikidown API", mikidown_api)
    make_write_toc("api_markdown.rst", "Markdown Extentions", mdx)
        

        
