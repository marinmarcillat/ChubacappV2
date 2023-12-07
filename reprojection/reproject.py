import camera
from openmvg_json_file_handler import OpenMVGJSONFileHandler
import pyembree
import itertools
import numpy as np
import trimesh
import os
import video_annotations
import ast
from math import dist
import pandas as pd
from datetime import datetime
from PyQt5 import QtCore


def get_reproj_cameras(hit_maps_dir):
    hit_maps = os.listdir(hit_maps_dir)
    cam_list = {}
    for hm in hit_maps:
        img = hm.rsplit('.', maxsplit=1)[0]
        str_dt = img.rsplit('.', maxsplit=1)[0]
        date_object = datetime.strptime(str_dt, "%Y%m%dT%H%M%S.%fZ")
        hm_path = os.path.join(hit_maps_dir, hm)
        cam_list[img] = {"datetime": date_object, "hm": hm_path}
    cam_df = pd.DataFrame.from_dict(cam_list, orient='index')
    cam_df['image_name'] = cam_df.index
    return cam_df


class annotationTo3D():
    def __init__(self, annotation_path: str, hit_maps_dir: str, video_dir: str = None):
        self.annotation_path = annotation_path
        self.hit_maps_dir = hit_maps_dir
        self.video_dir = video_dir

        self.reproj_cameras = get_reproj_cameras(self.hit_maps_dir)

        self.min_x = self.min_y = 0
        self.max_x = 0
        self.max_y = 0

        self.min_radius = 0.01
        self.points_bound = None

    def annotation2hitpoint(self, ann_coords, hit_map):
        (x, y) = ann_coords
        if self.min_x < x < self.max_x and self.min_y < y < self.max_y:
            coord = hit_map[int(x)][int(y)]
            if np.array_equal(coord, [0,0,0]):
                return None
            return coord
        return None

    def get_image_bound(self):
        # List of points corresponding to the image bound
        edge1 = [(x, self.min_y + 1) for x in range(self.min_x + 1, self.max_x - 1)]
        edge2 = [(self.max_x - 1, y) for y in range(self.min_y + 1, self.max_y - 1)]
        edge3 = [(x, self.max_y - 1) for x in range(self.max_x - 1, self.min_x + 1, -1)]
        edge4 = [(self.min_x + 1, y) for y in range(self.max_y - 1, self.min_y + 1, -1)]
        points_bound = edge1 + edge2 + edge3 + edge4
        self.points_bound = list(itertools.chain(*points_bound))

    def get_hit_map(self, hit_map_path):
        hit_map = np.load(hit_map_path)
        self.max_x, self.max_y = hit_map.shape[:2]
        self.get_image_bound()
        return hit_map

    def reproject_annotations(self):
        if self.video_dir is not None:
            print("Retrieve video annotations tracks...")
            annotations = video_annotations.get_annotations_tracks(self.annotation_path, self.reproj_cameras, self.video_dir)
            annotations = annotations.rename(columns={"image_name": "filename"})
        else:
            annotations = pd.read_csv(self.annotation_path, sep=",")
            annotations['points'] = annotations['points'].apply(lambda x: ast.literal_eval(x))


        point = []
        polygon = []
        line = []
        for image in self.reproj_cameras['image_name']:
            ann_img = annotations.loc[annotations['filename'] == image]
            result = self.reproject(ann_img, image, False)
            point.extend(result[0])
            line.extend(result[1])
            polygon.extend(result[2])
        print(polygon)
        print("Done")

    def reproject(self, annotations, image, label):
        point = []
        polygon = []
        line = []
        image_info = self.reproj_cameras[self.reproj_cameras['image_name'] == image].iloc[0]
        hit_map = self.get_hit_map(image_info['hm'])
        if label:
            annotations['shape_name'] = 'Rectangle'
            annotations['points'] = self.points_bound
            annotations['annotation_id'] = -999
        else:
            image_bound = pd.DataFrame({
                'filename': [image],
                'shape_name': ['Rectangle'],
                'points': [self.points_bound],
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
                    vertexes = self.points_bound
                else:
                    vertexes = ann['points']
                list_coord = list(zip(*[iter(vertexes)] * 2))
                points_out = []
                for i in list_coord:  # For all the points of the polygone
                    # get the location of the intersection between ray and target
                    coord = self.annotation2hitpoint((i[0], i[1]), hit_map)

                    if coord is not None:
                        points_out.append([coord[0], coord[1], coord[2]])
                if points_out:  # If more than one point exist
                    polygon.append(
                        [points_out, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                         ann['annotation_id']])

        return point, line, polygon


class reprojector(QtCore.QThread):
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, model, sfm, images, export):
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



