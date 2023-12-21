# Chubacapp V2

## Installation procedure
- Install cuda (cuda-enabled GPU mandatory): https://developer.nvidia.com/cuda-toolkit
- Install Miniforge: https://github.com/conda-forge/miniforge/releases
- Download the latest release of ChubacappV2
- Extract to the location of your choice

### To install the environment (do once):
- Open Miniforge
- run
```
cd path to your chubacapp installation folder
mamba env create -f chubacappv2.yaml 
```



### To launch
- Open Miniforge
- Run
```
mamba activate chuv2
cd path to your chubacapp installation folder
python main.py
```




## Creating your own environment

Required libraries:

 | Function            | External programs                   | libraries                                                                                                                                                                                                                                                                                                                                                                                                               |
|---------------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Geomorphometrics    | CloudComPy                          | python=3.10 <br/> boost=1.74 <br/> cgal=5.4 <br/> cmake <br/> draco <br/> ffmpeg <br/> gdal=3.5 <br/> jupyterlab <br/> laszip <br/> matplotlib=3.5 <br/> mysql=8.0 <br/> numpy=1.22 <br/> opencv=4.5 <br/> openmp=8.0 <br/> pcl=1.12 <br/> pdal=2.4 <br/> psutil=5.9 <br/> pybind11 <br/> qhull=2020.2 <br/> qt=5.15.4 <br/> scipy=1.8 <br/> sphinx_rtd_theme <br/> spyder <br/> tbb <br/> tbb-devel <br/> xerces-c=3.2 |
| Reconstruction      | Colmap <br/> OpenMVS <br/> texrecon |                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Visualisation       |                                     | pyqt=5 <br/> pyvista <br/> pyvistaqt <br/> pyntcloud  <br/> pyglet                                                                                                                                                                                                                                                                                                                                                      |
| Automatic detection |                                     | onnxruntime <br/> onnx                                                                                                                                                                                                                                                                                                                                                                                                  |
| Reprojection        |                                     | trimesh <br/> fiona <br/>                                                                                                                                                                                                                                                                                                                                                                                               |
|                     |                                     |                                                                                                                                                                                                                                                                                                                                                                                                                         |

# ! This is an ongoing work, use at your own risk !