from .BaseAPI import BaseAPI


class EMIT(BaseAPI): 
    """
    API interface to search and download EMIT scenes

    Search and download is implemented for:

    Current priority ordering:
        search:   
        download: 
    """
    search_sources   = ['earth_access']
    download_sources = ['earth_access']
