import pyvista as pv
import numpy as np
import os
import pandas as pd
import camera
import coord_conversions
from openmvg_json_file_handler import OpenMVGJSONFileHandler


def add_3d_cameras(qt):
    """
    Adds reconstructed 3D cameras to the plotter based on the project configuration.

    Args:
        qt: The main window object.

    Returns:
        None.
    """
    plotter, project_config = qt.plotter, qt.project_config
    if qt.CameraLayer.isChecked():
        models = project_config['outputs']['3D_models']
        if len(models) == 0:
            print("Missing camera to plot !")
        else:
            for model in models:
                sfm_path = model['sfm']
                cams = OpenMVGJSONFileHandler.parse_openmvg_file(sfm_path,  "NAME", True)
                points = []
                for cam in cams:
                    trsf_matrix, fov, shift, focal_length, res, dist = camera.get_cam_parameters(cam)
                    # camera_model = pv.Camera()
                    # camera_model.model_transform_matrix = trsf_matrix
                    # camera_model.clipping_range = [0.1, 1]
                    # frustum = camera_model.view_frustum(1.0)
                    # actor = plotter.add_mesh(frustum, style="wireframe")
                    points.append(trsf_matrix[:, -1][:-1].tolist())

                actor = plotter.add_points(
                    np.array(points), render_points_as_spheres=True, point_size=10.0
                )
                qt.plotter_actors['recon_camera'].append(actor)

    else:
        for actor in qt.plotter_actors['recon_camera']:
            _ = plotter.remove_actor(actor)



def add_mesh(plotter, obj_path):
    """
    Adds a mesh to the plotter.

    Args:
        plotter: The pyvista.Plotter object.
        obj_path: The path to the OBJ file.

    Returns:
        None.
    """
    mesh = pv.read(obj_path)
    plotter.add_mesh(mesh)


def add_3d_models(qt):
    """
    Adds 3D models to the plotter based on the project configuration.

    Args:
        qt: The main window object.

    Returns:
        None.
    """
    plotter, project_config = qt.plotter, qt.project_config
    if qt.ModelLayer.isChecked():
        models = project_config['outputs']['3D_models']
        if len(models) == 0:
            print("Missing 3D model !")
        else:
            for model in models:
                model_path = model['model_path']
                mesh = pv.read(model_path)
                #mesh = mesh.rotate_x(180)
                actor = plotter.add_mesh(mesh)
                qt.plotter_actors['3D_models'].append(actor)
    else:
        for actor in qt.plotter_actors['3D_models']:
            _ = plotter.remove_actor(actor)


def add_nav_camera(qt):
    """
    Adds navigation cameras to the plotter based on the project configuration and navigation data.

    Args:
        qt: The main window object.

    Returns:
        None.
    """
    plotter, project_config, nav_data = qt.plotter, qt.project_config, qt.nav_data
    if qt.NavLayer.isChecked():
        if project_config['inputs']['navigation']:
            points = coord_conversions.position2d_2_local(nav_data, project_config['model_origin'])

            actor = plotter.add_points(
                points.to_numpy(), render_points_as_spheres=True, point_size=10.0, scalars=nav_data[['depth']]
            )
            qt.plotter_actors['navigation'].append(actor)
        else:
            print("Missing navigation data !")
    else:
        for actor in qt.plotter_actors['navigation']:
            _ = plotter.remove_actor(actor)


def plot_obj_with_multiple_textures(plotter, obj_path):
    """
    Plots an OBJ file with multiple textures.

    Args:
        plotter: The pyvista.Plotter object.
        obj_path: The path to the OBJ file.

    Returns:
        None.
    """
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

def add_3d_annotations(qt):
    plotter, project_config = qt.plotter, qt.project_config
    if qt.AnnotationsLayer.isChecked():
        ann_path = project_config['outputs']['3D_annotation_path']
        if ann_path:
            points_pd = pd.read_pickle(os.path.join(ann_path, "points.pkl"))
            filenames = points_pd['filename'].to_list()
            points = points_pd['points'].to_list()

            actor = plotter.add_points(
                np.array(points, dtype='float'), render_points_as_spheres=True, point_size=10.0, color = 'red',
            )
            qt.plotter_actors['3D_annotations'].append(actor)

            polygons_pd = pd.read_pickle(os.path.join(ann_path, "polygons.pkl"))
            polygons = polygons_pd[polygons_pd['filename'].isin(filenames)]['points'].to_list()
            for polygon in polygons:
                polygon.append(polygon[0])
                actor = plotter.add_lines(np.array(polygon, dtype='float'), connected=True, color='purple', width=3)
                qt.plotter_actors['3D_annotations'].append(actor)

        else:
            print("Missing reprojected_annotations data !")
    else:
        for actor in qt.plotter_actors['3D_annotations']:
            _ = plotter.remove_actor(actor)
