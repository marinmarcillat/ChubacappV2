import pyvista as pv
import numpy as np
import os

import camera
import coord_conversions
from openmvg_json_file_handler import OpenMVGJSONFileHandler


def add_3d_cameras(qt):
    plotter, project_config = qt.plotter, qt.project_config
    for model in project_config['outputs']['3D_models']:
        sfm_path = model['sfm']
        cams = OpenMVGJSONFileHandler.parse_openmvg_file(sfm_path,  "NAME", True)
        for cam in cams:
            trsf_matrix, fov, shift, focal_length, res, dist = camera.get_cam_parameters(cam)

            camera_model = pv.Camera()
            camera_model.model_transform_matrix = trsf_matrix
            camera_model.clipping_range = [0.1, 1]
            frustum = camera_model.view_frustum(1.0)
            plotter.add_mesh(frustum, style="wireframe")


def add_mesh(plotter, obj_path):
    mesh = pv.read(obj_path)
    plotter.add_mesh(mesh)


def add_3d_models(qt):
    plotter, project_config = qt.plotter, qt.project_config
    for model in project_config['outputs']['3D_models']:
        model_path = model['model_path']
        mesh = pv.read(model_path)
        mesh = mesh.rotate_x(180)
        plotter.add_mesh(mesh)
    #plotter.reset_camera()

def add_nav_camera(qt):
    plotter, project_config, nav_data = qt.plotter, qt.project_config, qt.nav_data
    if qt.NavLayer.isChecked() and project_config['inputs']['navigation']:
        points = coord_conversions.position2d_2_local(nav_data, project_config['model_origin'])

        plotter.add_points(
            points.to_numpy(), render_points_as_spheres=True, point_size=10.0, scalars=nav_data[['depth']]
        )
        #plotter.reset_camera()


def plot_obj_with_multiple_textures(plotter, obj_path):
    obj_mesh = pv.read(obj_path)
    texture_dir = os.path.dirname(obj_path)

    pre = os.path.splitext(os.path.basename(obj_path))[0]

    mtl_path = os.path.join(texture_dir, f"{pre}.mtl")

    texture_paths = []
    mtl_names = []

    # parse the mtl file
    with open(mtl_path) as mtl_file:
        for line in mtl_file:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            if parts[0] == 'map_Kd':
                texture_paths.append(os.path.join(texture_dir, parts[1]))
            elif parts[0] == 'newmtl':
                mtl_names.append(parts[1])

    material_ids = obj_mesh.cell_arrays['MaterialIds']

    # This one do.
    for i in np.unique(material_ids):
        mesh_part = obj_mesh.extract_cells(material_ids == i)
        mesh_part.textures[mtl_names[i]] = pv.read_texture(texture_paths[i])
        plotter.add_mesh(mesh_part)
