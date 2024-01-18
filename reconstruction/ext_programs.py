from PyQt5.QtCore import QProcess
import os

class command():

    def __init__(self, prog, args, gui):
        self.p = QProcess()
        self.p.setWorkingDirectory(os.path.dirname(os.path.abspath(__file__)))
        self.p.readyReadStandardOutput.connect(self.handle_stdout)
        self.p.readyReadStandardError.connect(self.handle_stderr)
        self.p.finished.connect(self.process_finished)
        self.p.error.connect(self.handle_error)

        self.debug = gui
        self.prog = prog
        self.args = args

        self.error = False

        self.debug.normalOutputWritten("Starting command: \r")
        self.debug.normalOutputWritten(f"Program: {prog}; Args: {str(args)} \r")
        self.p.start(self.prog, self.args)
        self.running = True

    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8", errors='ignore')
        self.debug.normalOutputWritten(stderr)

    def handle_error(self):
        self.handle_stderr()
        self.error = True
        self.running = False
        self.debug.normalOutputWritten("An error occurred \r")

    def handle_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8", errors='ignore')
        self.debug.normalOutputWritten(stdout)

    def process_finished(self):
        self.p = None
        self.running = False
        self.debug.normalOutputWritten("Command finished \r")


def create_database_command(db_path):
    return ["database_creator", "--database_path", db_path]


def extract_features_command(config_path):
    return ["feature_extractor", "--project_path", config_path]


def match_features_vocab_command(vocab_tree_path, db_path, num_nearest_neighbors=10):
    return [
        "vocab_tree_matcher",
        "--VocabTreeMatching.vocab_tree_path", vocab_tree_path,
        "--database_path", db_path,
        "--VocabTreeMatching.num_nearest_neighbors", str(num_nearest_neighbors),
        "--SiftMatching.guided_matching", str(1),
    ]


def match_features_seq_command(db_path, num_nearest_neighbors=10):
    return [
        "sequential_matcher",
        "--database_path", db_path,
        "--SequentialMatching.overlap", str(num_nearest_neighbors),
        "--SiftMatching.guided_matching", str(1),
    ]


def match_features_spatial_command(db_path):
    return [
        "spatial_matcher",
        "--database_path", db_path,
        "--SiftMatching.min_inlier_ratio", str(0.2),
        "--SpatialMatching.ignore_z", str(0),
        "--SpatialMatching.max_distance", str(10),
        "--SpatialMatching.max_num_neighbors", str(64),
        "--SiftMatching.guided_matching", str(1),
    ]


def match_features_transitive_command(db_path):
    return [
        "transitive_matcher",
        "--database_path", db_path
    ]


def hierarchical_mapper_command(sparse_model_path, db_path, image_path, two_view):
    cmd = [
        "hierarchical_mapper",
        "--output_path", sparse_model_path,
        "--database_path", db_path,
        "--image_path", image_path
    ]
    if two_view:
        cmd.extend(["--Mapper.tri_ignore_two_view_tracks", "0"])
    return cmd


def hierarchical_mapper_gps_prior_command(sparse_model_path, db_path, image_path, ignore_two_view, focal=0, pp=0, dist=0, std_z=0.1):
    cmd = [
        "hierarchical_mapper",
        "--output_path", sparse_model_path,
        "--database_path", db_path,
        "--image_path", image_path,
        "--Mapper.abs_pose_min_num_inliers", str(20),
        "--Mapper.ba_refine_focal_length", str(focal),
        "--Mapper.ba_refine_principal_point", str(pp),
        "--Mapper.ba_refine_extra_params", str(dist),
        "--Mapper.ba_global_function_tolerance", "1e-06",
        "--Mapper.ba_global_max_num_iterations", str(30),
        "--Mapper.ba_global_max_refinements", str(5),
        "--Mapper.use_enu_coords", str(1),
        "--Mapper.prior_is_gps", str(1),
        "--Mapper.use_prior_motion", str(1),
        "--Mapper.ba_prior_std_z", str(std_z),
        "--Mapper.tri_ignore_two_view_tracks", str(ignore_two_view),
        "--Mapper.ba_global_use_robust_loss_on_prior", str(1),
        "--Mapper.prior_loss_scale", str(11.345),
    ]
    return cmd

def model_sfm_aligner_command(sparse_path, full_optim_path, db_path, std_z = 0.1, refine_calib = 1):
    return [
        "model_sfm_gps_aligner",
        "--input_path", sparse_path,
        "--output_path", full_optim_path,
        "--database_path", db_path,
        "--ref_is_gps", str(1),
        "--alignment_type,", "enu",
        "--motion_prior_std_z", str(std_z),
        "--use_robust_cost_on_motion_prior", str(1),
        "--robust_prior_huber_cost_squared", str(11.345),
        "--use_robust_visual_cost", str(1),
        "--robust_visual_soft_l1_cost_squared", str(5.991),
        "--refine_extra_params", str(refine_calib),
        "--refine_focal_length", str(refine_calib),
        "--refine_principal_point", str(refine_calib),
        "--ba_max_iterations", str(100),
        "--nb_ba_refinement", str(5),
        "--ba_function_tolerance", "1e-06",
    ]

def georegistration_command(model_path):
    return [
        "model_aligner",
        "--input_path", model_path,
        "--ref_images_path", os.path.join(model_path, 'georegist.txt'),
        "--output_path", model_path,
        "--ref_is_gps", str(1),
        "--alignment_type", 'enu',
        "--robust_alignment", str(1),
        "--robust_alignment_max_error", str(3.0)
    ]


def convert_model_command(model_path, output_type = 'TXT'):
    return [
        "model_converter",
        "--input_path", model_path,
        "--output_path", model_path,
        "--output_type", output_type,
    ]


def merge_model_command(sparse_model_path, model1_name, model2_name, combined_path):
    return [
        "model_merger",
        "--input_path1", os.path.join(sparse_model_path, model1_name),
        "--input_path2", os.path.join(sparse_model_path, model2_name),
        "--output_path", combined_path,
    ]


def undistort_image_command(image_path, model_path, output_path):
    return [
        "image_undistorter",
        "--image_path", image_path,
        "--input_path", model_path,
        "--output_path", output_path,
        "--output_type", "COLMAP"
    ]


def interface_openmvs_command(model_path):
    return [
        model_path,
        "-w", model_path,
        "-o", os.path.join(model_path, "model.mvs"),
        "--image-folder", os.path.join(model_path, "images"),
    ]


def dense_reconstruction_command(model_path, openMVS, two_view, img_scaling):
    cmd = [
        "-i", os.path.join(model_path, "model.mvs"),
        "-o", os.path.join(model_path, "dense.mvs"),
        "-w", model_path,
        "--resolution-level", str(img_scaling)
    ]
    if two_view:
        densify_path = os.path.join(openMVS, "Densify.ini")
        cmd.extend(["--number-views-fuse", "2", "--dense-config-file", str(densify_path)])

        if not os.path.exists(densify_path):
            with open(densify_path, 'w') as f:
                f.write("Min Views Filter = 1")
    return cmd




def mesh_reconstruction_command(model_path, decimation):
    return [
        "-i", os.path.join(model_path, "dense.mvs"),
        "-o", os.path.join(model_path, "mesh.mvs"),
        "-w", model_path,
        "--constant-weight", str(0),
        "-f", str(1),
        "--decimate", str(decimation)
    ]


def openmvs_texturing_command(model_path):
    return [
        "-i", os.path.join(model_path, "mesh.mvs"),
        "-o", os.path.join(model_path, "textured_mesh.mvs"),
        "-w", model_path
    ]


def texrecon_texturing_command(model_path):
    return [
        "--keep_unseen_faces",
        os.path.join(model_path, "images"),
        os.path.join(model_path, "mesh.ply"),
        os.path.join(model_path, "textured_mesh")
    ]


def convert_mesh(model_path):
    return [
        "-i", os.path.join(model_path, "textured_mesh.mvs"),
        "-o", os.path.join(model_path, "textured_mesh.obj"),
        "-w", model_path,
        "--export-type", 'obj'
    ]