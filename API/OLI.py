from .BaseAPI import BaseAPI


class OLI(BaseAPI): 
    """
    API interface to search and download OLI scenes

    Search can only be performed via EarthExplorer, whereas
    downloading can be done with both EarthExplorer and Google.

    Google is a much faster download, but provides no search
    functionality. Therefore, the current priority ordering is:
        search:   EarthExplorer
        download: Google, EarthExplorer

    Google download is currently disabled until rate limiting
    is put in place, due to issues with too much data being 
    downloaded on Pardees.
    """
    search_sources   = ['EarthExplorer']
    download_sources = ['Google', 'EarthExplorer'][0:]

