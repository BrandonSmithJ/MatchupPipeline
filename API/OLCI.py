from .BaseAPI import BaseAPI


class OLCI(BaseAPI): 
    """
    API interface to search and download OLCI scenes

    Search and download is implemented for three Sources:
        - Copernicus: slow, but reliable
        - OBPG: relatively fast, but mildly hostile towards automated downloading
        - LAADS: uncertain

    Current priority ordering:
        search:   Copernicus, OBPG, LAADS
        download: OBPG, LAADS, Copernicus
    """
    search_sources   = ['Copernicus', 'OBPG', 'LAADS']
    download_sources = ['OBPG', 'LAADS', 'Copernicus']
