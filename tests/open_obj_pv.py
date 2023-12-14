import pyvista as pv
import numpy as np
from pyntcloud import PyntCloud



pcd_path = r"U:\colmap_prior\export\0\cloud_metrics_1.0.pcd"

pcd = PyntCloud.from_file(pcd_path)
point_cloud = pv.PolyData(np.asarray(pcd.points[['x','y','z']]))
scalars = pcd.points.columns.to_list()
scalars = [x for x in scalars if not (x.startswith("__") or x.startswith("normal_") or x in ["x", "y", "z"])]
for scalar in scalars:
    point_cloud[scalar] = pcd.points[[scalar]]

plotter = pv.Plotter()
plotter.add_mesh(point_cloud)
plotter.show()


print("ok")