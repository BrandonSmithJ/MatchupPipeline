from .bitmask_parse import bitmask_parse, print_bitmask_stats
from .assert_contains import assert_contains
import numpy as np 



def bitmask_l2gen(bitmask, mask_flags='l2gen', verbose=True, debug=False):
    """Parse L2gen bitmask flags.

    Parameters
    ----------
    bitmask    : np.ndarray
        Bitmask array to parse.
    mask_flags : str
        Key for the set of flags to use when determining if a 
        sample is masked or not.
    verbose    : bool, optional
        Print statistics of the parsed bitmask.
    debug      : bool, optional
        If True, perform slower equality checks.

    Returns
    -------
    np.ndarray
        Parsed bitmask array, indicating if a sample is masked.

    Raises
    ------
    InvalidSelectionError
        Raises exception if an invalid `mask_flags` option is requested.

    References
    ----------
    .. [1] https://oceancolor.gsfc.nasa.gov/atbd/ocl2flags/

    """
    flags = [
        'atmfail',    # 00    ATMFAIL      Atmospheric correction failure   
        'land',       # 01    LAND         Pixel is over land 
        'prodwarn',   # 02    PRODWARN     One or more product algorithms generated a warning
        'higlint',    # 03    HIGLINT      Sunglint: reflectance exceeds threshold
        'hilt',       # 04    HILT         Observed radiance very high or saturated
        'hisatzen',   # 05    HISATZEN     Sensor view zenith angle exceeds threshold
        'coastz',     # 06    COASTZ       Pixel is in shallow water
        'spare1',     # 07    spare
        'straylight', # 08    STRAYLIGHT   Probable stray light contamination
        'cldice',     # 09    CLDICE       Probable cloud or ice contamination
        'coccolith',  # 10    COCCOLITH    Coccolithophores detected 
        'turbidw',    # 11    TURBIDW      Turbid water detected
        'hisolzen',   # 12    HISOLZEN     Solar zenith exceeds threshold
        'spare2',     # 13    spare
        'lowlw',      # 14    LOWLW        Very low water-leaving radiance
        'chlfail',    # 15    CHLFAIL      Chlorophyll algorithm failure
        'navwarn',    # 16    NAVWARN      Navigation quality is suspect 
        'absaer',     # 17    ABSAER       Absorbing Aerosols determined 
        'spare3',     # 18    spare
        'maxaeriter', # 19    MAXAERITER   Maximum iterations reached for NIR iteration
        'modglint',   # 20    MODGLINT     Moderate sun glint contamination
        'chlwarn',    # 21    CHLWARN      Chlorophyll out-of-bounds 
        'atmwarn',    # 22    ATMWARN      Atmospheric correction is suspect 
        'spare4',     # 23    spare 
        'seaice',     # 24    SEAICE       Probable sea ice contamination
        'navfail',    # 25    NAVFAIL      Navigation failure
        'filter',     # 26    FILTER       Pixel rejected by user-defined filter OR Insufficient data for smoothing filter 
        'spare5',     # 27    spare 
        'bowtiedel',  # 28    BOWTIEDEL    Deleted off-nadir, overlapping pixels (VIIRS only) 
        'hipol',      # 29    HIPOL        High degree of polarization determined
        'prodfail',   # 30    PRODFAIL     Failure in any product
        'spare6',     # 31    spare
    ]
    bitflag = bitmask_parse(bitmask, debug)
    labeled = {k: bitflag[..., i] for i, k in enumerate(flags)}
    masks   = {
        'L2': ['land', 'hilt', 'straylight', 'cldice'],
        'L3': ['atmfail', 'land', 'higlint', 'hilt', 'hisatzen', 'straylight', 'cldice', 
                'coccolith', 'hisolzen', 'lowlw', 'chlfail', 'navwarn', 'absaer', 'maxaeriter',
                'atmwarn', 'navfail'],
        'Custom' : ['land', 'hilt', 'straylight', 'cldice', 'atmfail', 'higlint', 'hisatzen', 'hisolzen', 'atmwarn'],
        'l2gen'  : ['cldice', 'land', 'hilt', 'straylight', 'cldice', 'atmfail', 'higlint', 'hisolzen'],# chlfail],
        'polymer': ['land', 'hilt'],
        'rhos'   : ['cldice'],
        'land'   : ['land'],
    }
    assert_contains(masks, mask=mask_flags)
    bitflag = {k: labeled[k] for k in masks[mask_flags]}

    if verbose: print_bitmask_stats(bitflag)
    return np.any(list(bitflag.values()) + [np.zeros_like(bitmask)], 0)
