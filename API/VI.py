from .BaseAPI import BaseAPI


class VI(BaseAPI): 
    """
    API interface to search and download VIIRS scenes
    Currently, the only source for VIIRS is OBPG.
    """
    search_sources   = ['OBPG']
    download_sources = ['OBPG']
