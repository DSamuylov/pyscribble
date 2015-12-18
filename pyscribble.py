#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pyscribble.py

Scribble image and create binary mask.

Usage:
    pyscribble.py <path-img>

Arguments:
    <path-img>

Author: Denis Samuylov
Date: denis.samuylov@gmail.com

"""

import os
import sys
import docopt
import tifffile
import numpy as np

from PyQt4 import QtGui
from PyQt4.QtCore import Qt


COLORTABLE = [QtGui.qRgb(i, i, i) for i in range(256)]


class PixelPicker(QtGui.QWidget):

    def __init__(self, path_img):
        super(PixelPicker, self).__init__()

        self.path_img = path_img
        self.working_floder = os.path.dirname(path_img)

        self.img = tifffile.imread(path_img)

        self.img_to_display = None
        self.img_zoomed = {}

        self.mask = np.zeros(self.img.shape[1:])
        # TODO: it depends...

        self.current_z = 0
        self.current_t = 0
        self.current_zoom = 1

        self.project_in_z = False
        self.dragging = False

        self.initUI()

    def initUI(self):
        # setup image:
        nframes, nslices, ny, nx = self.img.shape

        # The QLAbel widget provides a text or image display.
        self.img_label = QtGui.QLabel(self)
        self.img_label.resize(nx, ny)
        # self.img_label.mousePressEvent = self.detect_img_click
        self.img_label.mousePressEvent = self.activate_dragging
        self.img_label.mouseReleaseEvent = self.stop_dragging
        self.img_label.mouseMoveEvent = self.record_mouse_coordinates

        self.prepare_img_to_display()
        self.update_img(self.current_t, self.current_z)

        # The QLAbel widget provides a text or image display.
        # self.msk_label = QtGui.QLabel(self)
        # self.msk_label.resize(nx, ny)
        # self.msk_label.mousePressEvent = self.detect_img_click

        # self.update_mask(self.current_t, self.current_z)

        # -> set silce slider
        slider = QtGui.QSlider()
        slider.setMinimum(0)
        slider.setMaximum(nslices - 1)
        slider.setOrientation(Qt.Horizontal)
        slider.valueChanged.connect(self.update_slice)

        # -> rigtht panel:
        self.right_panel = QtGui.QFrame(self)

        # --> project in z
        self.zproj_cb = QtGui.QCheckBox('project in z', self)
        self.zproj_cb.setCheckState(self.project_in_z)
        self.zproj_cb.stateChanged.connect(self.respond_zproj_cb)

        # --> Set zoom buttons
        zoom_out_button = QtGui.QPushButton('   -   ')
        zoom_out_button.clicked.connect(self.zoom_out)

        zoom_in_button = QtGui.QPushButton('   +   ')
        zoom_in_button.clicked.connect(self.zoom_in)

        # --> Display output file name
        self.mask_name_le = QtGui.QLineEdit(self)
        self.mask_name_le.setText(self.generate_mask_name())

        # --> Save button
        save_button = QtGui.QPushButton('Save')
        save_button.clicked.connect(self.save_mask)

        # set layout for the right panel:
        right_layout = QtGui.QGridLayout()
        right_layout.addWidget(self.zproj_cb, 0, 0, 1, 2)
        right_layout.addWidget(zoom_out_button, 1, 0)
        right_layout.addWidget(zoom_in_button, 1, 1)
        right_layout.addWidget(self.mask_name_le, 2, 0, 1, 2)
        right_layout.addWidget(save_button, 3, 0, 1, 2)
        self.right_panel.setLayout(right_layout)

        # set layout
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.img_label, 0, 0)
        # grid.addWidget(self.msk_label, 1, 0)
        grid.addWidget(slider, 2, 0)

        # The widget spans 3 rows
        grid.addWidget(self.right_panel, 0, 1, 3, 1)

        self.setLayout(grid)

        # self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('Pixel Picker')
        self.show()

    def generate_mask_name(self):
        img_name = os.path.split(self.path_img)[1]
        name, ext = img_name.split('.')
        return "{}_mask.{}".format(name, ext)

    def activate_dragging(self, event):
        self.dragging = True
        self.record_mouse_coordinates(event)

    def stop_dragging(self, event):
        self.dragging = False

    def record_mouse_coordinates(self, event, val=255):
        _, _, ny, nx = self.img.shape
        x, y = event.x()/self.current_zoom, event.y()/self.current_zoom
        if x < 0 or x >= nx or y < 0 or y >= ny:
            return
        # print "click at x={} y={}".format(x, y)

        if self.project_in_z:
            self.mask[:, y, x] = val
        self.mask[self.current_z, y, x] = val

    def normalize(self, img, vmin=None, vmax=None):
        """scale image between 0 and 255"""
        img = np.array(img)
        if vmin is None:
            minv = img.min()
        if vmax is None:
            maxv = img.max()
        resc_img = np.uint8(255*np.float64(img - minv)/(maxv - minv))
        return resc_img

    def save_mask(self):
        mask_name = str(self.mask_name_le.text())
        mask_path = os.path.join(self.working_floder, mask_name)
        tifffile.imsave(mask_path, np.uint8(self.mask))

    def prepare_img_to_display(self):
        nframes, nslices, ny, nx = self.img.shape
        img_to_display = np.mean(self.img, axis=0)
        if self.project_in_z:
            img_to_display = np.mean(img_to_display,
                                     axis=0).reshape((1, ny, nx))
        self.img_to_display = self.normalize(img_to_display)
        self.compute_zoomed_image()

    def respond_zproj_cb(self):
        self.img_zoomed = {}
        self.project_in_z = self.zproj_cb.checkState()
        self.prepare_img_to_display()
        self.update_img(self.current_t, self.current_z)

    def update_slice(self, z):
        """update z-slice"""
        # print "slice is changed = {}".format(z)
        if self.project_in_z:
            return
        self.update_img(self.current_t, z)
        self.current_z = z

    def zoom_out(self):
        if self.current_zoom <= 1:
            return
        print "zoom out"
        self.current_zoom -= 1
        self.compute_zoomed_image()
        self.update_img(self.current_t, self.current_z)

    def zoom_in(self):
        print "zoom in"
        self.current_zoom += 1
        self.compute_zoomed_image()
        self.update_img(self.current_t, self.current_z)

    def compute_zoomed_image(self):
        if self.current_zoom in self.img_zoomed:
            print "the zoomed img is already computed"
            return
        nframes, nslices, ny, nx = self.img.shape
        zoom = self.current_zoom
        img_zoomed = [np.repeat(np.repeat(img2d, zoom, axis=0), zoom, axis=1)
                      for img2d in self.img_to_display]
        img_zoomed = self.normalize(img_zoomed)
        self.img_zoomed[self.current_zoom] = img_zoomed

    def get_img_zoomed_to_dispaly(self, z):
        zoom = self.current_zoom
        if self.project_in_z:
            return self.img_zoomed[zoom][0]
        return self.img_zoomed[zoom][z]

    def update_img(self, t, z):
        img2d = self.get_img_zoomed_to_dispaly(z)
        ny, nx = img2d.shape

        qimg = QtGui.QImage(img2d.data, nx, ny, nx,
                            QtGui.QImage.Format_Indexed8)
        qimg.setColorTable(COLORTABLE)
        qpm = QtGui.QPixmap.fromImage(qimg)

        self.img_label.resize(nx, ny)
        self.img_label.setPixmap(qpm)


def main():
    # Parse argumentsfrom command line:
    args = docopt.docopt(__doc__)
    # Run:
    app = QtGui.QApplication(sys.argv)
    PixelPicker(args["<path-img>"])
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
