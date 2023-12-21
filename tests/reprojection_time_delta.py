import pandas as pd
import numpy as np
import pyvista as pv
from pyntcloud import PyntCloud
from statistics import mean, stdev, median, quantiles
from tqdm import tqdm


poly = r"D:\chereef_lophelia_22\polygons.pkl"
pcd_path = r"D:\chereef_lophelia_22\export\0\cloud_metrics_1.0.pcd"

def debug_plotter_pyvista(volume, pcd, mesh):
    """
    Plot annotation volume and point cloud data for debugging
    """
    pl = pv.Plotter()
    pl.add_mesh(pcd)
    #pl.add_mesh(volume)
    pl.add_mesh(mesh)
    pl.show()

def points_to_mesh(points):
    """
    Construct a mesh surface from polygons point using Delaunay triangulation
    :param points: polygons points
    :return: pyvista 3D mesh
    """
    # Reconstruct the polygon with 2 intermediary points added on each edge

    pts = np.array(points, dtype=np.uint8)
    polygons_pts = pv.PolyData(pts)  # Convert to pyvista format
    mesh = polygons_pts.delaunay_2d(offset=0.5)  # Delaunay triangulation
    return mesh

def mesh_to_volume(mesh):
    mesh.compute_normals(inplace=True)
    mesh.compute_normals(cell_normals=True, point_normals=False, inplace=True)
    normals = np.asarray(mesh['Normals'])
    vect = np.asarray([mean(normals[:, 0]), mean(normals[:, 1]), mean(normals[:, 2])])
    mesh_bottom = mesh.translate(-vect, inplace=True)
    return mesh_bottom.extrude(4 * vect, capping=True)


test = pd.read_pickle(poly)

pcd = PyntCloud.from_file(pcd_path)
point_cloud = pv.PolyData(np.asarray(pcd.points[['x', 'y', 'z']]))
scalars = pcd.points.columns.to_list()
scalars = [x for x in scalars if
           not (x.startswith("__") or x.startswith("normal_") or x in ["x", "y", "z"])]
for scalar in scalars:
    point_cloud[scalar] = pcd.points[[scalar]]

ids = test['ann_id'].unique().tolist()
ids.remove(-999)

def to_volume(i):
    track = test[test['ann_id'] == ids[i]]
    vol_list = []
    for points in track['points']:
        points = list(list(map(float, pt)) for pt in points)
        polygons_pts = pv.PolyData(points)
        mesh = polygons_pts.delaunay_2d()
        vol_list.append(mesh_to_volume(mesh))
    return vol_list

v_list = to_volume(0)

def filter_volume(vol):
    result = point_cloud.select_enclosed_points(vol, tolerance=0, check_surface=False)
    return point_cloud.extract_points(
        result['SelectedPoints'].view(bool),
        adjacent_cells=False,
    )

result = None
for vol in tqdm(v_list):
    inside = filter_volume(vol)
    if result is None:
        result = inside.extract_surface()
    else:
        result += inside.extract_surface()
        result = result.clean()
    count = len(np.asarray(result[result.array_names[0]]))
    print(count)


pl = pv.Plotter()
pl.add_mesh(v_list[0])
pl.add_mesh(result)
pl.show()

print('ok')