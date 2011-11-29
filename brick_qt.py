#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
brICk Qt4 GUI module 

author: Andreas Hartel
"""

import sys
from PyQt4 import QtGui, QtCore

class Example(QtGui.QMainWindow):

    @QtCore.pyqtSlot()
    def __handleConfigure(self):
        modes = QtCore.QStringList()
        modes.append("build")
        modes.append("functional")

        input,ok = QtGui.QInputDialog.getItem(self,"Select build mode","Which mode do you want to configure?",modes,0,False)

        if ok:
            output = self.configureFunction(str(input))
            for line in output:
                self.topright.append(line)

    @QtCore.pyqtSlot()
    def __handleInit(self):
        msgBox = QtGui.QMessageBox()
        msgBox.setInformativeText("Do you really want to initialize brick in this project?")
        msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        msgBox.setDefaultButton(QtGui.QMessageBox.Yes )
        ret = msgBox.exec_()

        if ret == QtGui.QMessageBox.No:
            pass
        elif ret == QtGui.QMessageBox.Yes:
            output = self.initFunction()
            for line in output:
                self.topright.append(line)

    def __init__(self,initFunction,configureFunction):
        super(Example, self).__init__()

        self.initFunction = initFunction
        self.configureFunction = configureFunction
        self.initUI()

    def initUI(self):

        # top left
        topleft = QtGui.QTreeWidget(self)
#        topleft.setFrameShape(QtGui.QFrame.StyledPanel)

        # top right
        self.topright = QtGui.QTextEdit(self)
#        topright.setFrameShape(QtGui.QFrame.StyledPanel)

        # bottom status bar
        self.statusBar()
        # top toolbar
        exitAction = QtGui.QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        initAction = QtGui.QAction('Init', self)
        initAction.setShortcut('Alt+I')
        initAction.setStatusTip('Init brICk')
        initAction.triggered.connect(self.__handleInit)

        configureAction = QtGui.QAction('(Re-)configure', self)
        configureAction.setShortcut('Alt+C')
        configureAction.setStatusTip('configure brICk')
        configureAction.triggered.connect(self.__handleConfigure)

        toolbar = QtGui.QToolBar(self)
        self.addToolBar(toolbar)
        toolbar.addAction(initAction)
        toolbar.addAction(configureAction)
        toolbar.addAction(exitAction)

        splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(topleft)
        splitter1.addWidget(self.topright)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(splitter1)
        mainFrame = QtGui.QFrame(self)
        mainFrame.setLayout(hbox)
        self.setCentralWidget(mainFrame)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('brICk')
        self.show()


