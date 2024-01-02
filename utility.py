import numpy as np
import os


def create_dir(dir):
    if not os.path.isdir(dir):
        os.mkdir(dir)
    return dir

def get_geomorphometrics_scales(project_config):
    geomorphometrics = project_config["outputs"]['geomorphometrics']
    if len(geomorphometrics) != 0:
        return [str(scale['scale']) for scale in project_config["outputs"]['geomorphometrics']]
    else:
        return []


def get_geomorphometric_scalars(project_config, scale):
    geomorphometrics = project_config["outputs"]['geomorphometrics']
    if len(geomorphometrics) == 0 or scale == 0:
        return []
    geomorphometric = next((item for item in geomorphometrics if item["scale"] == float(scale)), None)
    if geomorphometric is None:
        return []
    pcd_path = geomorphometric["pcd_path"]
    with open(pcd_path, encoding="ANSI") as file:
        i = 0
        for item in file:
            if i == 2:
                s = item
            if i == 3:
                break
            i += 1
    scalars = s.split(' ')
    scalars = [
        x
        for x in scalars
        if not x.startswith("__")
        and not x.startswith("normal_")
        and x not in ["x", "y", "z", r"_\n", "FIELDS"]
    ]
    return scalars


def check_radial_distortion(radial_distortion, camera_name, op=None):
    """Check if the radial distortion is compatible with Blender."""

    # TODO: Integrate lens distortion nodes
    # https://docs.blender.org/manual/en/latest/compositing/types/distort/lens_distortion.html
    # to properly support radial distortion represented with a single parameter

    if radial_distortion is None:
        return
    if np.array_equal(
        np.asarray(radial_distortion), np.zeros_like(radial_distortion)
    ):
        return

    output = "Blender does not support radial distortion of cameras in the"
    output += f" 3D View. Distortion of camera {camera_name}:"
    output += " {radial_distortion}. If possible, re-compute the "
    output += "reconstruction using a camera model without radial distortion"
    output += ' parameters.  Use "Suppress Distortion Warnings" in the'
    output += " import settings to suppress this message."
