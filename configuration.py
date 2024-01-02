import os
import navigation
import video
import utility
import pandas as pd
from UI.navigation_ui import Ui_Dialog
from UI.add_video import Ui_Dialog as Ui_Dialog_add_video
from UI.add_image_ui import Ui_Dialog as Ui_Dialog_add_img
from UI.add_3D_model_ui import Ui_Dialog as Ui_Dialog_add_3D
from UI.annotations_ui import Ui_Dialog as Ui_Dialog_annotations
from PyQt5.QtWidgets import (QDialog, QFileDialog)
from video_annotations import report_type


"""
Configuration module for Chubacapp.

This module provides functions and classes for configuring the Chubacapp application. It includes functions for 
retrieving vocabulary tree files, adding images, videos, 3D models, and navigation data to the project configuration, 
updating the user interface, and launching dialogs for adding navigation, images, videos, 3D models, and annotations.

Functions:
    get_vocab_tree: Get the vocabulary tree files from the specified directory.
    add_images: Add images to the project configuration.
    add_videos: Add videos to the project configuration.
    add_3d_model: Add a 3D model to the project configuration.
    set_camera_model: Set the camera model in the project configuration.
    add_navigation: Add navigation data to the project configuration.
    update_interface: Update the user interface with the project configuration.
    AddNavigation: Dialog for adding navigation data.
    AddImage: Dialog for adding images.
    AddVideo: Dialog for adding videos.
    Add3Dmodel: Dialog for adding 3D models.
    AddAnnotations: Dialog for adding annotations.
"""


def get_vocab_tree():
    """
Get the vocabulary tree files from the specified directory.

This function retrieves the vocabulary tree files from the specified directory. It creates a dictionary where the keys are the file names and the values are the file paths. Only files with the ".bin" extension are included in the dictionary.

Returns:
    dict: A dictionary of vocabulary tree files, where the keys are the file names and the values are the file paths.
"""

    vocab_dir = r"configurations/vocab_trees"
    file_list = os.listdir(vocab_dir)
    tree_dict = {}
    for tree in file_list:
        tree_path = os.path.join(vocab_dir, tree)
        if tree_path.endswith(".bin"):
            tree_dict[tree] = tree_path
    return tree_dict

def add_images(project_config, image_path):
    count = sum(bool(file.endswith(".jpg"))
            for file in os.listdir(image_path))
    if count != 0:
        project_config['inputs']['image'] = True
        project_config['inputs']['image_path'] = image_path

def add_videos(project_config, video_dir):
    project_config['inputs']['video'] = True
    project_config['inputs']['video_path'] = video_dir

def add_3d_model(project_config, model_path, sfm_path):
    project_config['outputs']['3D_model'] = True
    project_config['outputs']['3D_model_path'] = model_path
    project_config['outputs']['sfm_data_path'] = sfm_path


def set_camera_model(project_config, camera):
    project_config['inputs']['camera_model'] = True
    project_config['inputs']['camera_model_path'] = camera


def add_navigation(project_config, navigation_path, nav_type):
    project_config['inputs']['navigation'] = nav_type
    project_config['inputs']['navigation_path'] = navigation_path

    if nav_type == "dim2":
        navigation_table = navigation.parse_nav_file_dim2(navigation_path)
    elif nav_type == 'csv':
        navigation_table = navigation.parse_csv(navigation_path)
    model_origin = navigation_table[["lat", "lon", "depth"]].iloc[0].tolist()
    project_config['model_origin'] = model_origin

    return navigation_table
#"date", "time", "camera", "name", "lat", "lon", "depth", "alt", "heading", "pitch", "roll"

def update_interface(qt):
    qt.populate_cb()
    qt.camera_cb.setCurrentText(qt.project_config['inputs']['camera_model_path'])

    p_list = [qt.project_label, qt.image_label, qt.nav_label]
    l_list = [qt.project_config['name'], qt.project_config['inputs']['image_path'], qt.project_config['inputs']['navigation_path']]
    for id in range(len(p_list)):
        p_list[id].setText(l_list[id])


class AddNavigation(QDialog, Ui_Dialog):
    def __init__(self, qt):
        super().__init__()
        self.setupUi(self)
        self.qt = qt
        self.nav_type.addItems(['csv', "dim2"])
        self.project_config = qt.project_config
        self.nav_path_B.clicked.connect(self.select_nav)
        self.buttonBox.accepted.connect(self.launch)

    def select_nav(self):
        options = QFileDialog.Options()
        file_path = QFileDialog.getOpenFileName(self, "Open file", "", "*." + self.nav_type.currentText(), options=options)
        self.nav_path.setText(file_path[0])

    def launch(self):
        if os.path.exists(self.nav_path.text()):
            self.qt.nav_data = add_navigation(self.project_config, self.nav_path.text(), self.nav_type.currentText())
            update_interface(self.qt)


class AddImage(QDialog, Ui_Dialog_add_img):
    def __init__(self, qt):
        super().__init__()
        self.setupUi(self)
        self.qt = qt
        self.project_config = qt.project_config
        self.image_dir_B.clicked.connect(self.select_img_dir)
        self.buttonBox.accepted.connect(self.launch)

    def select_img_dir(self):
        dir_path = QFileDialog.getExistingDirectory(None, 'Open Directory', r"")
        self.image_dir.setText(dir_path)

    def launch(self):
        if self.image_dir.text() != "":
            add_images(self.project_config, self.image_dir.text())
            update_interface(self.qt)
        else:
            self.qt.pop_message("Warning", "Invalid entry")


class AddVideo(QDialog, Ui_Dialog_add_video):
    def __init__(self, qt):
        super().__init__()
        self.setupUi(self)
        self.qt = qt
        self.project_config = qt.project_config
        self.video_dir_B.clicked.connect(self.select_video_dir)
        self.video_nav_B.clicked.connect(self.select_nav_file)
        self.buttonBox.accepted.connect(self.launch)

    def select_video_dir(self):
        dir_path = QFileDialog.getExistingDirectory(None, 'Open Directory', r"")
        self.video_dir.setText(dir_path)

    def select_nav_file(self):
        options = QFileDialog.Options()
        file_path = QFileDialog.getOpenFileName(self, "Open navigation file", "", "*.csv *.txt", options=options)
        self.video_nav.setText(file_path[0])

    def launch(self):
        if os.path.isdir(self.video_dir.text()):
            video_dir = self.video_dir.text()
            video_nav_path = self.video_nav.text()
            add_videos(self.project_config, video_dir)
            video_df = video.get_video_list(video_dir)
            extract = None
            if self.extract_img.checkState() and os.path.exists(video_nav_path):
                self.extract_images(extract, video_dir, video_df, video_nav_path)
            update_interface(self.qt)
        else:
            self.qt.pop_message("Warning", "Invalid entry")

    def extract_images(self, extract, video_dir, video_df, video_nav_path):
        self.qt.normalOutputWritten("Starting image extraction...")
        if self.img_st.checkState():
            extract = {"method": 'st', "param": float(self.st.text())}
        elif self.img_overlap.checkState():
            extract = {"method": 'overlap', "param": float(self.overlap.text())}
        self.out_dir = os.path.join(video_dir, "images")
        utility.create_dir(self.out_dir)
        self.extract_image_thread = video.ExtractImageThread(video_df, self.out_dir, extract['param'], video_nav_path)
        self.extract_image_thread.finished.connect(self.end_extraction)
        self.extract_image_thread.nav_path.connect(self.get_nav_file)
        if extract['method'] == "st":
            self.extract_image_thread.start()

        add_images(self.project_config, self.out_dir)

    def get_nav_file(self, nav_path):
        nav_type = 'csv'
        nav = add_navigation(self.project_config, nav_path, nav_type)
        self.qt.nav_data = nav
        update_interface(self.qt)
        self.qt.normalOutputWritten("Extraction ended successfully !")


    def end_extraction(self):

        print("Image extraction ended")


class Add3Dmodel(QDialog, Ui_Dialog_add_3D):
    def __init__(self, qt):
        super().__init__()
        self.setupUi(self)
        self.qt = qt
        self.project_config = qt.project_config
        self.model3D_B.clicked.connect(self.select_3D_file)
        self.sfm_data_B.clicked.connect(self.select_sfm_file)
        self.buttonBox.accepted.connect(self.launch)

    def select_3D_file(self):
        options = QFileDialog.Options()
        file_path = QFileDialog.getOpenFileName(self, "Open 3D file", "", "*.ply", options=options)
        self.model3D.setText(file_path[0])

    def select_sfm_file(self):
        options = QFileDialog.Options()
        file_path = QFileDialog.getOpenFileName(self, "Open sfm_data file", "", "*.json *.bin", options=options)
        self.sfm_data.setText(file_path[0])

    def launch(self):
        if self.model3D.text() != "" and self.sfm_data != "":
            add_3d_model(self.project_config, self.model3D.text(), self.sfm_data.text())
            update_interface(self.qt)
        else:
            self.qt.pop_message("Warning", "Invalid entry(s)")


class AddAnnotations(QDialog, Ui_Dialog_annotations):
    def __init__(self, qt):
        super().__init__()
        self.setupUi(self)
        self.qt = qt
        self.project_config = qt.project_config
        self.annotations_B.clicked.connect(self.select_annotations_file)
        self.buttonBox.accepted.connect(self.launch)

    def select_annotations_file(self):
        options = QFileDialog.Options()
        file_path = QFileDialog.getOpenFileName(self, "Open annotation report", "", "*.csv", options=options)
        self.annotations.setText(file_path[0])

    def launch(self):
        file_path = self.annotations.text()
        if file_path != "" and os.path.exists(file_path):
            name = os.path.basename(file_path)
            rep_type = report_type(file_path)
            self.qt.project_config['inputs']['annotations'].append({"name": name, "rep_type": rep_type, "path": file_path})
            update_interface(self.qt)
        else:
            self.qt.pop_message("Warning", "Invalid entry")