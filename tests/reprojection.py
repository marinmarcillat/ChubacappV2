import pandas as pd
import numpy as np
from reprojection.reproject import get_reproj_cameras
import video_annotations

HM_path = r"Q:\colmap_prior\hit_maps\20220819T172222.000000Z.jpg.npy"
video_dir = r"V:\01_MOSAIQUES\ChEReef22\Falaise_Lophelia\PL821_12"
hit_maps_dir = r"U:\colmap_prior\hit_maps"
reproj_cameras = get_reproj_cameras(hit_maps_dir)

annotation_path = r"U:\chereef_lophelia_22\annotations\115-lophelia-cliff.csv"

annotations = video_annotations.get_annotations_tracks(annotation_path, reproj_cameras, video_dir)

print('ok')