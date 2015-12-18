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

import os
import sys
import docopt
import Image
import ImageQt
import tifffile
import numpy as np
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore

COLORTABLE = [QtGui.qRgb(i, i, i) for i in range(256)]


class ControlWindow(QtGui.QWidget):

    def __init__(self, path_image=None):
        super(ControlWindow, self).__init__()
        self.path_image = path_image

        self.image_is_loaded = False
        self.image = None
        self.image_projected = None

        self.image_window = None
        if path_image is not None:
            self.image = read_image(path_image)
            # TODO: depends on the image dimension
            self.image_projected = np.mean(self.image, axis=0)
            self.image_is_loaded = True

        self.mask = None
        if self.image_is_loaded:
            # TODO: The mask dimension depends on...
            self.mask = np.zeros(self.image.shape[1:])

        # TODO: the projection depends on number of dimensions
        self.project_in_z = False
        self.dragging = False

        # TODO: the view depends on the image dimenstion
        self.view = {"z": 0, "t": 0, "scale": 1}

        # GUI elements:
        self.zoom_out_button = None
        self.zoom_in_button = None

    def initUI(self):
        self.setWindowTitle('pyscribble')

        # Zoom-in
        zoom_in_button = QtGui.QPushButton('   +   ')
        zoom_in_button.clicked.connect(self.zoom_in)
        # Zoom-out
        zoom_out_button = QtGui.QPushButton('   -   ')
        zoom_out_button.clicked.connect(self.zoom_out)

        # Set layout:
        layout = QtGui.QGridLayout()
        # layout.addWidget(self.zproj_cb, 0, 0, 1, 2)
        layout.addWidget(zoom_out_button, 1, 0)
        layout.addWidget(zoom_in_button, 1, 1)
        # layout.addWidget(self.mask_name_le, 2, 0, 1, 2)
        # layout.addWidget(save_button, 3, 0, 1, 2)
        self.setLayout(layout)

        self.setGeometry(100, 100, 200, 400)

        # Show image window and control window
        if self.image_is_loaded:
            self.image_window.initUI()
        self.show()

    def closeEvent(self, evnt):
        if self.image_window is not None:
            self.image_window.close()
        super(ControlWindow, self).closeEvent(evnt)

    def mousePressEvent(self, QMouseEvent):
        # Bring image window to front
        self.image_window.activateWindow()
        self.activateWindow()
        # print QMouseEvent.pos()

    def add_image_window(self, widget):
        widget.set_control_window(self)
        self.image_window = widget

    def zoom_in(self):
        self.view["scale"] *= 2
        self.image_window.rescale_image_to_display()

    def zoom_out(self):
        self.view["scale"] /= 2
        self.image_window.rescale_image_to_display()


class ImageWindow(QtGui.QWidget):

    def __init__(self):

        QtGui.QWidget.__init__(self)

        # Keep reference to control window to have access to view state & data:
        self.control_window = None
        # An image to display is stored in the format of QtGui.QImage:
        self.image_to_display = None
        # GUI elements:
        self.scene = None
        self.view = None

    def initUI(self):

        # Set window title:
        self.setWindowTitle(os.path.basename(self.control_window.path_image))

        # Set geometry depending on the control window.
        ctrl_xpos = self.control_window.geometry().left()
        ctrl_ypos = self.control_window.geometry().top()
        ctrl_w = self.control_window.geometry().width()
        nframes, nslices, ny, nx = self.control_window.image.shape
        self.setGeometry(ctrl_xpos + ctrl_w, ctrl_ypos, nx, ny)

        # Set scene:
        self.scene = QtGui.QGraphicsScene()
        # Set view:
        self.view = QtGui.QGraphicsView(self.scene)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Add listeners:
        # TODO

        # Add image to the scene and display it:
        self.update_image_to_display()

        # Set layout:
        layout = QtGui.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view, 0, 0)
        self.setLayout(layout)

        self.show()

    def set_control_window(self, control_window):
        self.control_window = control_window

    def update_image_to_display(self):
        """Read image data from control_window and convert them to Qt format"""
        # Get image we would like to display and its dimensions:
        img = self.control_window.image_projected
        _, h, w = img.shape
        # Get current slice to display:
        z = self.control_window.view["z"]
        # Normalize and convert to Qt format:
        nimg = normalize(img[z], img.min(), img.max()).T
        qimg = QtGui.QImage(nimg, w, h, w, QtGui.QImage.Format_Indexed8)
        qimg.setColorTable(COLORTABLE)
        self.image_to_display = qimg
        self.rescale_image_to_display()

    def rescale_image_to_display(self):
        # Clear the scene:
        self.scene.clear()
        # Get image dimensions of the original image:
        _, h, w = self.control_window.image_projected.shape
        # Get current scale of the image
        scale = self.control_window.view["scale"]
        # Adjust pixel map size:
        pix_map = QtGui.QPixmap.fromImage(self.image_to_display)
        pix_map = pix_map.scaled(scale*w, scale*h, QtCore.Qt.KeepAspectRatio)
        # Display pixel map:
        self.scene.addPixmap(pix_map)
        self.scene.update()
        # Adjust view size:
        self.view.setFixedSize(scale*w, scale*h)
        # Update Widget size:
        self.setFixedHeight(self.view.height())
        self.setFixedWidth(self.view.width())

    def drawImage(self, z):
        ny, nx = self.image_to_display[z].shape

        qimg = QtGui.QImage(self.image_to_display[z], nx, ny, nx,
                            QtGui.QImage.Format_Indexed8)
        qimg.setColorTable(COLORTABLE)
        qpm = QtGui.QPixmap.fromImage(qimg)

        self.image_holder.resize(nx, ny)
        self.image_holder.setPixmap(qpm)


def main():
    # Parse argumentsfrom command line:
    args = docopt.docopt(__doc__)
    path_img = args["<path-img>"]
    # Run:
    app = QtGui.QApplication(sys.argv)
    control_window = ControlWindow(path_img)
    if path_img:
        image_window = ImageWindow()
        control_window.add_image_window(image_window)
    control_window.initUI()
    sys.exit(app.exec_())


def read_image(path):
    img = tifffile.imread(path)
    return img


def normalize(image, vmin, vmax):
    return np.uint8(255*(image - vmin)/(vmax - vmin))


if __name__ == '__main__':
    main()


#     # def initUI(self):
#     #     # setup image:
#     #     nframes, nslices, ny, nx = self.img.shape

#     #     #
    #     #
#     #     #
#     #     # # self.img_label.mousePressEvent = self.detect_img_click
#     #     # self.img_label.mousePressEvent = self.activate_dragging
#     #     # self.img_label.mouseReleaseEvent = self.stop_dragging
#     #     # self.img_label.mouseMoveEvent = self.record_mouse_coordinates

#     #     # self.prepare_img_to_display()
#     #     # self.update_img(self.current_t, self.current_z)

#     #     # The QLAbel widget provides a text or image display.
#     #     # self.msk_label = QtGui.QLabel(self)
#     #     # self.msk_label.resize(nx, ny)
#     #     # self.msk_label.mousePressEvent = self.detect_img_click

#     #     # self.update_mask(self.current_t, self.current_z)

#     #     # -> set silce slider
#     #     slider = QtGui.QSlider()
#     #     slider.setMinimum(0)
#     #     slider.setMaximum(nslices - 1)
#     #     slider.setOrientation(Qt.Horizontal)
#     #     # slider.valueChanged.connect(self.update_slice)

#     #     # # # -> rigtht panel:
#     #     # self.right_panel = QtGui.QFrame(self)

#     #     # # --> project in z
#     #     # self.zproj_cb = QtGui.QCheckBox('project in z', self)
#     #     # self.zproj_cb.setCheckState(self.project_in_z)
#     #     # self.zproj_cb.stateChanged.connect(self.respond_zproj_cb)

#     #     # # --> Set zoom buttons
#     #     # zoom_out_button = QtGui.QPushButton('   -   ')
#     #     # zoom_out_button.clicked.connect(self.zoom_out)

#     #     # zoom_in_button = QtGui.QPushButton('   +   ')
#     #     # zoom_in_button.clicked.connect(self.zoom_in)

#     #     # # --> Display output file name
#     #     # self.mask_name_le = QtGui.QLineEdit(self)
#     #     # self.mask_name_le.setText(self.generate_mask_name())

#     #     # # --> Save button
#     #     # save_button = QtGui.QPushButton('Save')
#     #     # save_button.clicked.connect(self.save_mask)

#     #     # Set layout for the right panel:
#     #     # right_layout = QtGui.QGridLayout()
#     #     # right_layout.addWidget(self.zproj_cb, 0, 0, 1, 2)
#     #     # right_layout.addWidget(zoom_out_button, 1, 0)
#     #     # right_layout.addWidget(zoom_in_button, 1, 1)
#     #     # right_layout.addWidget(self.mask_name_le, 2, 0, 1, 2)
#     #     # right_layout.addWidget(save_button, 3, 0, 1, 2)
#     #     # self.right_panel.setLayout(right_layout)
#     #     # TODO: Right layout will go to the main window.

#     #     # Set layout for the image related things
#     #     grid_layout = QtGui.QGridLayout()
#     #     grid_layout.setSpacing(10)
#     #     # grid.addWidget(self.img_label, 0, 0)
#     #     # # grid.addWidget(self.msk_label, 1, 0)
#     #     # grid_layout.addWidget(slider, 2, 0)

#     #     # The widget spans 3 rows
#     #     # grid_layout.addWidget(self.right_panel, 0, 1, 3, 1)

#     #     self.setLayout(grid_layout)
#     #     self.setGeometry(300, 300, 350, 300)
#     #     self.setWindowTitle('Pixel Picker')
#     #     self.show()

#     # # def generate_mask_name(self):
#     # #     img_name = os.path.split(self.path_img)[1]
#     # #     name, ext = img_name.split('.')
#     # #     return "{}_mask.{}".format(name, ext)

#     # # def activate_dragging(self, event):
#     # #     self.dragging = True
#     # #     self.record_mouse_coordinates(event)

#     # # def stop_dragging(self, event):
#     # #     self.dragging = False

#     # # def record_mouse_coordinates(self, event, val=255):
#     # #     _, _, ny, nx = self.img.shape
#     # #     x, y = event.x()/self.current_zoom, event.y()/self.current_zoom
#     # #     if x < 0 or x >= nx or y < 0 or y >= ny:
#     # #         return
#     # #     # print "click at x={} y={}".format(x, y)

#     # #     if self.project_in_z:
#     # #         self.mask[:, y, x] = val
#     # #     self.mask[self.current_z, y, x] = val

#     # # def normalize(self, img, vmin=None, vmax=None):
#     # #     """scale image between 0 and 255"""
#     # #     img = np.array(img)
#     # #     if vmin is None:
#     # #         minv = img.min()
#     # #     if vmax is None:
#     # #         maxv = img.max()
#     # #     resc_img = np.uint8(255*np.float64(img - minv)/(maxv - minv))
#     # #     return resc_img

#     # # def save_mask(self):
#     # #     mask_name = str(self.mask_name_le.text())
#     # #     mask_path = os.path.join(self.working_floder, mask_name)
#     # #     tifffile.imsave(mask_path, np.uint8(self.mask))

#     # # def prepare_img_to_display(self):
#     # #     nframes, nslices, ny, nx = self.img.shape
#     # #     img_to_display = np.mean(self.img, axis=0)
#     # #     if self.project_in_z:
#     # #         img_to_display = np.mean(img_to_display,
#     # #                                  axis=0).reshape((1, ny, nx))
#     # #     self.img_to_display = self.normalize(img_to_display)
#     # #     self.compute_zoomed_image()

#     # # def respond_zproj_cb(self):
#     # #     self.img_zoomed = {}
#     # #     self.project_in_z = self.zproj_cb.checkState()
#     # #     self.prepare_img_to_display()
#     # #     self.update_img(self.current_t, self.current_z)

#     # # def update_slice(self, z):
#     # #     """update z-slice"""
#     # #     # print "slice is changed = {}".format(z)
#     # #     if self.project_in_z:
#     # #         return
#     # #     self.update_img(self.current_t, z)
#     # #     self.current_z = z

#     # # def zoom_out(self):
#     # #     if self.current_zoom <= 1:
#     # #         return
#     # #     print "zoom out"
#     # #     self.current_zoom -= 1
#     # #     self.compute_zoomed_image()
#     # #     self.update_img(self.current_t, self.current_z)

#     # # def zoom_in(self):
#     # #     print "zoom in"
#     # #     self.current_zoom += 1
#     # #     self.compute_zoomed_image()
#     # #     self.update_img(self.current_t, self.current_z)

#     # # def compute_zoomed_image(self):
#     # #     if self.current_zoom in self.img_zoomed:
#     # #         print "the zoomed img is already computed"
#     # #         return
#     # #     nframes, nslices, ny, nx = self.img.shape
#     # #     zoom = self.current_zoom
#     # #     img_zoomed = [np.repeat(np.repeat(img2d, zoom, axis=0), zoom, axis=1)
#     # #                   for img2d in self.img_to_display]
#     # #     img_zoomed = self.normalize(img_zoomed)
#     # #     self.img_zoomed[self.current_zoom] = img_zoomed

#     # # def get_img_zoomed_to_dispaly(self, z):
#     # #     zoom = self.current_zoom
#     # #     if self.project_in_z:
#     # #         return self.img_zoomed[zoom][0]
#     # #     return self.img_zoomed[zoom][z]

#     # # def update_img(self, t, z):
#     # #     img2d = self.get_img_zoomed_to_dispaly(z)
#     # #     ny, nx = img2d.shape

#     # #     qimg = QtGui.QImage(img2d.data, nx, ny, nx,
#     # #                         QtGui.QImage.Format_Indexed8)
#     # #     qimg.setColorTable(COLORTABLE)
#     # #     qpm = QtGui.QPixmap.fromImage(qimg)

#     # #     self.img_label.resize(nx, ny)
#     # #     self.img_label.setPixmap(qpm)


# def main():



# if __name__ == "__main__":
#     main()
