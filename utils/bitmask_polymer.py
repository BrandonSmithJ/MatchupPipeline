from .bitmask_parse import bitmask_parse, print_bitmask_stats
import numpy as np 


def bitmask_polymer(
    bitmask : np.ndarray, 
    *args, 
    verbose : bool = True, 
    debug   : bool = False, 
    **kwargs,
) -> np.ndarray:
    """Parse Polymer bitmask flags.

    Parameters
    ----------
    bitmask : np.ndarray
        Bitmask array to parse.
    *args
        Discarded.
    verbose : bool, optional
        Print statistics of the parsed bitmask.
    debug   : bool, optional
        If True, perform slower equality checks.
    **kwargs
        Discarded.

    Returns
    -------
    np.ndarray
        Parsed bitmask array, indicating if a sample is masked.
        
    """
    flags = [
        'land',         # 'LAND'          : 1
        'cloud',        # 'CLOUD_BASE'    : 2
        'invalid_L1',   # 'L1_INVALID'    : 4
        'neg_bb',       # 'NEGATIVE_BB'   : 8
        'out_bounds',   # 'OUT_OF_BOUNDS' : 16
        'exception',    # 'EXCEPTION'     : 32
        'aerosol',      # 'THICK_AEROSOL' : 64
        'high_airmass', # 'HIGH_AIR_MASS' : 128
        '_unused',      # 'UNUSED'        : 256
        'other_mask',   # 'EXTERNAL_MASK' : 512
        'case2_water',  # 'CASE2'         : 1024
        'inconsistent', # 'INCONSISTENCY' : 2048
    ]

    assert((bitmask < 4096).all()), bitmask.max()
    bitmask = bitmask_parse(bitmask.astype(np.uint16), debug)
    labeled = {k: bitmask[..., i] for i, k in enumerate(flags)}
    assert(not np.any(labeled['_unused']))
    assert(not np.any(bitmask[..., len(flags):])), [bitmask[np.where(bitmask[..., len(flags):])[0]][0]]

    nan_val   = ['land', 'cloud', 'invalid_L1', 'exception', 'other_mask'] # polymer calculated nans
    suggested = nan_val + ['neg_bb', 'out_bounds', 'aerosol', 'high_airmass'] # suggested invalid mask (all < 1024)
    w_incons  = suggested + ['inconsistent'] # with inconsistency flag
    bitmask   = {k: labeled[k] for k in w_incons}

    if verbose: print_bitmask_stats(bitmask)
    return np.any(list(bitmask.values()), 0)