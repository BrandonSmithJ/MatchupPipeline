from .BaseAPI import BaseAPI


class MSI(BaseAPI): 
    """
    API interface to search and download MSI scenes

    Search can only be performed via Copernicus, whereas
    downloading can be done with both Copernicus and Google.

    Google is a much faster download, but provides no search
    functionality. Therefore, the current priority ordering is:
        search:   Copernicus
        download: Google, Copernicus

    Google download is currently disabled until rate limiting
    is put in place, due to issues with too much data being 
    downloaded on Pardees.
    """
    search_sources   = ['Copernicus'] #Planet
    download_sources = ['Google', 'Copernicus'][0:]


