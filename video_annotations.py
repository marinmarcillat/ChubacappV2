import pandas as pd
import ast
import datetime
import numpy as np
import pandas as pd
import os, imghdr
import ast

def report_type(file_path):
    """
    Determines the type of report based on the file path.

    Args:
        file_path: The path to the file.

    Returns:
        str: The report type ("img" for image or "video" for video).
    """
    annotations = pd.read_csv(file_path, sep=",")
    col = annotations.columns[0]
    report_type = None
    if col == "annotation_label_id":
        report_type = "img"
    elif col == "video_annotation_label_id":
        report_type = "video"
    return report_type

def parse_video_name(file_name):
    name = file_name.rsplit('.', maxsplit=1)[0]
    time_str = name.split('_')[2]
    return datetime.datetime.strptime(time_str, "%y%m%d%H%M%S")

def get_video_list(video_dir):
    """
    Retrieves a list of videos from the specified directory.

    Args:
        video_dir: The directory containing the videos.

    Returns:
        pandas.DataFrame: A DataFrame containing the video information.
    """
    video_list = {}
    for file in sorted(os.listdir(video_dir)):
        video_path = os.path.join(video_dir, file)
        if os.path.isfile(video_path) and file.endswith(".mp4"):
            date_object = parse_video_name(file)
            video_list[file] = {"datetime_start": date_object, "path": video_path}
    return pd.DataFrame.from_dict(video_list, orient='index')


def get_img_list(img_path):
    """
    Retrieves a list of images from the specified directory.

    Args:
        img_path: The directory containing the images.

    Returns:
        list: A list of image names.
    """
    img_list = []
    for file in sorted(os.listdir(img_path)):
        jpg_path = os.path.join(img_path, file)
        if os.path.isfile(jpg_path) and imghdr.what(jpg_path) == "jpeg":
            img_list.append(file)
    return img_list


def get_annotations_tracks(annotation_path, reproj_cameras):
    """
    Retrieves the annotation tracks based on the annotation file, reprojected cameras, and video directory.

    Args:
        annotation_path: The path to the annotation file.
        reproj_cameras: The reprojected cameras.
        video_dir: The directory containing the videos.

    Returns:
        pandas.DataFrame: A DataFrame containing the annotation tracks.
    """
    annotations = pd.read_csv(annotation_path, sep=",", )

    video_list_from_annotation = annotations['video_filename'].unique().tolist()
    video_list = {}
    for video in video_list_from_annotation:
        date_object = parse_video_name(video)
        video_list[video] = {"datetime_start": date_object, "video_name": video}
    video_from_annotation_pd = pd.DataFrame.from_dict(video_list, orient='index').sort_values('datetime_start')


    merged = pd.merge_asof(reproj_cameras, video_from_annotation_pd, left_on='datetime', right_on='datetime_start', direction='backward').dropna()
    merged['timestamp_obj'] = merged['datetime'] - merged['datetime_start']
    merged['timestamp'] = merged.timestamp_obj.apply(lambda x: x.total_seconds())

    img_df = merged[["timestamp", "video_name", "image_name"]]
    reprojectable_videos = img_df['video_name'].unique().tolist()

    interval = 2  #TODO Set dynamically the interval

    # prepare all tracks for reprojection
    ann_tracks = pd.DataFrame(
        columns=['timestamp', 'points', 'image_name', 'shape_name', 'label_name', 'label_hierarchy', 'annotation_id'])
    for video in reprojectable_videos:
        annotations_filt = annotations[annotations['video_filename'] == video]
        img_df_filt = img_df[img_df['video_name'] == video].sort_values(['timestamp'])
        for index, row in annotations_filt.iterrows():
            timestamps = ast.literal_eval(row['frames'].replace('null', "'NaN'"))
            points = ast.literal_eval(row['points'].replace('null', "'NaN'"))

            if len(timestamps) == 2:  # Time interval
                timestamps_range = []
                reprojectable_timestamps = img_df_filt['timestamp'].tolist()
                start, end = timestamps
                closest_start = min(reprojectable_timestamps, key=lambda x: abs(x - start))
                closest_end = min(reprojectable_timestamps, key=lambda x: abs(x - end))
                if closest_start != closest_end:  # if start not after end of reprojectable timestamps and end not before start
                    index_start = reprojectable_timestamps.index(closest_start)
                    index_end = reprojectable_timestamps.index(closest_end)
                    timestamps_range = reprojectable_timestamps[index_start:index_end]
                tracking = pd.DataFrame({'timestamp': timestamps_range, 'points': [None for i in range(len(timestamps_range))]})
            else:  # Normal annotation
                tracking = pd.DataFrame({'timestamp': timestamps,'points': points}).astype({"timestamp": float})

            tracking_merged = pd.merge_asof(tracking, img_df_filt, on='timestamp', direction='nearest', tolerance=interval)
            tracking_merged = tracking_merged[tracking_merged['image_name'].notnull()]
            tracking_merged['shape_name'], tracking_merged['label_name'], tracking_merged['label_hierarchy'], tracking_merged['annotation_id'] = [
                row['shape_name'], row['label_name'], row['label_hierarchy'], row['video_annotation_label_id']]
            if len(tracking_merged) != 0:
                ann_tracks = pd.concat([ann_tracks, tracking_merged], ignore_index=True)

    return ann_tracks

def frame_to_time(frame_list, start_time):
    """
    Converts a list of frame numbers to corresponding timestamps.

    Args:
        frame_list: The list of frame numbers.
        start_time: The start time of the video.

    Returns:
        list: A list of timestamps.
    """
    result = []
    for i in frame_list:
        td = datetime.timedelta(seconds=i)
        result.append(start_time+td)
    return result


def import_video_annotations(ann_path, start_time):
    """
    Imports video annotations from a CSV file.

    Args:
        ann_path: The path to the annotation file.
        start_time: The start time of the video.

    Returns:
        pandas.DataFrame: A DataFrame containing the imported video annotations.
    """
    data = pd.read_csv(ann_path)
    data['frames'] = data.frames.apply(lambda x: ast.literal_eval(str(x)))
    data['points'] = data.points.apply(lambda x: ast.literal_eval(str(x)))
    data['frames_time'] = data.frames.apply(lambda x: frame_to_time(x, start_time))
    return data
