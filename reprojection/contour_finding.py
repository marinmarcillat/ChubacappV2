import cv2
import numpy as np
import itertools

def find_contour(hit_map):
    width = hit_map.shape[0]
    height = hit_map.shape[1]

    hm_array = hit_map.copy()
    for a in range(hm_array.shape[0]):
        for b in range(hm_array.shape[1]):
            if not np.array_equal(hm_array[a][b], np.array([0, 0, 0])):
                hm_array[a][b] = np.array([255, 255, 255])
    hm_array = hm_array.astype(np.uint8)
    img = np.rot90(hm_array)  #Transform to horizontal image
    img = np.pad(img, pad_width=((10, 10), (10, 10), (0, 0)))

    edged = cv2.Canny(img, 30, 200)
    contours, hierarchy = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    longest_contour = max(contours, key=len)

    contour = list(itertools.chain(*longest_contour.tolist()))
    contour.append(contour[0])
    for i in range(len(contour)):
        # Remove padding and inverse y-axis
        coord_point_contour = [contour[i][0] - 10, height - (contour[i][1] - 10)]
        # If contour slightly off image, get back on it
        coord_point_contour = [max(min(coord_point_contour[0], width - 1), 0), max(min(coord_point_contour[1], height - 1), 0)]
        # If contour slightly offset, get the closest point that's hit
        if np.array_equal(hit_map[coord_point_contour[0]][coord_point_contour[1]], [0,0,0]):
            coord_point_contour = search_around(coord_point_contour, hit_map)

        # Convert to annotation format (y-axis inverted)
        contour[i] = [coord_point_contour[0], hit_map.shape[1] - coord_point_contour[1]]
    contour = list(itertools.chain(*contour))
    return contour

def search_around(point, hm):
    for radius in range(1, 4):
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                x = point[0]+i
                y = point[1]+j
                if 0 <= x < hm.shape[0] and 0 <= y < hm.shape[1]:
                    if not np.array_equal(hm[x][y], [0,0,0]):
                        return [x, y]
    return point