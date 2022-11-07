def UTM_zone(lon: float, lat: float) -> str:
    """Calculate the UTM zone for a given coordinate.

    Parameters
    ----------
    lon : float
        Longitude.
    lat : float
        Latitude.

    Returns
    -------
    str
        String representing UTM zone for the given
        coordinate pair.

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system#UTM_zone

    """
    bandVals = "CDEFGHJKLMNPQRSTUVWXX"
    zone     = int(lon + 186.0) // 6

    if (lat >= 84.0):
        band = 'Y' if (lon < 0.0) else 'Z'
    elif (lat <= -80.0):
        band = 'A' if (lon < 0.0) else 'B'
    else:
        band = bandVals[int(lat + 80.0) // 8]
    return '{:02d}{:s}'.format(zone,band)