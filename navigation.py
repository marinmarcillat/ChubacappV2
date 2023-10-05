import pandas as pd


def parse_nav_file_dim2(nav_path):
    nav_data = pd.read_csv(nav_path, sep=";", header=None, dtype=str, na_filter=False)
    nav_data_trim = nav_data.iloc[:, [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12]]
    nav_data_trim = nav_data_trim.set_axis(["date", "time", "camera", "name", "lat", "lon", "depth", "alt", "heading", "pitch", "roll"], axis=1, copy=False)
    nav_data_trim = nav_data_trim.astype({"lon": float, "lat": float, "depth": float, "alt": float, "heading": float, "pitch": float, "roll": float})
    return nav_data_trim

def parse_csv(nav_path):
    return pd.read_csv(nav_path)

