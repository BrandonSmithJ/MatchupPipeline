from .BaseAPI import BaseAPI


class HICO(BaseAPI): 
    """
    API interface to search and download HICO scenes
    Currently, the only source for HICO is OBPG.
    """
    search_sources   = ['OBPG']
    download_sources = ['OBPG']
