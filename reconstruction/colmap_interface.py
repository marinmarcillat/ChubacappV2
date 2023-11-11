import os, json, shutil
import configparser
import utils
from shutil import copy
from PyQt5 import QtCore
import database_add_gps_from_dim2
import colmap_write_kml_from_database
import convert_colmap_poses_to_texrecon_dev
import ext_programs as ep


class ReconstructionThread(QtCore.QThread):
    """
ReconstructionThread class for the colmap_interface module.

This class represents a thread for performing the reconstruction process.
It handles feature extraction, matching, mapping, post-sparse reconstruction, meshing, and model export.
The thread emits signals to update the GUI with progress and status information.

Args:
    gui: The GUI object.
    image_path (str): The path to the images.
    project_path (str): The path to the project.
    camera (str): The path to the camera file.
    vocab_tree_path (str): The path to the vocabulary tree.
    nav_data (pandas.DataFrame): The navigation data.
    options (tuple): Various reconstruction options.

Attributes:
    step (QtCore.pyqtSignal): Signal emitted to indicate the current step in the reconstruction process.
    prog_val (QtCore.pyqtSignal): Signal emitted to indicate the progress value.
    nb_models (QtCore.pyqtSignal): Signal emitted to indicate the number of models processed.
    finished (QtCore.pyqtSignal): Signal emitted when the reconstruction process is finished.
"""

    def __init__(self, gui, image_path, project_path, camera, vocab_tree_path, nav_data, options):
        ...

    step = QtCore.pyqtSignal(str)
    prog_val = QtCore.pyqtSignal(int)
    nb_models = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, gui, image_path, project_path, camera, vocab_tree_path, nav_data, options):
        """
Initialize a ReconstructionThread object.

This constructor initializes a ReconstructionThread object with the provided parameters.
It sets up the necessary paths, creates directories if they don't exist, and initializes the options for the
 reconstruction process.

Args:
    gui: The GUI object.
    image_path (str): The path to the images.
    project_path (str): The path to the project.
    camera (str): The path to the camera file.
    vocab_tree_path (str): The path to the vocabulary tree.
    nav_data (pandas.DataFrame): The navigation data.
    options (tuple): Various reconstruction options.

Returns:
    None
"""

        super(ReconstructionThread, self).__init__()
        self.running = True

        self.gui = gui
        self.image_path = image_path
        self.camera_path = camera
        self.project_path = project_path
        self.vocab_tree_path = vocab_tree_path

        self.get_exec()

        self.db_path = os.path.join(project_path, 'main.db')
        if not os.path.isfile(self.db_path):
            self.run_cmd(self.colmap, ep.create_database_command(self.db_path))

        self.models_path = os.path.join(project_path, 'models')
        self.sparse_model_path = os.path.join(project_path, 'sparse')
        self.export_path = os.path.join(project_path, 'export')
        for path in [self.models_path, self.sparse_model_path, self.export_path]:
            if not os.path.isdir(path):
                os.mkdir(path)
        self.nav_data = nav_data

        self.CPU_features, self.vocab_tree, self.seq, self.spatial, self.refine, self.matching_neighbors, self.two_view, self.img_scaling, self.decimation, self.skip_reconstruction = options

    def run(self):
        """
Run the reconstruction process.

This function executes the reconstruction process, which includes calling the reconstruction, post-sparse
reconstruction, meshing, and model export methods. If a RuntimeError occurs, an error message is displayed.
The progress value is set to 0, and the 'finished' signal is emitted.

Args:
    self: An instance of the colmap_interface class.

Returns:
    None
"""

        try:
            if not self.skip_reconstruction:
                self.reconstruction()
            self.post_sparse_reconstruction()
            self.meshing()
            self.export_models()


        except RuntimeError:
            self.gui.normalOutputWritten("An error occurred")
        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False

    def end(self):  # sourcery skip: raise-specific-error
        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False
        raise RuntimeError("An error occurred !")

    def get_exec(self):
        """
Get the paths for the required executables.

This function sets the paths for the COLMAP, OpenMVS, and texrecon executables. It checks if the executables exist and
raises an error if any of them is missing.

Args:
    self: An instance of the colmap_interface class.

Returns:
    None
"""

        self.colmap = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"COLMAP-3.8-GPS_prior\COLMAP.bat")
        self.openMVS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OpenMVS_Windows_x64")
        self.texrecon = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"texrecon\texrecon.exe")

        for path in [self.colmap, self.openMVS, self.texrecon]:
            if not os.path.exists(path):
                self.gui.normalOutputWritten(f"Error: missing executable: {path}")
                self.end()

    def run_cmd(self, prog, args):
        """
Run a command and wait for it to finish.

This function runs a command with the specified arguments and waits for it to finish. If an error occurs, it calls the
'end' method to handle the error. Otherwise, it returns 1.

Args:
    self: An instance of the colmap_interface class.
    prog (str): The path to the program to be executed.
    args (str): The arguments to be passed to the program.

Returns:
    int: 1 if the command was executed successfully.

Raises:
    RuntimeError: If an error occurs during command execution.
"""

        p = ep.command(prog, args, self.gui)
        p.p.waitForFinished(-1)
        if p.error:
            self.end()
        else:
            return 1

    def config_extract_features(self, cpu_features):
        """
Configure feature extraction for the colmap_interface module.

This function generates a configuration file for feature extraction.
It reads the camera path, adds necessary sections and options to the configuration,
and writes the configuration file. The path to the generated configuration file is returned.

Args:
    self: An instance of the colmap_interface class.
    cpu_features (bool): Flag indicating whether to use CPU features.

Returns:
    str: The path to the generated configuration file.
"""

        print("Extracting features")
        config_path = os.path.join(self.project_path, 'extract_features.ini')

        config = configparser.ConfigParser()
        config.read(self.camera_path)
        config.add_section('top')
        config.add_section('SiftExtraction')
        config.set('top', 'database_path', self.db_path)
        config.set('top', 'image_path', self.image_path)
        config.set('ImageReader', 'single_camera', str(1))

        if cpu_features:
            config.set('SiftExtraction', 'estimate_affine_shape', str(1))
            config.set('SiftExtraction', 'domain_size_pooling', str(1))

        text1 = '\n'.join(['='.join(item) for item in config.items('top')])
        text2 = '\n'.join(['='.join(item) for item in config.items('ImageReader')])
        text3 = '\n'.join(['='.join(item) for item in config.items('SiftExtraction')])
        text = text1 + '\n[ImageReader]\n' + text2 + '\n[SiftExtraction]\n' + text3
        with open(config_path, 'w') as config_file:
            config_file.write(text)

        return config_path

    def reconstruction(self):
        """
Reconstruction function for the colmap_interface module.

This function performs the reconstruction process, including feature extraction, matching, and mapping.
It extracts features from the images, adds GPS information to the database,
matches features using various methods (vocab tree, sequential, spatial, and transitive), and performs mapping
using hierarchical mapper with GPS priors.

Args:
    self: An instance of the colmap_interface class.

Returns:
    None
"""

        self.step.emit('extraction')
        config_path = self.config_extract_features(self.CPU_features)
        self.run_cmd(self.colmap, ep.extract_features_command(config_path))

        database_add_gps_from_dim2.add_table_to_db(self.db_path, self.nav_data)

        self.step.emit('matching')
        if self.vocab_tree:
            self.run_cmd(self.colmap,
                         ep.match_features_vocab_command(self.vocab_tree_path, self.db_path, self.matching_neighbors))
        if self.seq:
            self.run_cmd(self.colmap, ep.match_features_seq_command(self.db_path, self.matching_neighbors), )
        if self.spatial:
            self.run_cmd(self.colmap, ep.match_features_spatial_command(self.db_path))
        self.run_cmd(self.colmap, ep.match_features_transitive_command(self.db_path))

        self.step.emit('mapping')
        self.run_cmd(self.colmap,
                     ep.hierarchical_mapper_gps_prior_command(self.sparse_model_path, self.db_path, self.image_path,
                                                              self.two_view))

    def post_sparse_reconstruction(self):
        """
Post-sparse reconstruction function for the colmap_interface module.

This function performs post-processing steps after the sparse reconstruction. It iterates through each model in the
 sparse model path, creates a corresponding dense model path if it doesn't exist, performs georegistration, converts
 the model, undistorts images, and interfaces with OpenMVS for further processing.

Args:
    self: An instance of the colmap_interface class.

Returns:
    None
"""

        list_models = next(os.walk(self.sparse_model_path))[1]
        prog = 0
        tot_len = len(list_models)
        for model in list_models:
            sparse_model_path = os.path.join(self.sparse_model_path, model)
            dense_model_path = os.path.join(self.models_path, model)
            if not os.path.isdir(dense_model_path):
                os.mkdir(dense_model_path)

            self.prog_val.emit(round((prog / tot_len) * 100))
            prog += 1
            s = f"{str(round(prog / tot_len * 100))} %, {prog} / {tot_len} \r"
            self.nb_models.emit(f'{prog} / {tot_len}')
            self.gui.normalOutputWritten(s)

            self.step.emit('georegistration')
            # self.run_cmd(self.colmap, ep.model_aligner_command(sparse_model_path, self.db_path))
            self.run_cmd(self.colmap, ep.convert_model_command(sparse_model_path))
            self.get_georegistration_file(sparse_model_path)
            self.run_cmd(self.colmap, ep.georegistration_command(sparse_model_path))
            self.run_cmd(self.colmap, ep.convert_model_command(sparse_model_path))
            self.run_cmd(self.colmap, ep.undistort_image_command(self.image_path, sparse_model_path, dense_model_path))
            self.run_cmd(os.path.join(self.openMVS, 'InterfaceCOLMAP.exe'),
                         ep.interface_openmvs_command(dense_model_path))

    def meshing(self):
        """
Meshing function for the colmap_interface module.

This function performs the meshing process for each model in the specified model path. It iterates through each model,
performs dense reconstruction, mesh reconstruction, optional refinement, texture conversion, and texturing.
The progress of the meshing process is displayed in the GUI.

Args:
    self: An instance of the colmap_interface class.

Returns:
    None
"""

        list_models = next(os.walk(self.models_path))[1]
        prog = 0
        tot_len = len(list_models)
        for model in list_models:
            dense_model_path = os.path.join(self.models_path, model)

            self.gui.set_prog(round((prog / tot_len) * 100))
            prog += 1
            s = f"{str(round(prog / tot_len * 100))} %, {prog} / {tot_len} \r"
            self.nb_models.emit(f'{prog} / {tot_len}')
            self.gui.normalOutputWritten(s)

            self.step.emit('dense')
            self.run_cmd(os.path.join(self.openMVS, 'DensifyPointCloud.exe'),
                         ep.dense_reconstruction_command(dense_model_path, self.openMVS, self.two_view,
                                                         self.img_scaling))

            self.step.emit('mesh')
            self.run_cmd(os.path.join(self.openMVS, 'ReconstructMesh.exe'),
                         ep.mesh_reconstruction_command(dense_model_path, self.decimation))

            if self.refine:
                self.step.emit('refinement')
                self.gui.normalOutputWritten("Not available yet \r")

            self.step.emit('texture')
            convert_colmap_poses_to_texrecon_dev.colmap2texrecon(os.path.join(dense_model_path, "sparse"),
                                                                 os.path.join(dense_model_path, "images"))
            self.run_cmd(self.texrecon, ep.texrecon_texturing_command(dense_model_path))

            # self.run_cmd(os.path.join(self.openMVS, 'TextureMesh.exe'), ep.openmvs_texturing_command(dense_model_path))

    def get_georegistration_file(self, model_path):
        filename = os.path.join(model_path, 'images.txt')
        img_list = []
        with open(filename) as file:
            img_list.extend(
                line.rstrip("\n").split(' ')[9]
                for n, line in enumerate(file, start=1)
                if n % 2 != 0 and n > 4
            )
        nav_filtered = self.nav_data[self.nav_data['name'].isin(img_list)]
        nav_filtered = nav_filtered[['name', 'lat', 'lon', 'depth']]
        nav_filtered.to_csv(os.path.join(model_path, 'georegist.txt'), index=None, header=None,
                            sep=' ')
        ref_position = [nav_filtered['lat'].iloc[0], nav_filtered['lon'].iloc[0], nav_filtered['depth'].iloc[0]]
        with open(os.path.join(model_path, 'reference_position.txt'), 'w') as f:
            f.write(str(ref_position))

    def export_models(self, obj=True):
        """
Export models for the colmap_interface module.

This function exports the models generated during the reconstruction process. It copies the necessary files to the
export path, creates an SFM data file, writes a KML file, and updates the project configuration with the exported model
information.

Args:
    self: An instance of the colmap_interface class.
    obj (bool, optional): Flag indicating whether to export the model as an OBJ file. Defaults to True.

Returns:
    None
"""

        list_models = next(os.walk(self.models_path))[1]
        for model_id, model in enumerate(list_models):
            files2copy = [os.path.join(self.sparse_model_path, model, "reference_position.txt")]
            model_dir = os.path.join(self.models_path, model)
            if obj:
                model_name = 'textured_mesh.obj'
                mesh_name = "mesh.ply"
                files2copy.extend([os.path.join(model_dir, model_name),
                                   os.path.join(model_dir, mesh_name),
                                   os.path.join(model_dir, 'textured_mesh.mtl')])
                i = 0
                while os.path.exists(os.path.join(model_dir, f'textured_mesh_material{str(i).zfill(4)}_map_Kd.png')):
                    files2copy.append(os.path.join(model_dir, f'textured_mesh_material{str(i).zfill(4)}_map_Kd.png'))
                    i += 1
            else:
                model_name = 'textured_mesh.ply'
                files2copy.append(os.path.join(model_dir, model_name))

            model_export_path = os.path.join(self.export_path, model)
            if not os.path.exists(model_export_path):
                os.mkdir(model_export_path)

            for file in files2copy:
                copy(file, os.path.join(model_export_path, os.path.basename(file)))

            list_poses = utils.read_images_text(os.path.join(self.sparse_model_path, model, "images.txt"), [0, 0, 0])
            camera = utils.read_cameras_text(os.path.join(self.sparse_model_path, model, "cameras.txt"))
            sfm = utils.listposes2sfm(list_poses, camera)
            with open(os.path.join(model_export_path, "sfm_data_temp.json"), 'w') as fp:
                json.dump(sfm, fp, sort_keys=True, indent=4)

            lat, long, alt = utils.read_reference(os.path.join(model_export_path, "reference_position.txt"))
            colmap_write_kml_from_database.write_kml_file(os.path.join(model_export_path, 'textured_mesh.kml'),
                                                          model_name, lat, long, alt)

            self.gui.normalOutputWritten("Removing temporary folders \r")
            rm = [self.models_path, self.sparse_model_path]
            for fp in rm:
                shutil.rmtree(fp)

            model_dict = {"name": f"mesh_{model_id}", "model_path": os.path.join(model_export_path, "mesh.ply"),
                          "sfm": os.path.join(model_export_path, "sfm_data_temp.json")}
            self.gui.project_config['outputs']['3D_models'].append(model_dict)
