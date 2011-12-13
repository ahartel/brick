#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
brICk Qt4 GUI module 

author: Andreas Hartel
"""

import sys
from PyQt4 import QtGui, QtCore

class brickQT(QtGui.QMainWindow):

    def __updateTreeView(self):
        item = QtGui.QTreeWidgetItem(['hallo'])
        child = QtGui.QTreeWidgetItem(['kind'])
        item.addChild(child)
        self.topleft.insertTopLevelItem(0,item);

    @QtCore.pyqtSlot()
    def __handleBuild(self):
        output = self.buildFunction()
        self.__publish(output)

    @QtCore.pyqtSlot()
    def __handleRun(self):
        output = self.runFunction()
        self.__publish(output)

    def __publish(self,output):
        for line in output:
            self.topright.append(line)

    @QtCore.pyqtSlot()
    def __handleConfigure(self):
        modes = QtCore.QStringList()
        modes.append("build")
        modes.append("functional")

        input,ok = QtGui.QInputDialog.getItem(self,"Select build mode","Which mode do you want to configure?",modes,0,False)

        if ok:
            output = self.configureFunction(str(input),'','')
            self.__publish(output)

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
            self.__publish(output)

    def __init__(self,initFunction,configureFunction,buildFunction,runFunction):
        super(brickQT, self).__init__()

        self.initFunction = initFunction
        self.configureFunction = configureFunction
        self.buildFunction = buildFunction
        self.runFunction = runFunction
        self.initUI()

    def initUI(self):

        # top left
        self.topleft = QtGui.QTreeWidget(self)
        self.topleft.setColumnCount(1)
        self.topleft.setHeaderLabels([''])
        self.__updateTreeView()

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

        buildAction = QtGui.QAction('Build', self)
        buildAction.setShortcut('Alt+B')
        buildAction.setStatusTip('build sources')
        buildAction.triggered.connect(self.__handleBuild)

        runAction = QtGui.QAction('Run', self)
        runAction.setShortcut('Alt+R')
        runAction.setStatusTip('run simulation')
        runAction.triggered.connect(self.__handleRun)

        toolbar = QtGui.QToolBar(self)
        self.addToolBar(toolbar)
        toolbar.addAction(initAction)
        toolbar.addAction(configureAction)
        toolbar.addAction(buildAction)
        toolbar.addAction(runAction)
        toolbar.addAction(exitAction)

        splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(self.topleft)
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


