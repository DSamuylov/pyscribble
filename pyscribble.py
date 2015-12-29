#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pyscribble.py

Scribble image and create binary mask.

Usage:
    pyscribble.py
    pyscribble.py <path-img>

Arguments:
    <path-img>

Author: Denis Samuylov
Date: denis.samuylov@gmail.com
Last edited: December 2015

"""

import sys
import docopt
import PyQt4.QtGui as QtGui
from pyscribble.main import ControlWindow

if __name__ == '__main__':
    # Parse arguments from command line:
    args = docopt.docopt(__doc__)
    path_img = args["<path-img>"]
    # Run:
    app = QtGui.QApplication(sys.argv)
    cw = ControlWindow(path_img)
    sys.exit(app.exec_())
