import sys, os

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QDialog, QFileDialog
)

from geomorphometrics.geomorphometrics_launcher import LaunchPCDThread
from UI.geomorphometrics_ui import Ui_Dialog


class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass


class GeomDialog(QDialog, Ui_Dialog):
    def __init__(self, qt):
        super().__init__()
        self.setupUi(self)
        self.qt = qt
        self.project_config = qt.project_config

        self.setGeometry(0, 30, 420, 360)
        self.setWindowIcon(QtGui.QIcon('Logo-Ifremer.ico'))
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)

        self.models_list = self.project_config['outputs']['3D_models']
        if len(self.models_list) != 0:
            item_list = [x['name'] for x in self.models_list]
            self.models.addItems(item_list)

        self.buttonBox.accepted.connect(self.launch_pcd_computation)

    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""
        cursor = self.textBrowser.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.textBrowser.setTextCursor(cursor)
        self.textBrowser.ensureCursorVisible()

    def selectdir(self, line):
        if dir_path := QFileDialog.getExistingDirectory(None, 'Open Dir', r""):
            line.setText(dir_path)

    def set_prog(self, val):
        self.progressBar.setValue(val)

    def launch_pcd_computation(self):
        metrics = [self.slope.isChecked(), self.aspect.isChecked(), self.roughness.isChecked(), self.TRI.isChecked(),
                   self.BPI.isChecked(), self.GC.isChecked(), self.MC.isChecked(), self.VRM.isChecked()]
        scales = list(map(float, self.scales.text().split(',')))
        model_name = self.models.currentText()
        model = None
        for x in self.models_list:
            if x['name'] == model_name:
                model = x
        if model is not None:
            model_path = model['model_path']
            self.normalOutputWritten(f'Number of operations: {len(scales)} \r')

            self.pcdThread = LaunchPCDThread(model_path, scales, metrics)
            self.pcdThread.prog_val.connect(self.set_prog)
            self.pcdThread.finished.connect(self.end_pcd)
            self.pcdThread.start()

            self.project_config['outputs']['geomorphometrics'] = [{'scale': scale,
                                                                   'model_name': model_name,
                                                                   'pcd_path': os.path.join(
                                                                       os.path.dirname(model_path),
                                                                       'cloud_metrics_{}.pcd'.format(str(scale)))}
                                                                  for scale in scales]
        else:
            self.normalOutputWritten("Error: missing model \r")

    def end_pcd(self):
        self.set_prog(0)
        self.normalOutputWritten("Geomorphometrics Completed \r")
