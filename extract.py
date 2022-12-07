from collections import defaultdict as dd
from itertools import compress
from pathlib import Path 
from netCDF4 import Dataset
from geopy import distance
import numpy as np 

from .utils import get_latlon 


meters_distance = lambda *args: distance.distance(*args).km * 1000



def get_variables(data : Dataset) -> dict:
    """ 
    Get all variable names in the given file, as well as the number
    of values for each variable (e.g. Rrs_412, Rrs_443, etc.)

    Example return value:
        {
            Rrs      : [(Rrs_412, 412), (Rrs_443, 443), ...], 
            l2_flags : l2_flags, 
            Rw       : [(Rw412, 412), (Rw443, 443), ...],
            ...
        }

    """
    names = dd(list) 
    for var in data.variables.keys():
        if data[var].ndim < 2: continue

        # Parse variables via underscore
        if '_' in var:
            key, val = var.rsplit('_', 1) 
            try:    names[key].append( (var, int(val)) ) # e.g. Rrs_412
            except: names[var] = var                     # e.g. l2_flags

        # Attempt to separate variable into string prefix / int suffix
        # e.g. Rw412 -> (Rw, 412) 
        else:
            idx = len(var) - 1
            while idx >= 0:
                try:    int(var[idx:])
                except: break 
                idx -= 1
            
            prefix, suffix = var[:idx+1], var[idx+1:]
            if prefix and suffix: 
                names[prefix].append( (var, int(suffix)) )
            names[var] = var

    # Clean up the results
    for name, values in list(names.items()):
        if type(values) is list:

            # Default dict adds unused keys 
            if len(values) == 0:
                del names[name]

            # Sort by value if there are multiple keys
            elif len(values) > 1:
                names[name] = sorted(values, key=lambda v: v[1])

            # Demote to single key variable otherwise
            else:
                assert(len(values)), [name, values]
                del names[name]
                [[name, _]] = values
                names[name] = name
    return names 



def get_window(
        lat    : float,      # Point latitude
        lon    : float,      # Point longitude
        im_lat : np.ndarray, # Image latitude
        im_lon : np.ndarray, # Image longitude
        window : int,        # Pixel window around center point
    ) -> np.ndarray:
    """
    Return a window around the closest pixel to (lat, lon),
    where window=1 -> 3x3 window; 2 -> 5x5; 0 -> 1x1; etc.

    Can pass flattened im_lon/im_lat arrays (i.e. filtered by 
    valid pixels only) to get the closest valid points, rather
    than a strict NxN window.
    """
    shape  = im_lon.shape
    im_lon = im_lon.flatten()
    im_lat = im_lat.flatten()

    # For efficiency, we first approximate the actual distance by finding the 1000 closest
    # pixels according to a total absolute degrees error metric. The actual physical distances
    # between these 1000 points and the target coordinates are then calculated, with the 
    # smallest physical distance (in meters) image coordinate being used as the window center
    pseudo_dist = (np.abs(im_lat - lat) + np.abs(im_lon - lon)).argsort()[:1000]
    distances   = [meters_distance((ilat, ilon), (lat, lon)) for ilat, ilon in
                    zip(im_lat[pseudo_dist], im_lon[pseudo_dist])]

    # If the passed image lon/lat arrays are 2d grids, then we return a strict NxN window around the center
    if len(shape) == 2:
        min_dist = np.argmin(distances)
        w_center = np.unravel_index(pseudo_dist[min_dist], shape)
        w_slices = slice(-window, window+1)
        return np.array(w_center) + np.mgrid[w_slices, w_slices].reshape((2, -1)).T

    # Otherwise, we return the closest image points, regardless of location relative to one another 
    n_samples = (2*window + 1) ** 2
    min_dists = np.argsort(distances)[:n_samples]
    return [pseudo_dist[i] for i in min_dists]




def extract_window(
    sensor   : str,   # Satellite sensor
    inp_file : Path,  # Path to the netCDF input file 
    lat      : float, # Center latitude of window to extract 
    lon      : float, # Center longitude of window to extract 
    window   : int,   # Size of window to extract (e.g. 1 -> 3x3)
) -> dict:            # Returns dict of {all variables : window}
    """ Extract geolocated window from the given netCDF file """
    assert(inp_file.exists()), f'Input file {inp_file} does not exist'

    with Dataset(inp_file.as_posix(), 'r') as data:
        latlons  = get_latlon(data)
        shape    = latlons[0].shape
        in_bound = lambda xy: all(0 <= i < s for i,s in zip(xy, shape))

        if 'geophysical_data' in data.groups.keys():
            data = data['geophysical_data']
        datavars = get_variables(data)
        img_idxs = get_window(lat, lon, *latlons, window=window)
        w_slices = slice(-window, window+1)
        raw_idxs = np.mgrid[w_slices, w_slices].reshape((2, -1)).T

        # Filter to only valid (in bound) pixels
        raw_idxs = list( compress(raw_idxs, map(in_bound, img_idxs)) )
        img_idxs = list( compress(img_idxs, map(in_bound, img_idxs)) )
        extract  = lambda feature: [feature[tuple(i)] for i in img_idxs] 
        w_coords = list( map(extract, latlons) )

        # Location variables are stored both separately and together.
        # They are stored together for compatibility purposes, and new
        # code should use the single variable storage version.
        pt_distance = lambda loc: meters_distance(tuple(loc), (lat, lon))
        vars_bands  = {}
        vars_single = {
            'window_lat'  : w_coords[0],
            'window_lon'  : w_coords[1],
            'window_dist' : list(map(pt_distance, zip(*w_coords) )),
            'window_idxs' : list(map(str, map(tuple, raw_idxs))),
        }
        vars_double = { 'loc' : list(zip(*[vars_single[f'window_{k}'] 
                            for k in ['lat', 'lon', 'dist', 'idxs']])) }

        # Extract and store all remaining variables 
        for key, values in datavars.items():

            # Multi-key variable
            if type(values) is list:
                names, vars_bands[f'{key}_bands'] = zip(*values)
                feature_window   = [extract(data[n][:]) for n in names]
                vars_double[key] = list(zip(*feature_window))

            # Single key variable
            else:
                vars_single[key] = extract(data[key][:])
                if data[key].ndim == 3:
                    vars_single[key] = list(map(list, vars_single[key]))

    return vars_bands, vars_single, vars_double
