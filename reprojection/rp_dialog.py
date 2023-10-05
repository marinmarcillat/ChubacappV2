import os
import utility
import reproject
from UI.reprojection_ui import Ui_Dialog as Ui_Dialog_reproj
from PyQt5.QtWidgets import (QDialog, QFileDialog)
import video_annotations as VA


class rpDialog(QDialog, Ui_Dialog_reproj):
    def __init__(self, qt):
        super().__init__()
        self.setupUi(self)
        self.qt = qt
        self.project_config = qt.project_config
        self.hit_map_launch.clicked.connect(self.launch_get_hit_maps)
        self.reproject_launch.clicked.connect(self.launch_reprojection)

        self.reprojector = None
        self.annotations_list = None

        self.models_list = self.project_config['outputs']['3D_models']
        if len(self.models_list) != 0:
            item_list = [x['name'] for x in self.models_list]
            self.models3D.addItems(item_list)

        if len(self.project_config['inputs']['annotations']) != 0 and self.project_config['outputs']['hit_maps'] != '':
            self.enable_reproject()

    def set_prog(self, val):
        self.progressBar.setValue(val)

    def enable_reproject(self):
        obj_to_enable = [self.label_3, self.annotation_cb, self.reproject_launch]
        for obj in obj_to_enable:
            obj.setDisabled(False)

        self.annotations_list = self.project_config['inputs']['annotations']
        if len(self.annotations_list) != 0:
            item_list = [x['name'] for x in self.annotations_list]
            self.annotation_cb.addItems(item_list)
        print("ok")

    def launch_get_hit_maps(self):
        project_path = self.project_config['project_directory']
        exp_path = utility.create_dir(os.path.join(project_path,'hit_maps'))
        model_name = self.models3D.currentText()
        model = None
        for x in self.models_list:
            if x['name'] == model_name:
                model = x
        if model is not None:
            model_path = model['model_path']
            sfm_path = model['sfm']
            image_path = self.project_config['inputs']['image_path']

            self.reprojector = reproject.reprojector(model_path, sfm_path, image_path, exp_path)
            self.reprojector.prog_val.connect(self.set_prog)
            self.reprojector.finished.connect(self.end_get_hit_maps)
            self.reprojector.start()

    def end_get_hit_maps(self):
        self.set_prog(0)
        self.qt.normalOutputWritten("Hit maps generation ended \r")
        if len(self.project_config['inputs']['annotations']) != 0:
            self.enable_reproject()

    def launch_reprojection(self):
        project_path = self.project_config['project_directory']
        hit_maps_path = os.path.join(project_path, 'hit_maps')

        rep_name = self.annotation_cb.currentText()
        report = None
        for x in self.annotations_list:
            if x['name'] == rep_name:
                report = x
        if report is not None:
            rep_type = report['rep_type']
            rep_path = report['path']
            video_dir = None
            if rep_type == "video":
                video_dir = self.project_config['inputs']['video_path']

            self.annotation_reprojector = reproject.annotationTo3D(rep_path, hit_maps_path, video_dir)
            self.annotation_reprojector.reproject_annotations()


        print("ok")
