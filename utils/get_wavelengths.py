import numpy as np
import netCDF4


def get_wavelengths(data: netCDF4.Dataset, key: str) -> np.ndarray:
    """Attempt to extract the wavelengths for a given key from a netCDF.

    Parameters
    ----------
    data : netCDF4.Dataset
        netCDF data object which should be examined.
    key     : str
        String that should be searched for; e.g. 'Rrs_'.

    Returns
    -------
    np.ndarray
        Numpy array containing the wavelengths for `key`
        if they are found, and an empty array otherwise.

    """
    wvl = []
    for v in data.variables.keys():
        if key in v:
            try:    wvl.append(int(v.replace(key, '')))
            except: pass
    return np.array(wvl) 