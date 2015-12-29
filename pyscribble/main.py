import os
import tifffile
import numpy as np
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore

# Scale of the image to draw:
SCALE = "scale"

# Image dimensions:
SLICE = "slice"
FRAME = "frame"
DIMENSION_LABELS = [FRAME, SLICE]
# CHANNEL = "channel"
# DIMENSION_LABELS = [FRAME, SLICE, CHANNEL]

# Color map to display the image:
COLORTABLE = [QtGui.qRgb(i, i, i) for i in range(256)]


class ControlWindow(QtGui.QWidget):

    def __init__(self, path_image=None):
        super(ControlWindow, self).__init__()
        self.path_image = path_image

        self.image_is_loaded = False
        self.image = None
        self.image_projected = None

        self.image_window = None

        # Objects we will initialize from the scene
        self.selected_pixels = None
        self.polygon_collection = None

        self.view = {SLICE: 0, FRAME: 0, SCALE: 1}
        self.project = {SLICE: False, FRAME: False}
        # self.view = {CHANNEL: 0, SLICE: 0, FRAME: 0, SCALE: 1}
        # self.project = {CHANNEL: False, SLICE: False, FRAME: False}

        # Shared GUI elements:
        self.sliders_widget = None
        self.mask_name_line = None
        self.sliders = {}
        self.projection_checkboxes = {}

        # Define shortcuts
        self.define_shortcuts()

        # Set focus, otherwise it focuses on QLineEdit
        self.setFocus()
        self.setFixedSize(self.minimumSize())
        self.initUI()

        if path_image is not None:
            self.load_image(path_image)

    def initUI(self):
        self.setWindowTitle('pyscribble')

        # Open image
        open_button = QtGui.QPushButton("Open image")
        open_button.clicked.connect(self.open_image)

        # Zoom-in
        zoom_in_button = QtGui.QPushButton('   +   ')
        zoom_in_button.clicked.connect(self.zoom_in)

        # Zoom-out
        zoom_out_button = QtGui.QPushButton('   -   ')
        zoom_out_button.clicked.connect(self.zoom_out)

        # Widget panel
        self.sliders_widget = QtGui.QFrame()

        # Display output mask name
        self.mask_name_line = QtGui.QLineEdit(self)

        # Reset mask
        reset_button = QtGui.QPushButton("Reset")
        reset_button.clicked.connect(self.reset_mask)

        # Save button
        save_button = QtGui.QPushButton("Save")
        save_button.clicked.connect(self.save_mask)

        # Set layout:
        layout = QtGui.QGridLayout()
        layout.addWidget(open_button, 0, 0, 1, 2)
        layout.addWidget(zoom_out_button, 1, 0)
        layout.addWidget(zoom_in_button, 1, 1)
        layout.addWidget(self.sliders_widget, 2, 0, 1, 2)
        layout.addWidget(self.mask_name_line, 3, 0, 1, 2)
        layout.addWidget(reset_button, 4, 0)
        layout.addWidget(save_button, 4, 1)
        self.setLayout(layout)

        self.setGeometry(100, 100, 200, 400)
        self.show()

    def closeEvent(self, event):
        if self.image_window is not None:
            self.image_window.close()
        super(ControlWindow, self).closeEvent(event)

    def mousePressEvent(self, QMouseEvent):
        # Bring image window to front
        if self.image_window is not None:
            self.image_window.activateWindow()
        self.activateWindow()

    def reset_image_data(self):
        if self.image_window is not None:
            self.image_window.close()
            self.image_window = None
        # Reset view and projection:
        self.path_image = None

        self.image_is_loaded = False
        self.image = None
        self.image_projected = None

        self.view = {SLICE: 0, FRAME: 0, SCALE: 1}
        self.project = {SLICE: False, FRAME: False}
        self.update_default_mask_name()

    def load_image(self, path):
        if self.image_window is not None:
            self.reset_image_data()
        # Load image
        self.path_image = path
        self.image = read_image(path)
        self.image_is_loaded = True
        self.update_projected_image()
        # Update GUI elements
        image_window = ImageWindow(self)
        self.add_image_window(image_window)
        self.update_slider_widget()
        self.image_window.update_image_to_display()
        self.update_default_mask_name()

    def update_view(self):
        # Read data from sliders into views:
        for slider_label in self.sliders:
            slider = self.sliders[slider_label]
            value = slider.value()
            self.view[slider_label] = value
        # print "Display:", self.view
        # Update view
        self.image_window.update_image_to_display()

    def update_slider_widget(self):

        layout = self.sliders_widget.layout()
        if layout is None:
            layout = QtGui.QGridLayout()
            self.sliders_widget.setLayout(layout)
        else:
            # Remove all widgets:
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().setParent(None)
                # Note: widget is deleted when its parent is deleted.

        if self.image is not None:
            # For each image dimension add slider:
            shape = self.image.shape
            for dim in range(len(self.image.shape) - 2):
                lbl = DIMENSION_LABELS[dim]
                n = shape[dim]
                # --> add label:
                label = QtGui.QLabel(lbl)
                layout.addWidget(label, dim, 1)
                # --> add slider:
                slider = QtGui.QSlider()
                slider.setMinimum(0)
                slider.setMaximum(n - 1)
                slider.setOrientation(QtCore.Qt.Horizontal)
                slider.valueChanged.connect(self.update_view)
                layout.addWidget(slider, dim, 2)
                # (register slider)
                self.sliders[DIMENSION_LABELS[dim]] = slider
                # --> add checkbox:
                check = QtGui.QCheckBox(self.sliders_widget)
                check.setChecked(True)
                check.stateChanged.connect(self.update_project_checkbox)
                layout.addWidget(check, dim, 3)
                # (register checkbox)
                self.projection_checkboxes[DIMENSION_LABELS[dim]] = check

    def update_default_mask_name(self):
        mask_name = None
        if self.image is not None:
            # Generate default mask name
            folder_name = os.path.dirname(self.path_image)
            image_id = os.path.basename(self.path_image).split(".")[0]
            mask_name = os.path.join(folder_name,
                                     "{}-mask.tif".format(image_id))

        if mask_name is not None:
            self.mask_name_line.setText(mask_name)
        else:
            self.mask_name_line.setText("")

    def update_project_checkbox(self):
        self.project[SLICE] = not self.projection_checkboxes[SLICE].isChecked()
        self.project[FRAME] = not self.projection_checkboxes[FRAME].isChecked()
        self.update_projected_image()
        # update max values for sliders
        shape = self.image_projected.shape

        self.sliders[FRAME].setValue(0)
        self.view[FRAME] = 0
        self.sliders[FRAME].setMaximum(shape[0] - 1)

        self.sliders[SLICE].setValue(0)
        self.view[SLICE] = 0
        self.sliders[SLICE].setMaximum(shape[1] - 1)

        self.image_window.update_image_to_display()

    def update_projected_image(self):
        tmp = np.array(self.image)
        if self.project[FRAME]:
            tmp = np.mean(tmp, axis=0)
            tmp = np.expand_dims(tmp, 0)
        if self.project[SLICE]:
            tmp = np.mean(tmp, axis=1)
            tmp = np.expand_dims(tmp, 1)
        self.image_projected = tmp

    def add_image_window(self, widget):
        widget.set_control_window(self)
        self.image_window = widget

    def zoom_in(self):
        self.view["scale"] *= 2
        self.image_window.rescale_image_to_display()

    def zoom_out(self):
        self.view["scale"] /= 2
        self.image_window.rescale_image_to_display()

    def open_image(self):
        path = str(QtGui.QFileDialog.getOpenFileName(
            self,
            "Select an image.",
            os.path.expanduser("~"),
            "Images (*.tif)"))
        self.load_image(path)

    def reset_mask(self):
        self.image_window.reset_scribbles()

    def save_mask(self):
        # Pixel centers:
        nslices, nheight, nwidth = self.image.shape[-3:]

        # Initialize mask
        mask = np.zeros(self.image.shape[1:], np.uint8)
        mask_value = 255
        for scribble in self.image_window.view.scribbles:
            # Check that all pixel positions fit the boundary:
            pts = filter(lambda x: (0 <= x[0]) and (x[0] < nslices) and
                                   (0 <= x[1]) and (x[1] < nheight) and
                                   (0 <= x[2]) and (x[2] < nwidth),
                         scribble)
            # TODO: do filtering letter, otherwise, boundary segment goes away
            pts = np.int32(pts)

            # Select pixels overlapped by a line segment between two points:
            for ps, pe in zip(pts[1:], pts[:-1]):
                # Coordinates of start- and end- points of the line segment
                zs, ys, xs = ps
                ze, ye, xe = pe
                assert zs == ze
                # Parameters defining line segment:
                param = line_pass_two_points_2d(ps, pe)
                # Bounding box of the segment:
                pixel_centers = pixel_centers_2d(ys, ye, xs, xe)

                if len(pixel_centers) == 1:
                    mask[zs, ys, xs] = mask_value
                    continue

                for px in pixel_centers:
                    pass_ = line_pass_square(px, param)
                    if pass_:
                        y_, x_ = px
                        mask[zs, y_, x_] = mask_value
        tifffile.imsave(self.mask_name_line.text(), mask)

    def define_shortcuts(self):
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+D"), self, self.close)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+="), self, self.zoom_in)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+-"), self, self.zoom_out)


class GraphicsView(QtGui.QGraphicsView):

    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        # We need to have an access to the control window
        self.control_window = None
        # Where we start drawing:
        self.dragging = None
        # Store scribbles:
        self.scribbles = []  # y, x
        self.current_scribble = None
        # Define pens:
        self.red_pen = QtGui.QPen(QtGui.QColor("red"), 3)

    def mousePressEvent(self, event):
        self.dragging = True
        # Initialize a scribble (only in 2D):
        self.current_scribble = []
        # Note: we add slice information when we register release event.

        # Register clicked point:
        qp = QtCore.QPointF(event.pos())
        y, x = self.qp2px(qp)
        # Update current scribble:
        self.current_scribble.append((y, x))
        self.draw_current_scribble()

    def mouseMoveEvent(self, event):
        # Register clicked point:
        qp = QtCore.QPointF(event.pos())
        y, x = self.qp2px(qp)
        # Update current scribble:
        self.current_scribble.append((y, x))
        self.draw_current_scribble()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        # Save the scribble we have drawn:
        self.register_current_scribble()
        self.current_scribble = None

    def register_current_scribble(self):
        """Add scribble that we have drawn."""
        # Add scribble depending on a view:
        if self.control_window.project[SLICE]:
            # -> at all slices:
            nslices = self.control_window.image.shape[-3]
            [self.scribbles.append([(z,) + p for p in self.current_scribble])
                for z in np.arange(nslices)]
        else:
            # -> at a current slice:
            z = self.control_window.view["slice"]
            self.scribbles.append([(z,) + p for p in self.current_scribble])

    def qp2px(self, qp):
        """Convert clicked position to selected pixel."""
        return tuple([c/self.control_window.view["scale"]
                      for c in [qp.y(), qp.x()]])

    def px2qp(self, px):
        """Convert clicked position to selected pixel."""
        scale = self.control_window.view["scale"]
        return QtCore.QPoint(px[1]*scale, px[0]*scale)

    def draw_current_scribble(self):
        if self.current_scribble is not None:
            polygon = QtGui.QPolygonF()
            [polygon.append(self.px2qp(p)) for p in self.current_scribble]

            path = QtGui.QPainterPath()
            path.addPolygon(polygon)
            self.scene().addPath(path, self.red_pen)

    def draw_scribbles(self):
        # Draw all traces that are already stored:
        for scribble in self.scribbles:

            # Draw scribbles only at a current slice:
            # TODO: do it more efficiently by storing scribbles for each frame
            if self.control_window.project[SLICE]:
                # Draw scribbles for all slices:
                pass
            else:
                # Draw scribbles only for current slice:
                z = self.control_window.view[SLICE]
                scribble = filter(lambda p: p[0] == z, scribble)

            polygon = QtGui.QPolygonF()
            [polygon.append(self.px2qp(p[1:])) for p in scribble]

            path = QtGui.QPainterPath()
            path.addPolygon(polygon)
            self.scene().addPath(path, self.red_pen)


class ImageWindow(QtGui.QWidget):

    def __init__(self, control_window):

        QtGui.QWidget.__init__(self)

        # Keep reference to control window to have access to view state & data:
        self.control_window = control_window
        # An image to display is stored in the format of QtGui.QImage:
        self.image_to_display = None
        # GUI elements:
        self.scene = None
        self.view = None
        # Add shortcuts:
        self.define_shortcuts()
        self.initUI()

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
        self.view = GraphicsView(self.scene)
        # TODO: pass reference to the control window with constructor.
        self.view.control_window = self.control_window
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Add image to the scene and display it:
        self.update_image_to_display()

        # Set layout:
        layout = QtGui.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view, 0, 0)
        self.setLayout(layout)

        self.show()

    def closeEvent(self, event):
        self.control_window.reset_image_data()
        self.control_window.update_slider_widget()
        super(ImageWindow, self).closeEvent(event)

    def set_control_window(self, control_window):
        self.control_window = control_window

    def update_image_to_display(self):
        """Read image data from control_window and convert them to Qt format"""
        # Get image we would like to display and its dimensions:
        img = self.control_window.image_projected
        _, _, h, w = img.shape
        # Get current slice to display:
        frame = self.control_window.view["frame"]
        z = self.control_window.view["slice"]
        # Normalize and convert to Qt format:
        nimg = normalize(img[frame, z], img.min(), img.max()).T
        qimg = QtGui.QImage(nimg, w, h, w, QtGui.QImage.Format_Indexed8)
        qimg.setColorTable(COLORTABLE)
        self.image_to_display = qimg
        self.rescale_image_to_display()

    def rescale_image_to_display(self):
        # Clear the scene:
        self.scene.clear()
        # Get image dimensions of the original image:
        _, _, h, w = self.control_window.image_projected.shape
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
        # Draw scribbles:
        self.view.draw_scribbles()
        # Update Widget size:
        self.setFixedHeight(self.view.height())
        self.setFixedWidth(self.view.width())

    def define_shortcuts(self):
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+="), self,
                        self.control_window.zoom_in)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+-"), self,
                        self.control_window.zoom_out)

    def reset_scribbles(self):
        self.view.scribbles = []
        self.update_image_to_display()


def read_image(path):
    img = np.float64(tifffile.imread(path))
    # print "Image of the shape is loaded", img.shape
    ndim = len(img.shape)
    if ndim == 2:
        img = img.reshape((1, 1,) + img.shape)
    elif ndim == 3:
        img = img.reshape((1,) + img.shape)
    elif ndim > 4:
        raise Exception("To many dimensions...")
    return img


def normalize(image, vmin, vmax):
    return np.uint8(255*(image - vmin)/(vmax - vmin))


def pixel_centers_2d(min_height, max_height, min_width, max_width):
    """Generate coordinates of pixel centers in image space in 2d bounding box.
    """
    nh = abs(max_height - min_height) + 1
    nw = abs(max_width - min_width) + 1
    v, u = np.meshgrid(np.linspace(min_height, max_height, nh),
                       np.linspace(min_width, max_width, nw),
                       indexing='ij')
    # Note: v = height, u = width
    px_centers = np.vstack([v.ravel(), u.ravel()]).T
    return px_centers


def line_pass_two_points_2d(p1, p2):
    """Return (C, B, A) of a line Cy + Bx + A = 0 passing through p1 and p2.
    """
    ys, xs = p1[-2:]
    ye, xe = p2[-2:]
    return [xe - xs, ys - ye, ye*xs - ys*xe]


def line_pass_square(c, p):
    """Test if a line Cy + Bx + A = 0 pass through a unit square.

    c: coordinates of the center (y, x).
    p: parameters defining a line (C, B, A).

    """
    c = np.array(c, np.float64)
    p = np.array(p, np.float64)
    vertices = [c + [0.5, 0.5], c + [-0.5, 0.5],
                c + [-0.5, -0.5], c + [0.5, -0.5]]
    res = np.int16([np.sign(np.dot(list(v) + [1], p)) for v in vertices])
    # At least two vertices have to be on different sides of the line:
    if -1 in res and 1 in res:
        return True
    return False
