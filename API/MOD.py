from .BaseAPI import BaseAPI


class MOD(BaseAPI): 
    '''
    API interface to search and download MODIS scenes

    Currently, the only source for MOD is OBPG.
    '''
    search_sources   = ['earth_access']
    download_sources = ['earth_access']
