import subprocess, os
from PyQt5 import QtCore
import multiprocessing as mp

from geomorphometrics.generate_geomorphometrics_pcd import generate_pcd


class LaunchPCDThread(QtCore.QThread):
    prog_val = QtCore.pyqtSignal(int)

    def __init__(self, model_path, scales, metrics):
        super(LaunchPCDThread, self).__init__()
        self.model_path = model_path
        self.scales = scales
        self.metrics = metrics

    def run(self):
        nb_processes = 4
        inputs = [[self.model_path, scale, os.path.dirname(self.model_path), self.metrics] for scale in self.scales]
        with mp.Pool(processes=nb_processes) as pool:
            pool.starmap(generate_pcd, inputs)
        print("Done")


def launch_process(model, scale, output_path):
    subprocess.call(['python', 'generate_pcd.py', model, str(scale), output_path])