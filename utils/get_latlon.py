from ..exceptions import UnknownLatLonError
import netCDF4


def get_latlon(data : netCDF4.Dataset) -> tuple:
    """Attempt to determine the Latitude/Longitude from the netCDF object.
    
    Parameters
    ----------
    data : netCDF4.Dataset
        netCDF data object which should be examined.

    Returns
    -------
    tuple
        (Latitude, Longitude) numpy arrays from the given netCDF object.

    Raises
    ------
    UnknownLatLonError
        If the Lat/Lon cannot be determined for the given file object.

    """
    if 'navigation_data' in data.groups.keys():
        data = data['navigation_data']
    lon, lat = (('lon', 'lat') if 'lon' in data.variables.keys() else 
                ('longitude', 'latitude') if 'longitude' in  data.variables.keys()
                else ('x', 'y'))

    if lon in data.variables.keys():
        return data[lat][:], data[lon][:]
    raise UnknownLatLonError('Failed to determine netCDF lat/lon')
