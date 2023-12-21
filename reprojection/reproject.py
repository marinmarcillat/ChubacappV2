import camera
from openmvg_json_file_handler import OpenMVGJSONFileHandler
import pyembree
from reprojection.contour_finding import find_contour
import itertools
import numpy as np
import trimesh
import os
import video_annotations
import ast
from math import dist
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from PyQt5 import QtCore


def get_reproj_cameras(hit_maps_dir):
    hit_maps = os.listdir(hit_maps_dir)
    cam_list = {}
    for hm in hit_maps:
        if hm.endswith('.npy'):
            hm_path = os.path.join(hit_maps_dir, hm)
            img = hm.rsplit('.', maxsplit=1)[0]
            str_dt = img.rsplit('.', maxsplit=1)[0]
            date_object = datetime.strptime(str_dt, "%Y%m%dT%H%M%S.%fZ")
            cam_list[img] = {"datetime": date_object, "hm": hm_path}
    cam_df = pd.DataFrame.from_dict(cam_list, orient='index')
    cam_df['image_name'] = cam_df.index
    return cam_df


class annotationTo3D():
    def __init__(self, annotation_path: str, hit_maps_dir: str, report_type: bool, wholeframe_only: bool =  False):
        self.annotation_path = annotation_path
        self.hit_maps_dir = hit_maps_dir
        self.wholeframe_only = wholeframe_only
        self.report_type = report_type

        self.reproj_cameras = get_reproj_cameras(self.hit_maps_dir)

        self.min_x = self.min_y = 0
        self.max_x = 0
        self.max_y = 0

        self.min_radius = 0.01

    def annotation2hitpoint(self, ann_coords, hit_map):
        (x, y) = ann_coords
        if self.min_x < x < self.max_x and self.min_y < y < self.max_y:
            y = self.max_y - y  # Inverse Y axis
            coord = hit_map[int(x)][int(y)]
            if np.array_equal(coord, [0, 0, 0]):
                return None
            return coord
        return None

    def get_hit_map(self, hit_map_path):
        hit_map = np.load(hit_map_path)
        self.max_x, self.max_y = hit_map.shape[:2]
        contour = find_contour(hit_map)
        return hit_map, contour

    def reproject_annotations(self):
        if self.report_type is not None:
            print("Retrieve video annotations tracks...")
            annotations = video_annotations.get_annotations_tracks(self.annotation_path, self.reproj_cameras)
            annotations = annotations.rename(columns={"image_name": "filename"})
            if self.wholeframe_only:
                annotations = annotations[annotations['shape_name'] == 'WholeFrame']
        else:
            annotations = pd.read_csv(self.annotation_path, sep=",")
            annotations['points'] = annotations['points'].apply(lambda x: ast.literal_eval(x))

        point = []
        polygon = []
        line = []
        annotation_output_dir = os.path.dirname(self.annotation_path)
        print("Starting reprojection...")
        for image in tqdm(self.reproj_cameras['image_name']):
            ann_img = annotations.loc[annotations['filename'] == image]
            result = self.reproject(ann_img, image, False)
            point.extend(result[0])
            line.extend(result[1])
            polygon.extend(result[2])
            point_pd = pd.DataFrame(point, columns=['points', 'label', 'label_hier', 'filename', 'ann_id', 'radius'])
            line_pd = pd.DataFrame(line, columns=['points', 'label', 'label_hier', 'filename', 'ann_id'])
            polygon_pd = pd.DataFrame(polygon, columns=['points', 'label', 'label_hier', 'filename', 'ann_id', "misses"])

            point_pd.to_pickle(os.path.join(annotation_output_dir, 'points.pkl'))
            line_pd.to_pickle(os.path.join(annotation_output_dir, 'lines.pkl'))
            polygon_pd.to_pickle(os.path.join(annotation_output_dir, 'polygons.pkl'))

        return annotation_output_dir

    def reproject(self, annotations, image, label):
        point = []
        polygon = []
        line = []
        image_info = self.reproj_cameras[self.reproj_cameras['image_name'] == image].iloc[0]
        hit_map, contour = self.get_hit_map(image_info['hm'])
        if label:
            annotations['shape_name'] = 'WholeFrame'
            annotations['points'] = contour
            annotations['annotation_id'] = -999
        else:
            image_bound = pd.DataFrame({
                'filename': [image],
                'shape_name': ['WholeFrame'],
                'points': [contour],
                'label_name': ['bound'],
                'label_hierarchy': ['bound'],
                'annotation_id': [-999],
            })
            annotations = pd.concat([annotations, image_bound])

        for index, ann in annotations.iterrows():  # for each annotation
            if ann['shape_name'] == 'Circle':  # if the annotation is a point or a circle
                x, y = ann['points'][:2]

                # get the location of the intersection between ray and target
                coord = self.annotation2hitpoint((x, y), hit_map)

                if coord is not None:  # If we have a hit point
                    # If the annotation is a circle, we try to get an approximate radius by looking
                    # North, South, East and West from the center. We then keep the minimal distance
                    # obtained
                    radius = []  # min arbitrary value
                    r = ann['points'][2]
                    list_coord_r = [(x + r, y), (x - r, y), (x, y + r), (x, y - r)]
                    for i in list_coord_r:
                        # get the location of the intersection between ray and target
                        coord_radius = self.annotation2hitpoint((i[0], i[1]), hit_map)

                        if coord_radius is not None:
                            ct = [coord[0], coord[1]]
                            off = [coord_radius[0], coord_radius[1]]
                            radius.append(dist(ct, off))
                    radius = min(radius, default=self.min_radius)
                    point.append([[coord[0], coord[1], coord[2]], ann['label_name'], ann['label_hierarchy'],
                                  ann['filename'],
                                  ann['annotation_id'], radius])

            elif ann['shape_name'] == 'Point':  # if the annotation is a point or a circle
                x, y = ann['points'][:2]

                # get the location of the intersection between ray and target
                coord = self.annotation2hitpoint((x, y), hit_map)

                if coord is not None:  # If we have a hit point
                    radius = 0
                    point.append([[coord[0], coord[1], coord[2]], ann['label_name'], ann['label_hierarchy'],
                                  ann['filename'],
                                  ann['annotation_id'], radius])

            elif ann['shape_name'] == 'LineString':  # if geometry is a line
                list_coord = list(zip(*[iter(ann['points'])] * 2))
                points_out = []
                for i in list_coord:
                    # get the location of the intersection between ray and target
                    coord = self.annotation2hitpoint((i[0], i[1]), hit_map)
                    if coord is not None:
                        points_out.append([coord[0], coord[1], coord[2]])
                if points_out:
                    line.append(
                        [points_out, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                         ann['annotation_id']])

            elif ann['shape_name'] in ['Polygon', 'Rectangle', "WholeFrame"]:  # if geometry is a polygon or rectangle
                if ann['shape_name'] == "WholeFrame":
                    vertexes = contour
                else:
                    vertexes = ann['points']
                list_coord = list(zip(*[iter(vertexes)] * 2))
                points_out = []
                count = 0
                for i in list_coord:  # For all the points of the polygone
                    # get the location of the intersection between ray and target
                    coord = self.annotation2hitpoint((i[0], i[1]), hit_map)

                    if coord is not None:
                        points_out.append([coord[0], coord[1], coord[2]])
                    else:
                        count+=1
                        print("stop")
                if points_out:  # If more than one point exist
                    polygon.append(
                        [points_out, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                         ann['annotation_id'], count])

        return point, line, polygon


class reprojector(QtCore.QThread):
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, model, sfm, export):
        super(reprojector, self).__init__()
        self.running = True

        self.export = export
        mesh = trimesh.load(model)
        self.intersector = trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)
        self.scene = trimesh.Scene([mesh])

        self.cams = OpenMVGJSONFileHandler.parse_openmvg_file(sfm, "NAME", True)

    def run(self):
        try:
            tot_len = len(self.cams)
            for prog, cam in enumerate(self.cams, start=1):
                hit_map = self.convert_to_hit_map(cam)
                self.save_hit_map(cam, hit_map)
                self.prog_val.emit(round((prog / tot_len) * 100))

        except RuntimeError:
            self.gui.normalOutputWritten("An error occurred")
        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False

    def save_hit_map(self, cam, hit_map):
        export_path = os.path.join(self.export, cam.get_relative_fp())
        np.save(export_path, hit_map)

    def convert_to_hit_map(self, cam):
        trsf_matrix, fov, shift, focal_length, res, dist = camera.get_cam_parameters(cam)

        self.scene.camera.resolution = res
        self.scene.camera.fov = np.rad2deg(fov)

        self.scene.camera_transform = trsf_matrix

        # convert the camera to rays with one ray per pixel
        origins, vectors, pixels = self.scene.camera_rays()
        points, index_ray, index_tri = self.intersector.intersects_location(
            origins, vectors, multiple_hits=False)
        # find pixel locations of actual hits
        pixel_ray = pixels[index_ray]
        # create a numpy array we can turn into an image
        # doing it with uint8 creates an `L` mode greyscale image
        a = np.zeros(np.append(res, 3), dtype=np.float16)
        a[pixel_ray[:, 0], pixel_ray[:, 1]] = points
        return a
