import os
import sys
import time

import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import (
    QDialog, QMainWindow, QFileDialog, QProgressBar, QErrorMessage, QMessageBox
)
import pyvista as pv
import pv_utils
import project
import configuration
import camera_manager as cm

# from scipy import stats

from UI.menu import Ui_MainWindow

script_dir = os.path.dirname(__file__)
recon_dir = os.path.join(script_dir, 'reconstruction')
reproj_dir = os.path.join(script_dir, 'reprojection')
sys.path.append(recon_dir)
sys.path.append(reproj_dir)

import reconstruction.rc_dialog as rc
import reprojection.rp_dialog as rp
import geomorphometrics.geomorphometrics_dialog as geom

"""
Main module for the Chubacapp application.

This module contains the main window class `Window` which serves as the main interface for the Chubacapp application. 
It handles the setup of the user interface, connects actions to their respective functions, and launches various dialogs
 for reconstruction, camera management, navigation, image and video addition, 3D model addition, and annotation addition

Classes:
    Window: Main window class for the Chubacapp application.

Functions:
    EmittingStream.write: Write text to the QTextEdit.
    EmittingStream.flush: Flush the stream.
"""


class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass


class Window(QMainWindow, Ui_MainWindow):
    """
    A class representing the main window of the application.

    Args:
        parent: The parent widget (default: None).

    Attributes:
        progress_bar: A QProgressBar widget.
        available_cameras: A dictionary of available cameras.
        available_trees: A vocabulary tree.
        plotter: The plotter widget.
        project_config: The project template.
        nav_data: A DataFrame for navigation data.

    Methods:
        __init__(self, parent=None): Initializes the main window.
        connect_actions(self): Connects the actions to their respective slots.
        normalOutputWritten(self, text): Appends text to the QTextEdit.
        launch_reconstruction(self): Launches the reconstruction dialog.
        launch_reprojection(self): Launches the reprojection dialog.
        launch_navigation(self): Launches the navigation dialog.
        launch_add_img(self): Launches the add image dialog.
        launch_add_video(self): Launches the add video dialog.
        launch_add_3dmodel(self): Launches the add 3D model dialog.
        launch_add_annotations(self): Launches the add annotations dialog.
        launch_camera_manager(self): Launches the camera manager dialog.
        pop_message(self, title, message): Displays a message dialog.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowIcon(QtGui.QIcon('Logo-Ifremer.png'))
        self.setGeometry(100, 100, 1600, 1200)

        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)


        self.progress_bar = QProgressBar()
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

        self.available_cameras = cm.get_cameras()
        self.camera_cb.addItems(list(self.available_cameras.keys()))
        self.available_trees = configuration.get_vocab_tree()

        self.plotter = self.contentWidget
        self.plotter.add_axes()
        self.plotter_actors = {
            'navigation': [],
            'recon_camera': [],
            '3D_models': [],
            '3D_annotations': [],
            'textured_models': [],
            'geomorphometrics':[],
        }

        self.project_config = project.project_template.copy()
        self.nav_data = pd.DataFrame()

        self.connect_actions()

    def connect_actions(self):
        self.Reconstruction3D.triggered.connect(self.launch_reconstruction)
        self.AddCamera.triggered.connect(self.launch_camera_manager)
        self.actionNew_project.triggered.connect(lambda: project.new_project(self))
        self.actionOpen_project.triggered.connect(lambda: project.open_project(self))
        self.actionSave_project.triggered.connect(lambda: project.save_project(self))
        self.AddNavigation.triggered.connect(self.launch_navigation)
        self.AddImage.triggered.connect(self.launch_add_img)
        self.AddVideos.triggered.connect(self.launch_add_video)
        self.AddAnnotation.triggered.connect(self.launch_add_annotations)
        self.Add3DModel.triggered.connect(self.launch_add_3dmodel)
        self.Reprojection.triggered.connect(self.launch_reprojection)
        self.Geomorphomtrics.triggered.connect(self.launch_geomorphometrics)
        self.NavLayer.stateChanged.connect(lambda: pv_utils.add_nav_camera(self))
        self.ModelLayer.stateChanged.connect(lambda: pv_utils.add_3d_models(self))
        self.CameraLayer.stateChanged.connect(lambda: pv_utils.add_3d_cameras(self))
        self.AnnotationsLayer.stateChanged.connect(lambda: pv_utils.add_3d_annotations(self))
        self.TexturedModelLayer.stateChanged.connect(lambda: pv_utils.add_textured_models(self))
        self.GeomLayer.stateChanged.connect(lambda: pv_utils.add_geomorphometrics(self))
        self.camera_cb.currentTextChanged.connect(
            lambda: configuration.set_camera_model(self.project_config, self.camera_cb.currentText()))

    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""
        cursor = self.debug.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.debug.setTextCursor(cursor)
        self.debug.ensureCursorVisible()

    def launch_reconstruction(self):
        dlg = rc.RcDialog(self.project_config, self.available_trees, self.nav_data)
        if dlg.exec():
            print("Reconstruction success!")
        else:
            print("Cancel !")
        project.save_project(self)

    def launch_reprojection(self):
        dlg = rp.rpDialog(self)
        if dlg.exec():
            print("Reconstruction success!")
        else:
            print("Cancel !")
        project.save_project(self)

    def launch_geomorphometrics(self):
        dlg = geom.GeomDialog(self)
        if dlg.exec():
            print("Geomorphometrics success!")
        else:
            print("Cancel !")
        project.save_project(self)

    def launch_navigation(self):
        dlg = configuration.AddNavigation(self)
        if dlg.exec():
            print(self.nav_data)
        else:
            print("Cancel !")
        project.save_project(self)

    def launch_add_img(self):
        dlg = configuration.AddImage(self)
        if dlg.exec():
            print("ok")
        else:
            print("Cancel !")
        project.save_project(self)

    def launch_add_video(self):
        dlg = configuration.AddVideo(self)
        if dlg.exec():
            print("ok")
        else:
            print("Cancel!")
        project.save_project(self)

    def launch_add_3dmodel(self):
        dlg = configuration.Add3Dmodel(self)
        if dlg.exec():
            print("ok")
        else:
            print("Cancel!")
        project.save_project(self)

    def launch_add_annotations(self):
        dlg = configuration.AddAnnotations(self)
        if dlg.exec():
            print("ok")
        else:
            print("Cancel!")
        project.save_project(self)

    def launch_camera_manager(self):
        dlg = cm.CameraManager(self, self.available_cameras)
        if dlg.exec():
            print("Success!")
        else:
            print("Cancel!")
        project.save_project(self)

    def pop_message(self, title, message):
        dlg = QMessageBox.warning(self, title, message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
