from .BaseAPI import BaseAPI


class MERIS(BaseAPI): 
    """
    API interface to search and download MERIS scenes

    Search and download is implemented for three Sources:
        - Copernicus: slow, but reliable
        - OBPG: relatively fast, but mildly hostile towards automated downloading
        - LAADS: uncertain

    However, sources other than LAADS currently do not provide the correct processing
    for MERIS scenes. 
    """
    search_sources   = ['OBPG','LAADS'] #
    download_sources = ['OBPG','LAADS'] #'LAADS'
