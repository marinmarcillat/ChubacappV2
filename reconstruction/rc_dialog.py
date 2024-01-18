import os, time
from PyQt5.QtWidgets import QDialog
from PyQt5 import QtCore, QtGui
from UI.reconstruction_ui import Ui_Dialog

from colmap_interface import ReconstructionThread


class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass


class RcDialog(QDialog, Ui_Dialog):
    def __init__(self, project_config, available_trees, nav_data):
        super().__init__()
        self.setupUi(self)

        self.file_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.log_path = f'log_reconstruction_{int(time.time())}.txt'

        self.project_config = project_config
        self.nav_data = nav_data
        self.available_trees = available_trees
        self.LabelTree.addItems(list(self.available_trees.keys()))

        self.active_pb = self.main_pb
        self.reconstruction_thread = None

        self.buttonBox.accepted.connect(self.launch_reconstruction)

    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""
        with open(self.log_path, 'a') as f:
            f.write(text)
        cursor = self.debug.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.debug.setTextCursor(cursor)
        self.debug.ensureCursorVisible()

    def set_nb_models(self, val):
        self.model_nb.setText(val)

    def set_prog(self, val):
        self.active_pb.setValue(val)

    def set_step(self, step):
        label_dict = {
            'georegistration': self.georeferencing,
            'extraction': self.feature_extraction,
            'matching': self.feauture_matching,
            'mapping': self.sparse_reconstruction,
            'dense': self.dense_reconstruction,
            'mesh': self.mesh_reconstruction,
            'refinement': self.mesh_refinement,
            'texture': self.mesh_texturing,
        }
        for key in label_dict:
            label_dict[key].setStyleSheet("QLabel {color : black; font-weight: roman}")
        label_dict[step].setStyleSheet("QLabel {color : green; font-weight: bold}")

    def launch_reconstruction(self):
        image_path = self.project_config['inputs']['image_path']
        project_path = self.project_config['project_directory']
        #nav_path = self.project_config['inputs']['navigation_path']
        vocab_tree_path = os.path.join(self.file_dir, self.available_trees[self.LabelTree.currentText()])
        camera = os.path.join(self.file_dir, "configurations\camera", self.project_config['inputs']['camera_model_path'])

        CPU_features = self.CPU_features.isChecked()
        vocab_tree = self.vocab_tree_cb.isChecked()
        seq = self.sequential_cb.isChecked()
        spatial = self.spatial_cb.isChecked()
        refine = self.refine.isChecked()
        matching_neighbors = int(self.num_neighbors.text())
        skip_reconstruction = self.skip_reconstruction.isChecked()
        ignore_two_view = self.two_view.isChecked()
        img_scaling = int(self.img_scaling.value())
        decimation = float(self.decimation.value())
        options = [CPU_features, vocab_tree, seq, spatial, refine, matching_neighbors, ignore_two_view, img_scaling, decimation, skip_reconstruction]

        self.reconstruction_thread = ReconstructionThread(self, image_path, project_path, camera,
                                                          vocab_tree_path, self.nav_data, options)
        self.reconstruction_thread.prog_val.connect(self.set_prog)
        self.reconstruction_thread.step.connect(self.set_step)
        self.reconstruction_thread.nb_models.connect(self.set_nb_models)
        self.reconstruction_thread.finished.connect(self.end_reconstruction)
        self.reconstruction_thread.start()

    def end_reconstruction(self):
        label_dict = {
            'georegistration': self.georeferencing,
            'extraction': self.feature_extraction,
            'matching': self.feauture_matching,
            'mapping': self.sparse_reconstruction,
            'dense': self.dense_reconstruction,
            'mesh': self.mesh_reconstruction,
            'refinement': self.mesh_refinement,
            'texture': self.mesh_texturing,
        }

        for value in label_dict.values():
            value.setStyleSheet("QLabel {color : black; font-weight: roman}")

        self.set_prog(0)
        self.normalOutputWritten("Reconstruction ended \r")
        #self.accept()





