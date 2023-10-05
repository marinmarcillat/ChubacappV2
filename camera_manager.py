import os, ast
import configparser
import contextlib
from PyQt5.QtWidgets import QDialog
from UI.camera_manager_tool import Ui_CameraManagerTool


def get_cameras():
    camera_dir = r"configurations/camera"
    file_list = os.listdir(camera_dir)
    cam_dict = {}
    for cam in file_list:
        cam_path = os.path.join(camera_dir, cam)
        with contextlib.suppress(Exception):
            config = configparser.ConfigParser()
            config.read(cam_path)
            cam_param = ast.literal_eval(config['ImageReader']['camera_params'])
            cam_dict[cam] = cam_param
    return cam_dict

def add_camera(cam_name, cam_parameters):
    config = configparser.ConfigParser()
    config.add_section('ImageReader')
    config['ImageReader'] = {'camera_model': 'FULL_OPENCV',
                             'camera_params': cam_parameters
                             }
    cam_path = os.path.join(r"configurations/camera", f'{cam_name}.ini')
    with open(cam_path, 'w') as configfile:
        config.write(configfile)

def remove_camera(cam_name):
    cam_path = os.path.join(r"configurations/camera", f'{cam_name}.ini')
    os.remove(cam_path)


class CameraManager(QDialog, Ui_CameraManagerTool):
    def __init__(self, qt, camera_list):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Camera manager")
        self.qt = qt
        self.camera_list = camera_list
        self.active_camera = self.qt.camera_cb.currentText()
        self.show_camera(self.active_camera)
        self.cam_selection_cb.addItems(list(self.camera_list.keys()))
        self.cam_selection_cb.setCurrentText(self.active_camera)

        self.cam_selection_cb.currentTextChanged.connect(lambda: self.show_camera(self.cam_selection_cb.currentText()))

    def show_camera(self, camera):
        parameters = list(self.camera_list[camera][:12])
        parameters.extend([0 for i in range(12 - len(parameters))])
        fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, k5, k6 = parameters
        param_list = [fx, fy, cx, cy, k1, k2, k3, p1, p2]
        le_list = [self.K11_le, self.K22_le, self.K13_le, self.K23_le, self.k1_le, self.k2_le, self.k3_le, self.p1_le, self.p2_le]
        for id in range(len(le_list)):
            le_list[id].setText(str(param_list[id]))
        self.camera_name.setText(camera)






