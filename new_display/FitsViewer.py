#! /usr/local/anaconda/bin/python
"""
FitsViewer -- FITS viewer using the Ginga toolkit and Qt widgets
              

Purpose:
        Simple FITS viewer

Usage:
        FitsViewer.py
Flags:
        None

Restrictions:
        None
    
Example:
        ./FitsViewer.py

Exit values:        
        0 = normal completion
        1 = wrong number of arguments

Modification history:
        2017-Apr-18     CA    Original version.
"""

import sys, os
import logging

from ginga import AstroImage
from ginga.misc import log
from ginga.qtw.QtHelp import QtGui, QtCore
from ginga.qtw.ImageViewCanvasQt import ImageViewCanvas

from ginga import GingaPlugin
from ginga.gw import Widgets
from Pick import *

#----------------#
# Define classes #
#----------------#

class FitsViewer(QtGui.QMainWindow):

    def __init__(self, logger):
        super(FitsViewer, self).__init__()
        self.logger = logger

        fi = ImageViewCanvas(self.logger, render='widget')
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        fi.set_callback('drag-drop', self.drop_file)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_setActive(True)
        fi.enable_draw(False)
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        w = fi.get_widget()
        w.resize(512, 512)

        vbox = QtGui.QVBoxLayout()
        vbox.setContentsMargins(QtCore.QMargins(2, 2, 2, 2))
        vbox.setSpacing(1)
        vbox.addWidget(w, stretch=1)

        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(QtCore.QMargins(4, 2, 4, 2))

        wopen = QtGui.QPushButton("Open File")
        wopen.clicked.connect(self.open_file)
        wquit = QtGui.QPushButton("Quit")
        wquit.clicked.connect(self.quit)
#        wpick = QtGui.QPushButton("Pick")
#        wpick.clicked.connect(Pick(fi))

        hbox.addStretch(1)
        for w in (wopen, wquit):
            hbox.addWidget(w, stretch=0)

        hw = QtGui.QWidget()
        hw.setLayout(hbox)
        vbox.addWidget(hw, stretch=0)

        vw = QtGui.QWidget()
        self.setCentralWidget(vw)
        vw.setLayout(vbox)

    def load_file(self, filepath):
        image = AstroImage.AstroImage(logger=self.logger)
        image.load_file(filepath)
        self.fitsimage.set_image(image)
        self.setWindowTitle(filepath)

    def open_file(self):
        res = QtGui.QFileDialog.getOpenFileName(self, "Open FITS file", \
                                                "/home/calvarez/Work/scripts/deimos/DEIMOS_FCS_Migration/new_fcs/sample_data", "FITS files (*.fits)")
        if isinstance(res, tuple):
            fileName = res[0]
        else:
            fileName = str(res)
        if len(fileName) != 0:
            self.load_file(fileName)

    def drop_file(self, fitsimage, paths):
        fileName = paths[0]
        self.load_file(fileName)

    def quit(self, *args):
        self.logger.info("Attempting to shut down the application...")
        self.deleteLater()


#--------------#
# Main program #
#--------------#

def main(options, args):

    app = QtGui.QApplication(sys.argv)

    # ginga needs a logger.
    # If you don't want to log anything you can create a null logger by
    # using null=True in this call instead of log_stderr=True
    logger = log.get_logger("fvlog", log_stderr=True)

    w1 = FitsViewer(logger)
    w1.resize(800, 133)
    w1.show()
    app.setActiveWindow(w1)
    w1.raise_()
    w1.activateWindow()

    if len(args) > 0:
        w1.load_file(args[0])

    app.exec_()

if __name__ == '__main__':
    main(None, sys.argv[1:])