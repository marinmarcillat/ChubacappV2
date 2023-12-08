import pyvista as pv
import trimesh
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
        qt.plotter_actors['recon_camera'] = []



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
        qt.plotter_actors['3D_models'] = []


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
        qt.plotter_actors['navigation'] = []


def add_textured_models(qt):
    """
    Plots an OBJ file with multiple textures.

    Args:
        qt: The main window object.

    Returns:
        None.
    """
    plotter, project_config = qt.plotter, qt.project_config
    if qt.TexturedModelLayer.isChecked():
        models = project_config['outputs']['3D_models']
        if len(models) == 0:
            print("Missing 3D model !")
        else:
            for model in models:
                tex_model_path = model['textured_model_path']
                sc_dir = os.path.dirname(tex_model_path)
                pre = os.path.splitext(os.path.basename(tex_model_path))[0]
                glb_path = os.path.join(sc_dir, f"{pre}.glb")
                if not os.path.exists(glb_path):
                    print("Converting to glb")
                    mesh = trimesh.load(tex_model_path)
                    mesh.export(file_obj=glb_path)

                prev_actors = list(plotter.actors.keys())
                plotter.import_gltf(glb_path)
                act_actors = list(plotter.actors.keys())

                new_key = set(act_actors).difference(prev_actors)
                actor = plotter.actors[list(new_key)[0]]
                qt.plotter_actors['textured_models'].append(actor)
    else:
        #TODO: make it work !
        for actor in qt.plotter_actors['textured_models']:
            _ = plotter.remove_actor(actor)





def add_3d_annotations(qt):
    plotter, project_config = qt.plotter, qt.project_config
    if qt.AnnotationsLayer.isChecked():
        ann_path = project_config['outputs']['3D_annotation_path']
        if ann_path:
            plotter.enable_anti_aliasing('ssaa')
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
