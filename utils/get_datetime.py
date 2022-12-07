from ..exceptions import UnknownDatetimeError

from datetime import datetime as dt
from dateutil import parser
import netCDF4



def get_datetime(data: netCDF4.Dataset) -> dt:
    """Attempt to determine the datetime associated with the netCDF object.
    
    Parameters
    ----------
    data : netCDF4.Dataset
        netCDF data object which should be examined.

    Returns
    -------
    datetime.datetime
        Datetime object associated with the given netCDF object.

    Raises
    ------
    UnknownDatetimeError
        If the datetime cannot be determined for the given file object.

    """
    def parse(v: str, fmt: str) -> dt:
        """ Parse the given string, using dateutil as a backup """
        try:    return dt.strptime(v, fmt)
        except: return parser.parse(v)

    formats = {
        'time_coverage_start' : '%Y-%m-%dT%H:%M:%S.%fZ',
        'start_time'          : '%Y-%m-%d %H:%M:%S',
        'sensing_time'        : '%Y-%m-%d %H:%M:%S',
        'isodate'             : '%Y-%m-%dT%H:%M:%S.%fZ',
    }
    for key, fmt in formats.items():
        if hasattr(data, key):
            return parse(getattr(data, key), fmt)
    raise UnknownDatetimeError(f'Failed to determine netCDF datetime')
