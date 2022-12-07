try:   from .landsat_meta import read_meta
except: from landsat_meta import read_meta

from functools import wraps
from threading import Timer
from pathlib import Path
from typing import Iterable, Optional, Callable
from lxml import objectify

import pickle as pkl
import numpy as np
import os, subprocess, sys, socket, tempfile, inspect, logging

logger = logging.getLogger('MatchupPipeline')




def get_corners(sensor, folder):
    """ Parse out the corner values from sensor meta file """
    if sensor in ['MSI', 'S2B', 'S2A']:
        filename = Path(list(Path(folder).glob('*MTD*L1C*.xml'))[0])
        assert(filename.exists()), f'{filename} does not exist'
        
        root   = objectify.parse(filename.as_posix()).getroot()
        latlon = root.xpath('//EXT_POS_LIST')[0].text.strip().split()[:8]
        latlon = np.array(list(zip(latlon[::2], latlon[1::2]))).astype(np.float32)
        s_to_n = sorted(latlon, key=lambda v:v[0])
        sw, se = sorted(s_to_n[:2], key=lambda v:v[1])
        nw, ne = sorted(s_to_n[2:], key=lambda v:v[1])
        nrow   = ncol = 1830 # only correct if assuming 60m resolution
        return ne, nw, se, sw, nrow, ncol

    elif sensor in ['OLCI', 'S3A', 'S3B']:
        root   = objectify.parse(folder).getroot()
        latlon = root.xpath('//*[local-name()="posList"]')[0].text.strip().split()
        latlon = np.array(list(zip(latlon[::2], latlon[1::2]))).astype(np.float32)
        south  = np.min(latlon[:,0])
        north  = np.max(latlon[:,0])
        east   = np.max(latlon[:,1])
        west   = np.min(latlon[:,1])
        sw     = [south, west] #[south % 90, west % 180]
        se     = [south, east] #[south % 90, east % 180]
        nw     = [north, west] #[north % 90, west % 180]
        ne     = [north, east] #[north % 90, east % 180]
        nrow   = int(root.xpath('//*[local-name()="rows"]')[0].text.strip())
        ncol   = int(root.xpath('//*[local-name()="columns"]')[0].text.strip())
        return ne, nw, se, sw, nrow, ncol

    elif sensor in ['OLI', 'ETM', 'TM']:
        filename = list(Path(folder).glob('*_MTL.txt'))[0]
        meta = read_meta(filename.as_posix())['L1_METADATA_FILE']['PRODUCT_METADATA']
        ne   = [meta['CORNER_UR_LAT_PRODUCT'], meta['CORNER_UR_LON_PRODUCT']]
        nw   = [meta['CORNER_UL_LAT_PRODUCT'], meta['CORNER_UL_LON_PRODUCT']]
        se   = [meta['CORNER_LR_LAT_PRODUCT'], meta['CORNER_LR_LON_PRODUCT']]
        sw   = [meta['CORNER_LL_LAT_PRODUCT'], meta['CORNER_LL_LON_PRODUCT']]
        nrow = meta['REFLECTIVE_LINES']
        ncol = meta['REFLECTIVE_SAMPLES']
        return ne, nw, se, sw, nrow, ncol
    raise Exception(f'Sensor {sensor} has not been defined')


def extract_xy_from_lonlat(sensor, folder, lon, lat):
    """ 
    If the grid were a perfect rectangle, the following would work. Unfortunately,
    the grids are polygons, which means rows / columns are diagonal instead of straight 
    """
    # lats = [float(v) for v in latlon[::2]]
    # lons = [float(v) for v in latlon[1::2]]
    # lats = np.linspace(np.min(lats), np.max(lats), nrow)[::-1]
    # lons = np.linspace(np.min(lons), np.max(lons), ncol)
    # grid = np.array(np.meshgrid(lons, lats)).reshape((2, -1))
    # dist = np.sum((grid - np.array([[lon], [lat]])) ** 2, axis=0)
    # idx  = np.unravel_index(np.argmin(dist), (ncol, nrow))

    """
    Intuitively, an estimate can be made by averaging the row/col location
    between the N/S side, and the E/W side
    """
    # e_lats = np.linspace(se[0], ne[0], nrow)[::-1]
    # w_lats = np.linspace(sw[0], nw[0], nrow)[::-1]
    # n_lons = np.linspace(nw[1], ne[1], ncol)
    # s_lons = np.linspace(sw[1], se[1], ncol)
    # y = int(np.mean([((e_lats-lat)**2).argmin(), ((w_lats-lat)**2).argmin()]))
    # x = int(np.mean([((n_lons-lon)**2).argmin(), ((s_lons-lon)**2).argmin()]))

    """
    The downside of the above method is when a point lies outside the range of
    one of the sides (e.g. located in a corner) - the nearest index will be 0.
    Instead, we can determine the number of rows/columns the point is from
    each side by using the step size, while maintaining relative direction 

    For OLCI, this still is inadequate however. Best solution would likely be to 
    project the coordinates into a rectangular grid, find the row / column, then
    reproject back into the original coordinate system.
    """
    ne, nw, se, sw, nrow, ncol = get_corners(sensor, folder)

    e_lat_step = (ne[0]-se[0]) / nrow
    w_lat_step = (nw[0]-sw[0]) / nrow
    n_lon_step = (ne[1]-nw[1]) / ncol
    s_lon_step = (se[1]-sw[1]) / ncol

    # Mod by the rows/cols to maintain a positive index
    nw_cols = ((lon-nw[1]) / n_lon_step + ncol) % ncol
    ne_cols = ((lon-ne[1]) / n_lon_step + ncol) % ncol
    sw_cols = ((lon-sw[1]) / s_lon_step + ncol) % ncol
    se_cols = ((lon-se[1]) / s_lon_step + ncol) % ncol

    # Subtract from the number of rows to place (0,0) in the top-left
    nw_rows = nrow - ((lat-nw[0]) / w_lat_step + nrow) % nrow
    ne_rows = nrow - ((lat-ne[0]) / e_lat_step + nrow) % nrow
    sw_rows = nrow - ((lat-sw[0]) / w_lat_step + nrow) % nrow
    se_rows = nrow - ((lat-se[0]) / e_lat_step + nrow) % nrow

    x = int(np.mean([nw_cols, ne_cols, sw_cols, se_cols]))
    y = int(np.mean([nw_rows, ne_rows, sw_rows, se_rows]))
    return x, y, nrow, ncol



def force_ipv4() -> None:
    """
    Force network connections to use IPv4 instead of IPv6
    """
    old_getaddrinfo = socket.getaddrinfo
    if old_getaddrinfo.__name__ == 'new_getaddrinfo': 
        return
    def new_getaddrinfo(*args, **kwargs):
        responses = old_getaddrinfo(*args, **kwargs)
        return [response
                for response in responses
                if response[0] == socket.AF_INET]
    new_getaddrinfo.__name__ = 'new_getaddrinfo'
    socket.getaddrinfo = new_getaddrinfo



def execute_cmd(
    cmd     : Iterable[str],         # Command to execute in the form of a list of arguments
    env     : Optional[dict] = None, # Environment variables to set in the execution process
    cwd     : Optional[str]  = None, # Directory in which to execute the command
    timeout : float          = 20,   # Number of minutes before the process times out and exits
    raise_e : bool           = True, # Raise any exceptions from the process rather than returning process details
):
    """
    Execute the given command in an isolated subprocess, raising any errors that occur
    """
    def kill_process(process, cmd):
        """ Raise a TimeoutError when the process is killed due to timeout """
        getattr(process, 'kill', getattr(process, 'terminate', lambda: None))()
        raise TimeoutError(f'Took long to execute command "{cmd}"')

    process  = subprocess.Popen(cmd, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timeout  = Timer(60 * timeout, kill_process, [process, cmd])
    
    # Start the timeout thread and wait for process to complete (or timeout)
    try:
        timeout.start()
        out, err = process.communicate()
    finally: timeout.cancel()

    err = err.decode('utf-8').replace('\n\n\n', '\n')
    out = out.decode('utf-8').replace('\n\n\n', '\n')

    # Raise an exception if the process did not complete sucessfully
    if raise_e and process.returncode != 0:
        sep = ''.join(['-'] * 20)
        msg = f'Error executing command "{cmd}":\n'
        msg+= '\n'.join([sep, 'Subprocess Output:', out, ''])
        msg+= '\n'.join([sep, 'Subprocess Error:',  err, ''])
        logger.error(msg)
        raise Exception(err)

    # Return the process code and out/err strings
    return process.returncode, out, err



def subprocess_wrapper(function: Callable) -> Callable:
    """ 
    Isolate a function in a separate process to ensure all resources are released after completion.
    Could be simpler by using Process, and not having to pass around pickle files - but Process doesn't
    have an isolated stdout, which means any subprocesses called by the function (e.g. wget from polymer)
    still have stdout / stderr leakage, which can't be caught.

    A timeout value can be passed to the decorated function, which controls the number of minutes 
    before the process times out and exits, and a TimeoutError is raised.
    """
    curr_file = Path(inspect.getframeinfo(inspect.stack()[1][0]).filename).resolve()

    @wraps(function)
    def wrapper(*args, timeout=20, _subprocess_pass_through=False, **kwargs):
        if _subprocess_pass_through:
            return function(*args, **kwargs)

        env = dict(os.environ)
        # env['PYTHONPATH'] = ':'.join([curr_file.parent.as_posix(), curr_file.parent.parent.parent.as_posix()])
        env['PYTHONPATH'] = curr_file.parent.as_posix()

        with tempfile.NamedTemporaryFile(suffix=str(os.getpid()), mode='r+b', delete=False) as tmpfile:
            tmppath = Path(tmpfile.name).as_posix() # Windows has unicode issues if passing raw name

            # Dump args/kwargs to a temporary pickle file
            pkl.dump([args, kwargs], tmpfile)
            tmpfile.flush()
            tmpfile.close()
        
            # Execute a command which loads the function args/kwargs from the pickle file,
            # and runs the function in a separate python environment
            execute_cmd([sys.executable, '-c', 
                f'from {curr_file.stem} import *;'
                f'import pickle as pkl;'
                f'argfile = open("{tmppath}", "rb");'
                f'args, kwargs = pkl.load(argfile);'
                f'argfile.close();'
                f'ret = {function.__name__}(*args, _subprocess_pass_through=True, **kwargs);'
                f'argfile = open("{tmppath}", "wb");'
                f'pkl.dump(["ret_val", ret], argfile);'
                f'argfile.close();'
            ], env, timeout=timeout)

            # Load the function's return value
            with open(tmppath, 'rb') as f:
                ret = pkl.load(f)

            # Ensure it's the correct value, and return it
            assert(len(ret) == 2 and ret[0] == 'ret_val'), \
                f'Invalid return value when running {function.__name__} in subprocess: {ret}'
            return ret[1]
    return wrapper
