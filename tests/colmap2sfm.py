import reconstruction.utils as utils
import os
import json

image_path = r"D:\chereef22\colmap_prior\save\images.txt"
camera_path = r"D:\chereef22\colmap_prior\save\cameras.txt"
model_export_path = r"D:\chereef22\colmap_prior\save"


list_poses = utils.read_images_text(image_path, [0, 0, 0])
camera = utils.read_cameras_text(camera_path)
sfm = utils.listposes2sfm(list_poses, camera)
with open(os.path.join(model_export_path, "sfm_data_temp.json"), 'w') as fp:
    json.dump(sfm, fp, sort_keys=True, indent=4)