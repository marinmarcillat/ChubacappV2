import cv2
import os
from PyQt5 import QtCore
from datetime import datetime, timedelta
import pandas as pd

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
            name = video_path.rsplit('.', maxsplit=1)[0]
            time_str = name.split('_')[2]
            date_object = datetime.strptime(time_str, "%y%m%d%H%M%S")
            video_list[file] = {"datetime_start": date_object, "path": video_path}
    return pd.DataFrame.from_dict(video_list, orient='index')

class ExtractImageThread(QtCore.QThread):
    """
    A thread for extracting images from videos and generating navigation data.

    Args:
        video_df: The DataFrame containing video information.
        dir_out: The output directory for extracted images.
        sampling_time: The sampling time for extracting images.
        video_nav_path: The path to the video navigation file.

    Attributes:
        finished: A PyQt signal emitted when the thread finishes.
        nav_path: A PyQt signal emitted with the path to the extracted navigation file.

    Methods:
        run(self): Runs the thread.
        extract_images(self, video_path, dir_out, start_time, sampling_time): Extracts images from a video.
        generate_navigation(self, video_navigation_path): Generates navigation data based on video navigation file.
    """

    finished = QtCore.pyqtSignal()
    nav_path = QtCore.pyqtSignal(str)

    def __init__(self, video_df, dir_out, sampling_time, video_nav_path):
        super(ExtractImageThread, self).__init__()
        self.running = True
        self.video_df = video_df
        self.dir_out = dir_out
        self.sampling_time = sampling_time
        self.img_df = None
        self.video_nav_path = video_nav_path

    def run(self):
        for index, row in self.video_df.iterrows():
            new_img_df = self.extract_images(row['path'], self.dir_out, row['datetime_start'], self.sampling_time)
            self.img_df = new_img_df if self.img_df is None else pd.concat(self.img_df, new_img_df)

        nav_file = self.generate_navigation(self.video_nav_path)
        nav_path = os.path.join(self.dir_out, "extracted_navigation.csv")
        nav_file.to_csv(nav_path, index=False)

        self.nav_path.emit(nav_path)
        self.finished.emit()
        self.running = False

    def extract_images(self, video_path, dir_out, start_time, sampling_time):
        count = 0
        vidcap = cv2.VideoCapture(video_path)
        success,image = vidcap.read()
        st_ms = sampling_time*1000
        img_dic = {}
        while success:
            vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*st_ms))    # added this line
            success,image = vidcap.read()
            if success:
                frame_time = start_time + timedelta(seconds=(count*st_ms)/1000)
                filename = frame_time.strftime("%Y%m%dT%H%M%S.%fZ") + ".jpg"
                img_dic[filename] = {"frame_time": frame_time}
                cv2.imwrite(os.path.join(dir_out, filename), image)     # save frame as JPEG file
                count = count + 1
        return pd.DataFrame.from_dict(img_dic, orient='index')

    def generate_navigation(self, video_navigation_path):
        video_navigation = pd.read_csv(video_navigation_path, parse_dates=[['date', 'heure']])
        self.img_df['name'] = self.img_df.index
        merged = pd.merge(video_navigation, self.img_df, right_on="frame_time", left_on="date_heure")
        merged = merged.drop('frame_time', axis = 1)
        #merged.interpolate('time')
        return merged

