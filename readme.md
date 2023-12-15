# Chubacapp V2

## To install the environment:

- Install mamba (miniforge)
- Install cuda (cuda enabled GPU mandatory)
- Run mamba env create -f chubacappv2.yaml 


## To launch
Launch the main.py file

This is an ongoing work, 

## Creating your own environment

Required libraries:

 | Function            | External programs                   | libraries                                                                                                                                                                                                                                                                                                                                                                                                               |
|---------------------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Geomorphometrics    | CloudComPy                          | python=3.10 <br/> boost=1.74 <br/> cgal=5.4 <br/> cmake <br/> draco <br/> ffmpeg <br/> gdal=3.5 <br/> jupyterlab <br/> laszip <br/> matplotlib=3.5 <br/> mysql=8.0 <br/> numpy=1.22 <br/> opencv=4.5 <br/> openmp=8.0 <br/> pcl=1.12 <br/> pdal=2.4 <br/> psutil=5.9 <br/> pybind11 <br/> qhull=2020.2 <br/> qt=5.15.4 <br/> scipy=1.8 <br/> sphinx_rtd_theme <br/> spyder <br/> tbb <br/> tbb-devel <br/> xerces-c=3.2 |
| Reconstruction      | Colmap <br/> OpenMVS <br/> texrecon |                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Visualisation       |                                     | pyqt=5 <br/> pyvista <br/> pyvistaqt <br/> pyntcloud                                                                                                                                                                                                                                                                                                                                                                    |
| Automatic detection |                                     | onnxruntime <br/> onnx                                                                                                                                                                                                                                                                                                                                                                                                  |
| Reprojection        |                                     | trimesh <br/> fiona <br/>                                                                                                                                                                                                                                                                                                                                                                                               |
|                     |                                     |                                                                                                                                                                                                                                                                                                                                                                                                                         |