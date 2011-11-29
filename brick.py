#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
brICk main python script 

author: Andreas Hartel
"""

import os, sys, shutil
import subprocess
# cannot use argparse, because it is not installed on valgol
import getopt
from brick_qt import *

BRICK_DIR = ''

# init
def init():
    output = []
    # find out brick dir
    if os.path.exists('./brick'):
        BRICK_DIR = os.getcwd()+'/brick'
    elif os.path.exists('./brICk'):
        BRICK_DIR = os.getcwd()+'/brICk'
    else:
        output.append("brick directory not found!")
        return output

    # name files to be linked 
    files_to_be_linked = [
        "wscript",
        "waf",
    ]

    # and directories to be created
    dirs_to_be_created = [
        "components",
        "rundirs",
    ]

    for file in files_to_be_linked:
        if os.path.exists(file):
            output.append("File "+file+" already installed, doing nothing")
        else:
            output.append("File "+file+" not found, linking it")
            subprocess.call(["ln","-s",BRICK_DIR+"/"+file])

    for dir in dirs_to_be_created:
        if os.path.exists(dir):
            output.append("Folder "+dir+" already exists, doing nothing")
        else:
            output.append("Folder "+dir+" not found, creating it")
            subprocess.call(["mkdir","-p",dir])

    # check if a config exists
    if os.path.exists('brick_config.xml'):
        pass
    else:
        output.append("No config file found. Copying default config file")
        shutil.copy(BRICK_DIR+"/config/default_config.xml","brick_config.xml")

    return output
# end of init

# configure
def configure(mode):
    output = []
    import datetime
    jetzt = datetime.datetime.now()
    cmd = './waf configure --mode '+mode+' --out rundirs/'+jetzt.strftime("%Y%m%d%H%M")
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    for line in p.stdout:
        output.append(line.rstrip())
    return output
# end of configure

# start gui
def start_gui():
    app = QtGui.QApplication(sys.argv)
    ex = Example(init,configure)
    sys.exit(app.exec_())
# end of start gui


# main
try:
    opts,args = getopt.getopt(sys.argv[1:],"h")
except getopt.GetoptError, err:
    print str(err)
    sys.exit(2)

# try to find out if user
# wants to start the GUI
try:
    args.index('gui')
    start_gui()
    # if this is the case, remove other args
    args = []
except ValueError:
    pass

# try to find out if user
# wants to init the project
try:
    args.index('init')
    output = init()
    for line in output:
        print line
except ValueError:
    pass

# try to find out if user
# wants to configure the project
try:
    index = args.index('configure')
    output = []
    try:
        output = configure(args[index+1])
    except IndexError:
        print "Please give a mode to configure for: build/functional"
        sys.exit(2)
    for line in output:
        print line
except ValueError:
    pass
