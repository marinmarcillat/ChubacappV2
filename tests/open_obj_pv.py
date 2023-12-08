import pyvista as pv

obj_path = r"D:\chereef22\colmap_prior\export\0\textured_mesh.glb"

plotter = pv.Plotter()
plotter.enable_anti_aliasing('ssaa')
test = plotter.import_gltf(obj_path)
plotter.show()

print("ok")