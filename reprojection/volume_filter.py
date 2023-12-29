import os
import pandas as pd
import numpy as np
import pyvista as pv
from statistics import mean, stdev, median, quantiles
from pv_utils import parse_point_clouds
from tqdm import tqdm

def mesh_to_volume(mesh):
    mesh.compute_normals(inplace=True)
    mesh.compute_normals(cell_normals=True, point_normals=False, inplace=True)
    normals = np.asarray(mesh['Normals'])
    vect = np.asarray([mean(normals[:, 0]), mean(normals[:, 1]), mean(normals[:, 2])])
    mesh_bottom = mesh.translate(-vect, inplace=True)
    return mesh_bottom.extrude(4 * vect, capping=True)

def extract_points_in_volume(point_cloud, vol):
    result = point_cloud.select_enclosed_points(vol, tolerance=0, check_surface=False)
    return point_cloud.extract_points(
        result['SelectedPoints'].view(bool),
        adjacent_cells=False,
    )

def imprint_to_volume(points):
    points = list(list(map(float, pt)) for pt in points)
    polygons_pts = pv.PolyData(points)
    mesh = polygons_pts.delaunay_2d()
    return mesh_to_volume(mesh)


def list_imprint_to_list_volumes(track):
    vol_list = []
    for points in track['points']:
        vol = imprint_to_volume(points)
        vol_list.append(vol)
    return vol_list


def extract_all_points_in_volumes(point_cloud, v_list):
    result = None
    for vol in tqdm(v_list):
        inside = extract_points_in_volume(point_cloud, vol)
        if result is None:
            result = inside.extract_surface()
        else:
            result += inside.extract_surface()
            result = result.clean()
    return result

def point_cloud_stat_summary(point_cloud):
    names = point_cloud.array_names
    names = [x for x in names if not x.startswith("vtkOriginal")]
    metrics = []
    if point_cloud.number_of_points != 0:
        for name in names:  # For each metric
            point_cloud.set_active_scalars(name)
            sf = np.asarray(point_cloud[name])  # activate and retrieve the metric
            sf = sf[~np.isnan(sf)]  # Remove any nan values
            if len(sf) != 0:
                # Summarise the metric
                m = mean(sf)
                sd = stdev(sf)
                med = median(sf)
                q1, q2, q3 = quantiles(sf)
            else:
                m = sd = med = q1 = q3 = np.nan
            metrics.append([name, m, sd, med, q1, q3])
    return metrics

def summarise_track(point_cloud, track):
    vol_list = list_imprint_to_list_volumes(track)
    extracted_point_cloud = extract_all_points_in_volumes(point_cloud, vol_list)
    metrics = point_cloud_stat_summary(extracted_point_cloud)
    metrics_pd = pd.DataFrame(metrics, columns=['metrics_name', 'mean', 'sd', 'median', 'q1', "q3"])
    metrics_pd['track'] = track['ann_id']
    return metrics_pd

def summarise_polygon(point_cloud, annotations):
    vol = imprint_to_volume(annotations["points"])
    extracted_point_cloud = extract_points_in_volume(point_cloud, vol)
    metrics = point_cloud_stat_summary(extracted_point_cloud)
    metrics_pd = pd.DataFrame(metrics, columns=['metrics_name', 'mean', 'sd', 'median', 'q1', "q3"])
    metrics_pd['track'] = annotations['ann_id']
    return metrics_pd

def stat_summary(point_cloud_dir, annotations, vid_tracks_only):
    polygon_summary_pd = None
    tracks_summary_pd = None
    list_point_cloud = parse_point_clouds(point_cloud_dir)

    track_ids = annotations['ann_id'].unique().tolist()
    track_ids.remove(-999)
    ann_ids = annotations['ann_id'].tolist()
    track_ids_ = []
    for id in track_ids:
        if ann_ids.count(id) >= 2:
            track_ids_.append(id)
    tracked_annotations = annotations[annotations['ann_id'].isin(track_ids_)]
    non_tracked_annotations = annotations[-annotations['ann_id'].isin(track_ids_)]

    for point_cloud in list_point_cloud:
        if len(tracked_annotations) != 0:
            tracks_summary_pd = summarise_track(point_cloud, tracked_annotations)
        if not vid_tracks_only and len(non_tracked_annotations) != 0:
            polygon_summary_pd = summarise_polygon(point_cloud, non_tracked_annotations)


    return polygon_summary_pd, tracks_summary_pd


def save_stat_summary(summary_pd, name, output_dir):
    export_path = os.path.join(output_dir, name)
    summary_pd.to_csv(export_path, index=False)




