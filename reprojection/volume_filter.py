import pandas as pd
import numpy as np
import pyvista as pv
from pyntcloud import PyntCloud
from statistics import mean, stdev, median, quantiles
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

def imprint_to_volume(track):
    vol_list = []
    for points in track['points']:
        points = list(list(map(float, pt)) for pt in points)
        polygons_pts = pv.PolyData(points)
        mesh = polygons_pts.delaunay_2d()
        vol_list.append(mesh_to_volume(mesh))
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
    vol_list = imprint_to_volume(track)
    extracted_point_cloud = extract_all_points_in_volumes(point_cloud, vol_list)
    metrics = point_cloud_stat_summary(extracted_point_cloud)
    metrics_pd = pd.DataFrame(metrics, columns=['metrics_name', 'mean', 'sd', 'median', 'q1', "q3"])
    metrics_pd['track'] = track['ann_id']
    return metrics_pd
