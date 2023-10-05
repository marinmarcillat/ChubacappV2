import os
import json
import configuration
from PyQt5.QtWidgets import (
    QDialog, QMainWindow, QFileDialog, QProgressBar, QErrorMessage, QInputDialog
)


project_template = {
    'name': '',
    'project_directory': '',
    'model_origin': [],
    'inputs': {
        'image': False,
        'video': False,
        'blur_removed': False,
        'camera_model': False,
        'navigation': '',
        'video_navigation': '',
        'annotations': [],
        'image_path': '',
        'video_path': '',
        'camera_model_path': "camera_OTUS2.ini",
        'navigation_path': '',
    },
    'outputs': {
        '3D_model': False,
        'orthomosaic': False,
        'geomorpho': False,
        '3D_annotations': False,
        '3D_models': [],
        'orthomosaic_path': '',
        'geomorpho_scales': [],
        'geomorpho_path': '',
        '3D_annotation_path': '',
        'hit_maps': ''
    },
    'vocab_tree': r"configurations/vocab_trees/vocab_tree_flickr100K_words32K.bin"
}


def read_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def write_json(file_path, project_config):
    with open(file_path, "w") as outfile:
        json.dump(project_config, outfile)


def create_json(name, directory):
    project_path = os.path.join(directory, f'{name}.json')
    project_config = project_template.copy()
    project_config['name'] = name
    project_config['project_directory'] = directory

    write_json(project_path, project_config)
    return project_config


def new_project(qt):
    name, ok = QInputDialog.getText(qt, 'New project', 'Project name:')
    if ok and (project_path := QFileDialog.getExistingDirectory(None, 'Open Dir', r"")):
        create_json(name, project_path)
        qt.project_config = create_json(name, project_path)
        configuration.update_interface(qt)


def open_project(qt):
    project_path = QFileDialog.getOpenFileName(qt, "Open file", "", "*.json", options = QFileDialog.Options())[0]
    if project_path != '':
        project_config = read_json(project_path)
        if project_config is not None:
            qt.project_config = project_config
            if project_config['inputs']['navigation'] != '':
                qt.nav_data = configuration.add_navigation(project_config, project_config['inputs']['navigation_path'], project_config['inputs']['navigation'])
            configuration.update_interface(qt)


def save_project(qt):
    pc = qt.project_config
    file_path = os.path.join(pc['project_directory'], f"{pc['name']}.json")
    write_json(file_path, pc)


