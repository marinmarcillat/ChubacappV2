import cv2
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import itertools

npy_path = r"D:\chereef_lophelia_22\hit_maps\20220819T170015.000Z.jpg.npy"

def search_around(point, hm):
    for radius in range(1,4):
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                if not np.array_equal(hm[point[0]+i][point[1]+j], [0,0,0]):
                    return [point[0]+i, point[1]+j]
    return point

test = np.load(npy_path)
t1 = np.zeros([1920, 1080])
for a in tqdm(range(test.shape[0])):
    for b in range(test.shape[1]):
        if not np.array_equal(test[a][b], np.array([0, 0, 0])):
            test[a][b] = np.array([255, 255, 255])
            t1[a][b] = 1
hm_array = test.astype(np.uint8)
img = np.rot90(hm_array)
img = np.pad(img, pad_width=((10, 10), (10, 10), (0,0)))

edged = cv2.Canny(img, 30, 200)

# Finding Contours
# Use a copy of the image e.g. edged.copy()
# since findContours alters the image
contours, hierarchy = cv2.findContours(edged,
                                       cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)


longest_contour = max(contours, key=len)
contour = list(itertools.chain(*longest_contour.tolist()))

t2 = np.zeros([1920, 1080])
count = 0
for i in range(len(contour)):
    coord_point_contour = [contour[i][0] - 10, t1.shape[1] - (contour[i][1] - 10)]
    if np.array_equal(test[coord_point_contour[0]][coord_point_contour[1]], [0, 0, 0]):
        coord_point_contour = search_around(coord_point_contour, test)
        if np.array_equal(test[coord_point_contour[0]][coord_point_contour[1]], [0, 0, 0]):
            count += 1
            t2[coord_point_contour[0]][coord_point_contour[1]] = 1
            t1[coord_point_contour[0]][coord_point_contour[1]] = 2


print("ok")
print("end")
