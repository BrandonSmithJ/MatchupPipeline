from .BaseAPI import BaseAPI


class OCI(BaseAPI): 
    """
    API interface to search and download OCI scenes

    Search and download is implemented for:

    Current priority ordering:
        search:   
        download: 
    """
    search_sources   = ['earth_access']
    download_sources = ['earth_access']
