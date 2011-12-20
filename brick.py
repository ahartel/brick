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
from xml.dom import minidom
from brick_qt import *
sys.path.insert(0, os.path.join('./brick/source/waf'))
import brick_waf

class brickContainer:

    # init
    def __init__(self):
        self.BRICK_DIR = ''
        self.output = []
        self.config = {}
        self.__rundir = ''
        self.__mode = ''

        # find out brick dir
        if os.path.exists('./brick'):
            BRICK_DIR = os.getcwd()+'/brick'
        elif os.path.exists('./brICk'):
            BRICK_DIR = os.getcwd()+'/brICk'
        else:
            self.output.append("brick directory not found!")
            return

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
                self.output.append("File "+file+" already installed, doing nothing")
            else:
                self.output.append("File "+file+" not found, linking it")
                subprocess.call(["ln","-s",BRICK_DIR+"/"+file])

        for dir in dirs_to_be_created:
            if os.path.exists(dir):
                self.output.append("Folder "+dir+" already exists, doing nothing")
            else:
                self.output.append("Folder "+dir+" not found, creating it")
                subprocess.call(["mkdir","-p",dir])

        # check if a config exists
        if os.path.exists('brick_config.xml'):
            pass
        else:
            self.output.append("No config file found. Copying default config file")
            shutil.copy(BRICK_DIR+"/config/default_config.xml","brick_config.xml")

        # check if a state file exists
        if os.path.isfile('./.brick_info'):
            self.output.append(".brick_info file found. Loading state.")
            self.__load_state()
        else:
            self.output.append(".brick_info file not found.")

        self.__load_config()

        return
    # end of init

    def __load_config(self):
        xmlconfig = minidom.parse('./brick_config.xml') # parse an XML file by name
        self.config['projectname'] = brick_waf.getTextNodeValue(xmlconfig,'projectShortName')
        self.config['testcases'] = brick_waf.getTestCases(xmlconfig)

    def get_config_value(self,key):
        return self.config[key]


    # save state to file
    def __save_state(self):
        f = open('./.brick_info','w')
        f.write(self.__rundir+"\n")
        f.write(self.__mode+"\n")
        f.write(self.__testcase+"\n")
        f.write(self.__simulator+"\n")
        f.close()
    # end save state

    # load state from file
    def __load_state(self):
        f = open('./.brick_info','r')
        self.__rundir = f.readline().rstrip()
        self.__mode = f.readline().rstrip()
        self.__testcase = f.readline().rstrip()
        self.__simulator = f.readline().rstrip()
        f.close()
    # end save state

    # configure
    def configure(self,mode,rundir,testcase,simulator):
        # save variables in object fields and give them default values
        # rundir
        if not rundir:
            if not self.__rundir:
                self.output.append('No rundir was explecitly given. Setting rundir to current datetime string')
                import datetime
                jetzt = datetime.datetime.now()
                self.__rundir=jetzt.strftime("%Y%m%d%H%M")
        else:
            self.__rundir = rundir
        # mode
        if not mode:
            if not self.__mode:
                self.output.append('Please give a mode via the --mode option. Mode can be "build" or "functional"')
                return
        else:
            self.__mode = mode
        # testcase
        if testcase:
            self.__testcase = testcase

        if self.__mode == 'functional' and not self.__testcase:
            self.output.append("Testcase has to be given in mode 'functional'")
            return
        # simulator
        if not simulator:
            self.__simulator = 'cadence'
        else:
            self.__simulator = simulator

        cmd = ''
        if self.__mode == 'functional':
            cmd = './waf configure --mode '+self.__mode+' --out rundirs/'+self.__rundir+" --testcase "+self.__testcase+" --simulator "+self.__simulator
        else:
            cmd = './waf configure --mode '+self.__mode+' --out rundirs/'+self.__rundir

        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        for line in p.stdout:
            self.output.append(line.rstrip())

        self.__save_state()

        return
    # end of configure

    # build
    def build(self):
        cmd = './waf build'
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        for line in p.stdout:
            self.output.append(line.rstrip())
        return
    # end of build

    # run
    def run(self):
        cmd = './waf run'
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        for line in p.stdout:
            self.output.append(line.rstrip())
        return
    # end of run

    def flushOutput(self):
        returnOutput = "\n".join(self.output)
        self.output = []
        return returnOutput

# start gui
def start_gui(myBrick):
    app = QtGui.QApplication(sys.argv)
    ex = brickQT(myBrick)
    sys.exit(app.exec_())
# end of start gui

#
# main
#

# parse args and options
try:
    opts,args = getopt.getopt(sys.argv[1:],"h",["rundir=","mode=","testcase=","simulator="])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(2)
# initialize brick object
myBrick = brickContainer()
print myBrick.flushOutput()

# try to find out if user
# wants to start the GUI
try:
    args.index('gui')
    start_gui(myBrick)
    # if this is the case, remove other args
    args = []
except ValueError:
    pass

# try to find out if user
# wants to init the project
#try:
#    args.index('init')
#    output = init()
#    for line in output:
#        print line
#except ValueError:
#    pass

# try to find out if user
# wants to configure the project
try:
    index = args.index('configure')
    output = []
    mode = ''
    rundir = ''
    testcase = ''
    simulator = ''
    for opt in opts:
        if opt[0] == '--mode':
            mode = opt[1]
        elif opt[0] == '--rundir':
            rundir = opt[1]
        elif opt[0] == '--testcase':
            testcase = opt[1]
        elif opt[0] == '--simulator':
            simulator = opt[1]


    try:
        myBrick.configure(mode,rundir,testcase,simulator)
        print myBrick.flushOutput()
    except IndexError:
        print "Please give a mode to configure for: build/functional"
        sys.exit(2)
except ValueError:
    pass

# try to find out if user
# wants to build the project
try:
    args.index('build')
    myBrick.build()
    print myBrick.flushOutput()
except ValueError:
    pass

# try to find out if user
# wants to run the simulation
try:
    args.index('run')
    myBrick.run()
    print myBrick.flushOutput()
except ValueError:
    pass

