import os
from volume_filter import stat_summary, save_stat_summary
from UI.summary_statistics_ui import Ui_Dialog
from PyQt5.QtWidgets import (QDialog)
import pandas as pd
import utility


class VolStatDialog(QDialog, Ui_Dialog):
    def __init__(self, qt):
        super().__init__()
        self.setupUi(self)
        self.qt = qt
        self.project_config = qt.project_config

        self.annotations_list = self.project_config['outputs']['reprojected_annotations']
        annotations_name_list = [ann["report_name"] for ann in self.annotations_list]
        self.reproj_annot.addItems(annotations_name_list)
        self.buttonBox.accepted.connect(self.launch_summary_stat)

        self.models_list = self.project_config['outputs']['3D_models']
        if len(self.models_list) != 0:
            item_list = [x['name'] for x in self.models_list]
            self.model_3D.addItems(item_list)

    def launch_summary_stat(self):
        video_tracks_only = self.video_tracks_only.isChecked()
        reproj_annotations_name = self.reproj_annot.currentText()
        reproj_annotations = next((item for item in self.annotations_list if item["report_name"] == reproj_annotations_name), None)
        model_name = self.model_3D.currentText()
        model = next((item for item in self.models_list if item["name"] == model_name), None)
        point_cloud_dir = os.path.dirname(model["model_path"])
        output_dir = utility.create_dir(os.path.join(self.project_config['project_directory'], "volume_stat"))

        reproj_annotations_path = os.path.join(reproj_annotations["reprojected_annotation_dir"], "polygons.pkl")
        annotations = pd.read_pickle(r"{}".format(reproj_annotations_path))

        if annotations is not None:
            polygon_summary_pd, tracks_summary_pd = stat_summary(point_cloud_dir, annotations, video_tracks_only)
            if polygon_summary_pd is not None:
                save_stat_summary(polygon_summary_pd, f"{model_name}_{reproj_annotations_name}_poly_sum.csv", output_dir)
            if tracks_summary_pd is not None:
                save_stat_summary(tracks_summary_pd, f"{model_name}_{reproj_annotations_name}_track_sum.csv", output_dir)
