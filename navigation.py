import pandas as pd


def parse_nav_file_dim2(nav_path):
    """
Parse a navigation file with 2-dimensional data.

Args:
    nav_path (str): The path to the navigation file.

Returns:
    pandas.DataFrame: The parsed navigation data with trimmed columns.

Examples:
    >>> nav_data = parse_nav_file_dim2("path/to/nav_file.csv")
    >>> print(nav_data.head())
         date      time camera  name        lat         lon  depth  alt  heading  pitch  roll
    0  2020-01-01  12:00:00    cam1  John  40.712776  -74.005974   10.0  0.0      0.0    0.0   0.0
    1  2020-01-01  12:01:00    cam1  John  40.712776  -74.005974   10.0  0.0      0.0    0.0   0.0
    2  2020-01-01  12:02:00    cam1  John  40.712776  -74.005974   10.0  0.0      0.0    0.0   0.0
    3  2020-01-01  12:03:00    cam1  John  40.712776  -74.005974   10.0  0.0      0.0    0.0   0.0
    4  2020-01-01  12:04:00    cam1  John  40.712776  -74.005974   10.0  0.0      0.0    0.0   0.0
"""

    nav_data = pd.read_csv(nav_path, sep=";", header=None, dtype=str, na_filter=False)
    nav_data_trim = nav_data.iloc[:, [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12]]
    nav_data_trim = nav_data_trim.set_axis(["date", "time", "camera", "name", "lat", "lon", "depth", "alt", "heading", "pitch", "roll"], axis=1, copy=False)
    nav_data_trim = nav_data_trim.astype({"lon": float, "lat": float, "depth": float, "alt": float, "heading": float, "pitch": float, "roll": float})
    return nav_data_trim

def parse_csv(nav_path):
    return pd.read_csv(nav_path)

