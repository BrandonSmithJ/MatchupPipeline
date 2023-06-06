#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 11:14:06 2022

@author: ryanoshea
"""
import numpy as np
from scipy.spatial import KDTree

_triangulations = {}
def fix_projection(y, lon, lat, reproject=True, exact=True,nearestNeighborInterp=False,sparse_resample =False,lon2=None,lat2=None):
    ''' 
    Project y into its native rectangular coordinate grid 
        (e.g. diagonal image -> rectangular)
    Return the full diagonalized image, including lon/lat
        extent, with reproject=False
    Must pass name parameter if inverse transformations 
    are desired.
    '''
    # extent = 0, y.shape[1], 0, y.shape[0]
    # return y, extent, (lon, lat)
    from scipy.interpolate import griddata, LinearNDInterpolator, NearestNDInterpolator
    from scipy.spatial import ConvexHull, Delaunay
    import skimage.transform as st
    fill_value_float = -32767.0
    shape = lon.shape 
    dtype = y.dtype    
    y     = np.ma.masked_invalid(y.astype(np.float32)).filled(fill_value=np.nan)

    if len(y.shape) == 3: y = y.reshape((-1, y.shape[-1]))
    else:                 y = y.ravel()

    # Get lon/lat min/max values
    lonlat   = np.array(np.vstack([lon.ravel(), lat.ravel()]))
    min_val, min_val2 = np.partition(lonlat, 1).T[:2]
    max_val2, max_val = np.partition(lonlat,-2).T[-2:]
    extent   = np.vstack((min_val, max_val)).T.ravel()
    tri_key  = tuple(extent)
    step_val = np.mean([min_val2 - min_val, max_val - max_val2], 0)

    # Create a Delaunay triangulation for the original grid, if it doesn't already exist
    if tri_key not in _triangulations and not sparse_resample:
        print('Calculating Delaunay triangulation...')
        _triangulations[tri_key] = Delaunay(lonlat.T)

    # Apply a linear interpolation over the values for the new grid
    if lon2 is None and lat2 is None:
        if exact or (max_val[0]-min_val[0])/step_val[0] > 5000:
            # size = [min(1000, lon.shape[1]), min(1000, lat.shape[0])] #Ryan edit to remmove size limitation....
            size = [lon.shape[1],lat.shape[0],] #
    
            lon2 = np.linspace(min_val[0], max_val[0], size[0])
            lat2 = np.linspace(min_val[1], max_val[1], size[1])[::-1]
        else: 
            lon2 = np.arange(min_val[0], max_val[0], step_val[0])
            lat2 = np.arange(min_val[1], max_val[1], step_val[1])[::-1]
    if not sparse_resample:
        if nearestNeighborInterp:
            interp = NearestNDInterpolator(_triangulations[tri_key], np.int32(y))
            interp_fill_vals = LinearNDInterpolator(_triangulations[tri_key], y, fill_value=fill_value_float)
        else:
            interp = LinearNDInterpolator(_triangulations[tri_key], y, fill_value=fill_value_float)
    grid   = np.meshgrid(lon2, lat2)
    #Find the nearest lat lon for each original finite point
    def sparse_resampling(grid,y,lonlat,distance_upper_bound = 0.01):
        not_nan_locations = list(np.where(~np.isnan(y).any(axis=1)))[0]
        y_nan = np.empty((np.shape(grid[0])[0]*np.shape(grid[0])[1],np.shape(y[-1])[0]))
        y_nan.fill(np.nan)
        
       
        tree = KDTree(np.c_[lonlat[0].ravel(), lonlat[1].ravel()])
        value, index = tree.query(np.transpose([grid[0].ravel(), grid[1].ravel()]), k=1,distance_upper_bound=0.01)        
        y_nan[np.isfinite(value),:] = y[index[np.isfinite(value)],:]
        
        y_nan = y_nan.reshape((np.shape(grid[0])[0],np.shape(grid[0])[1],np.shape(y[-1])[0]))
        return y_nan
    lon_degrees_per_pixel = (extent[1] - extent[0])/lon.shape[1]
    lat_degrees_per_pixel = (extent[3] - extent[2])/lon.shape[0]
    average_pixel_diagonal = np.sqrt(np.square(lon_degrees_per_pixel)+np.square(lat_degrees_per_pixel))
    square = sparse_resampling(grid,y,lonlat,distance_upper_bound=average_pixel_diagonal) if sparse_resample else  interp(tuple(grid))     
    
    if nearestNeighborInterp:
        square_fill_vals = interp_fill_vals(tuple(grid))
        square=square.astype(np.int32)
        square[square_fill_vals == fill_value_float] = np.int32(-2**31)
    
    
    if not reproject:
        square = np.ma.masked_invalid(square).astype(dtype)
        mask   = square.mask if len(square.shape) == 2 else square.mask.any(-1)
        valid  = np.ix_(~np.all(mask, 1), ~np.all(mask, 0)) # remove any completely masked rows / columns
        #return square[valid], extent, (lonlat[0][valid], lonlat[1][valid]) # need to adjust extent if cutting off edges
        return square, extent, grid
        
    def minimum_bounding_rectangle(points):
        """
        https://gis.stackexchange.com/questions/22895/finding-minimum-area-rectangle-for-given-points
        https://stackoverflow.com/questions/38409156/minimal-enclosing-parallelogram-in-python
        Find the smallest bounding rectangle for a set of points.
        Returns a set of points representing the corners of the bounding box.

        :param points: an nx2 matrix of coordinates
        :rval: an nx2 matrix of coordinates
        """
        pi2 = np.pi/2.

        # get the convex hull for the points
        hull_points = points[ConvexHull(points).vertices]

        # calculate edge angles
        edges = np.zeros((len(hull_points)-1, 2))
        edges = hull_points[1:] - hull_points[:-1]

        angles = np.zeros((len(edges)))
        angles = np.arctan2(edges[:, 1], edges[:, 0])

        angles = np.abs(np.mod(angles, pi2))
        angles = np.unique(angles)

        # find rotation matrices
        rotations = np.vstack([
            np.cos(angles),
            np.cos(angles-pi2),
            np.cos(angles+pi2),
            np.cos(angles)]).T
        rotations = rotations.reshape((-1, 2, 2))

        # apply rotations to the hull
        rot_points = np.dot(rotations, hull_points.T)

        # find the bounding points
        min_x = np.nanmin(rot_points[:, 0], axis=1)
        max_x = np.nanmax(rot_points[:, 0], axis=1)
        min_y = np.nanmin(rot_points[:, 1], axis=1)
        max_y = np.nanmax(rot_points[:, 1], axis=1)

        # find the box with the best area
        areas = (max_x - min_x) * (max_y - min_y)
        best_idx = np.argmin(areas)

        # return the best box
        x1 = max_x[best_idx]
        x2 = min_x[best_idx]
        y1 = max_y[best_idx]
        y2 = min_y[best_idx]
        r  = rotations[best_idx]

        rval = np.zeros((4, 2))
        rval[0] = np.dot([x1, y2], r)
        rval[1] = np.dot([x2, y2], r)
        rval[2] = np.dot([x2, y1], r)
        rval[3] = np.dot([x1, y1], r)

        return rval

    # There's a way to use a convex hull, but would need 
    # to flatten the sides of the hull into a rectangle, 
    # in order to have an equal number of points between
    # src and dst in the projective transform
    # Can do this by iterating through hull points, and 
    # finding the nearest point on the rectangle perimeter
    #bounds   = minimum_bounding_rectangle(lonlat.T)
    #bot_left, top_left, top_right, bot_right = bounds 

    # assert(0), 'likely incorrect, currently - or at least inefficient'
    ''' 
    Need to check if we can just use the square matrix nan values to determine corners
    lonlat has now been reassigned above, so check if it's necessary to have down here
    '''
    # Get lon/lat 0-based corner values
    grid   = griddata(lonlat.T, np.ones_like(y), tuple(grid))
    lonlat = np.vstack(np.where(np.isfinite(grid.T if len(grid.shape) == 2 else grid.T[0])))
    top_left, top_right = lonlat[:, np.argmin(lonlat, 1)].T 
    bot_right, bot_left = lonlat[:, np.argmax(lonlat, 1)].T
    left_side  = np.sum(np.abs(bot_left  - top_left )**2)**0.5
    right_side = np.sum(np.abs(bot_right - top_right)**2)**0.5 
    top_side   = np.sum(np.abs(top_left  - top_right)**2)**0.5
    bot_side   = np.sum(np.abs(bot_left  - bot_right)**2)**0.5

    if exact:
        height, width = shape
    else:
        width  = int(np.max([top_side, bot_side])+1)
        height = int(np.max([left_side, right_side])+1)

    # Project the image onto a rectangle (fixing skew & rotation)
    proj = st.ProjectiveTransform()
    src  = np.array([[0,0], [0,height],[width,height],[width,0]])
    dst  = np.asarray([top_left, bot_left, bot_right, top_right])
    assert(proj.estimate(src, dst)), 'Failed to estimate warping parameters'

    lon, lat  = np.meshgrid(lon2, lat2)
    longitude = st.warp(lon, proj, output_shape=(height,width))
    latitude  = st.warp(lat, proj, output_shape=(height,width))
    projected = st.warp(square, proj, output_shape=(height,width), cval=np.nan)

    if projected.shape[0] > projected.shape[1]:
        n = 1 # 1 = 90 degrees, 2 = 180, ...
        longitude = np.rot90(longitude, n)
        latitude  = np.rot90(latitude, n)
        projected = np.rot90(projected, n)

    extent = left, right, bottom, top = 0, projected.shape[1], 0, projected.shape[0]
    return np.ma.masked_invalid(projected).astype(dtype), extent, (longitude, latitude)