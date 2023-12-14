import numpy as np
import sys, os, math

print("Adding CloudCompare to sys path...")
base_path = os.getcwd()
sys.path.append(os.path.join(base_path, "reconstruction", "CloudCompare"))
import reconstruction.CloudCompare.cloudComPy as cc


def format_number(num):
    num = float(num)
    return int(num) if num % 1 == 0 else num


def calc_vrm(points_vect):
    X = 0
    Y = 0
    Z = 0
    for point in points_vect:
        X += point[0]
        Y += point[1]
        Z += point[2]
    return 1 - (np.sqrt(np.square(X) + np.square(Y) + np.square(Z)) / len(points_vect))


def calc_tri_bpi(ref, points, a0, a1, a2, a3):
    TRI = 0
    BPI = 0
    d_ref = (a0 * ref[0] + a1 * ref[1] + a2 * ref[2] - a3) / math.sqrt(a0 ** 2 + a1 ** 2 + a2 ** 2)
    for point in points:
        d = (a0 * point[0] + a1 * point[1] + a2 * point[2] - a3) / math.sqrt(
            a0 ** 2 + a1 ** 2 + a2 ** 2)  # Distance to plane
        TRI += abs(d - d_ref)
        BPI += d
    TRI = TRI / len(points)
    BPI = d_ref - (BPI / len(points))
    return TRI, BPI


def cpd_compute(cloud, octree, scale, level, vector):
    np_tri = np.empty(shape=(len(cloud), 1))
    np_bpi = np.empty(shape=(len(cloud), 1))
    np_vrm = np.empty(shape=(len(cloud), 1))
    n_cloud = cc.ccPointCloud("N_cloud")
    for i in range(len(cloud)):
        neighbours = octree.getPointsInSphericalNeighbourhood(cloud[i].tolist(), scale, level)
        points = np.empty(shape=(len(neighbours), 3))
        points_vect = np.empty(shape=(len(neighbours), 3))
        for j in range(len(neighbours)):
            points[j] = neighbours[j].point
            id = neighbours[j].pointIndex
            points_vect[j] = [vector[0][id], vector[1][id], vector[2][id]]

        n_cloud.coordsFromNPArray_copy(points)
        plane = cc.ccPlane.Fit(n_cloud)
        if plane is not None:
            a0, a1, a2, a3 = plane.getEquation()
            np_tri[i], np_bpi[i] = calc_tri_bpi(cloud[i], points, a0, a1, a2, a3)
            np_vrm[i] = calc_vrm(points_vect)
        else:
            np_tri[i], np_bpi[i], np_vrm[i] = np.nan, np.nan, np.nan
    return [np_tri, np_bpi, np_vrm]


def generate_pcd(model, scale, output_path, metrics):
    slope, aspect, roughness, tri, bpi, gm, gc, vrm = metrics
    mesh = cc.loadMesh(model)

    target_nb_neighbours = 10
    vector = None

    density = target_nb_neighbours / (np.pi * scale ** 2)
    density = max(density, 100)  # min density
    density = min(density, 3000)  # max density

    print('Model: {}, scale: {}, density: {}'.format(str(model), str(scale), str(density)))

    cloud = mesh.samplePoints(True, density)
    np_cloud = cloud.toNpArrayCopy()

    if slope or aspect:
        cc.computeNormals([cloud], model=cc.LOCAL_MODEL_TYPES.QUADRIC, defaultRadius=scale)
        cloud.convertNormalToDipDirSFs()

        dic = cloud.getScalarFieldDic()
        if vrm:
            dip = cloud.getScalarField(dic['Dip (degrees)'])
            dip_dir = cloud.getScalarField(dic['Dip direction (degrees)'])

            np_dip_dir = dip_dir.toNpArrayCopy()
            np_dip = dip.toNpArrayCopy()
            np_xy = np.sin(np_dip * (3.14 / 180))
            np_z = np.cos(np_dip * (3.14 / 180))

            np_x = np.array([np_xy[i] * np.sin(np_dip_dir[i]) for i in range(len(np_xy))])
            np_y = np.array([np_xy[i] * np.cos(np_dip_dir[i]) for i in range(len(np_xy))])

            vector = [np_x, np_y, np_z]

        dic = cloud.getScalarFieldDic()
        if slope:
            dip = cloud.getScalarField(dic['Dip (degrees)'])
            dip.setName('slope_deg_{}_m'.format(str(scale)))
        else:
            cloud.deleteScalarField(dic['Dip (degrees)'])

        dic = cloud.getScalarFieldDic()
        if aspect:
            dip_dir = cloud.getScalarField(dic['Dip direction (degrees)'])
            dip_dir.setName('aspect_deg_{}_m'.format(str(scale)))

            np_dip_dir = dip_dir.toNpArrayCopy()
            north = np.cos(np.deg2rad(np_dip_dir))
            east = np.sin(np.deg2rad(np_dip_dir))
            sf_north_id = cloud.addScalarField('northness_{}_m'.format(str(scale)))
            sf_east_id = cloud.addScalarField('eastness_{}_m'.format(str(scale)))
            sf_north = cloud.getScalarField(sf_north_id)
            sf_east = cloud.getScalarField(sf_east_id)
            sf_north.fromNpArrayCopy(north)
            sf_east.fromNpArrayCopy(east)
        else:
            cloud.deleteScalarField(dic['Dip direction (degrees)'])

    if roughness:
        cc.computeRoughness(scale, [cloud])
        dic = cloud.getScalarFieldDic()
        key = [i for i in dic.keys() if i.startswith('Roughness ')][0]
        roughness = cloud.getScalarField(dic[key])
        roughness.setName('roughness_{}_m'.format(str(scale)))

    if gc:
        cc.computeCurvature(cc.CurvatureType.GAUSSIAN_CURV, scale, [cloud])
        dic = cloud.getScalarFieldDic()
        key = [i for i in dic.keys() if i.startswith('Gaussian curvature ')][0]
        gaus_curv = cloud.getScalarField(dic[key])
        gaus_curv.setName('gaus_curv_{}_m'.format(str(scale)))

    if gm:
        cc.computeCurvature(cc.CurvatureType.MEAN_CURV, scale, [cloud])
        dic = cloud.getScalarFieldDic()
        key = [i for i in dic.keys() if i.startswith('Mean curvature ')][0]
        mean_curv = cloud.getScalarField(dic[key])
        mean_curv.setName('mean_curv_{}_m'.format(str(scale)))

    if tri or bpi or vrm:
        if tri:
            TRI_id = cloud.addScalarField('TRI_{}_m'.format(str(scale)))  # TRI
            TRI_sf = cloud.getScalarField(TRI_id)

        if bpi:
            BPI_id = cloud.addScalarField('BPI_{}_m'.format(str(scale)))  # BPI
            BPI_sf = cloud.getScalarField(BPI_id)

        if vrm:
            VRM_id = cloud.addScalarField('VRM_{}_m'.format(str(scale)))  # BPI
            VRM_sf = cloud.getScalarField(VRM_id)

        octree = cloud.computeOctree(progressCb=None, autoAddChild=True)
        level = octree.findBestLevelForAGivenNeighbourhoodSizeExtraction(scale)

        nb_threads = 4
        # np_cld_split = np.array_split(np_cloud, nb_threads)
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #    futures = [executor.submit(thread_cpd_compute, cloud_i, octree, scale, level) for cloud_i in np_cld_split]
        #    results = [f.result() for f in futures]
        np_tri, np_bpi, np_vrm = cpd_compute(np_cloud, octree, scale, level, vector)

        # np_tri = np.vstack(list(i[0] for i in results))
        # np_bpi = np.vstack(list(i[1] for i in results))

        if tri:
            TRI_sf.fromNpArrayCopy(np_tri)
        if bpi:
            BPI_sf.fromNpArrayCopy(np_bpi)
        if vrm:
            VRM_sf.fromNpArrayCopy(np_vrm)

    exp_pcd_path = os.path.join(output_path, 'cloud_metrics_{}.pcd'.format(str(scale)))
    ret = cc.SavePointCloud(cloud, exp_pcd_path)

    cc.deleteEntity(cloud)

    print('Model: {}, scale: {}, Done !'.format(str(model), str(scale)))

    return scale