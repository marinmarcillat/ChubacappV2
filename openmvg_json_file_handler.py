import json
import numpy as np
import os

from camera import Camera
from utility import (
    check_radial_distortion,
)


class OpenMVGJSONFileHandler:
    """Class to read and write :code:`OpenMVG` files."""

    @staticmethod
    def _get_default_polymorphic_name(intrinsics):
        default_polymorpihc_name = None
        for _, intrinsic in intrinsics.items():
            if intrinsic["key"] == 0:
                default_polymorpihc_name = intrinsic["value"][
                    "polymorphic_name"
                ]
                break
        assert default_polymorpihc_name is not None
        return default_polymorpihc_name

    @staticmethod
    def _parse_cameras(
        json_data,
        image_fp_type,
        suppress_distortion_warnings,
        op=None,
    ):

        # For each input image there exists an entry in "views". In contrast,
        # "extrinsics" contains only information of registered images (i.e.
        # reconstructed camera poses) and may contain only information for a
        # subset of images.
        views = {item["key"]: item for item in json_data["views"]}
        intrinsics = {item["key"]: item for item in json_data["intrinsics"]}
        extrinsics = {item["key"]: item for item in json_data["extrinsics"]}

        # Regard 3D stores the polymorhic attribute in the first intrinsic
        default_polymorphic_name = (
            OpenMVGJSONFileHandler._get_default_polymorphic_name(intrinsics)
        )

        cams = []
        # Iterate over views and create a camera if intrinsic and extrinsic
        # parameters exist
        for id, view in views.items():  # Iterate over views

            id_view = view["key"]
            # view["value"]["ptr_wrapper"]["data"] should be equal to
            # view["value"]["ptr_wrapper"]["data"]["id_view"]
            view_data = view["value"]["ptr_wrapper"]["data"]
            id_pose = view_data["id_pose"]
            id_intrinsic = view_data["id_intrinsic"]

            # Check if the view is having corresponding Pose and Intrinsic data
            if (
                id_pose in extrinsics.keys()
                and id_intrinsic in intrinsics.keys()
            ):

                camera = Camera()

                camera.image_fp_type = image_fp_type
                camera._relative_fp = os.path.join(
                    view_data["local_path"], view_data["filename"]
                )
                camera._absolute_fp = os.path.join(
                    json_data["root_path"],
                    view_data["local_path"],
                    view_data["filename"],
                )
                camera.width = view_data["width"]
                camera.height = view_data["height"]
                id_intrinsic = view_data["id_intrinsic"]

                # Handle intrinsic params
                intrinsic_values = intrinsics[int(id_intrinsic)]["value"]
                intrinsic_data = intrinsic_values["ptr_wrapper"]["data"]

                if "polymorphic_name" in intrinsic_values:
                    polymorphic_name = intrinsic_values["polymorphic_name"]
                else:
                    polymorphic_name = default_polymorphic_name

                if polymorphic_name == "spherical":
                    camera.set_panoramic_type(
                        Camera.panoramic_type_equirectangular
                    )
                    # create some dummy values
                    focal_length = 1
                    cx = camera.width / 2
                    cy = camera.height / 2
                else:

                    focal_length = intrinsic_data["focal_length"]
                    principal_point = intrinsic_data["principal_point"]
                    cx = principal_point[0]
                    cy = principal_point[1]

                # For Radial there are several options:
                # "None", disto_k1, disto_k3
                if "disto_k3" in intrinsic_data:
                    radial_distortion = [
                        float(intrinsic_data["disto_k3"][0]),
                        float(intrinsic_data["disto_k3"][1]),
                        float(intrinsic_data["disto_k3"][2]),
                    ]
                elif "disto_k1" in intrinsic_data:
                    radial_distortion = float(intrinsic_data["disto_k1"][0])
                else:  # No radial distortion, i.e. pinhole camera model
                    radial_distortion = 0

                if not suppress_distortion_warnings:
                    check_radial_distortion(
                        radial_distortion, camera._relative_fp, op
                    )

                camera_calibration_matrix = np.array(
                    [[focal_length, 0, cx], [0, focal_length, cy], [0, 0, 1]]
                )

                camera.set_calibration(
                    camera_calibration_matrix, radial_distortion
                )
                extrinsic_params = extrinsics[id_pose]
                cam_rotation_list = extrinsic_params["value"]["rotation"]
                camera.set_rotation_with_rotation_mat(
                    np.array(cam_rotation_list, dtype=float)
                )
                camera.set_camera_center_after_rotation(
                    np.array(extrinsic_params["value"]["center"], dtype=float)
                )
                camera.view_index = id_view

                cams.append(camera)
        return cams

    @staticmethod
    def parse_openmvg_file(
        input_openMVG_file_path,
        image_fp_type,
        suppress_distortion_warnings,
        op=None,
    ):
        """Parse an :code:`OpenMVG` (:code:`.json`) file."""

        input_file = open(input_openMVG_file_path, "r")
        json_data = json.load(input_file)

        cams = OpenMVGJSONFileHandler._parse_cameras(
            json_data,
            image_fp_type,
            suppress_distortion_warnings,
            op,
        )
        return cams
