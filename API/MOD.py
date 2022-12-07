from .BaseAPI import BaseAPI


class MOD(BaseAPI): 
    '''
    API interface to search and download MODIS scenes

    Currently, the only source for MOD is OBPG.
    '''
    search_sources   = ['OBPG']
    download_sources = ['OBPG']
