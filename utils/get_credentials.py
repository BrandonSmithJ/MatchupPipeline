from .assert_contains import assert_contains

from typing import Union
from pathlib import Path 



def get_credentials(site: str) -> Union[list, str]:
    """Return the authentication credentials for the requested website.
    
    Note
    ----
    The credentials folder should be located at ../credentials.

    Parameters
    ----------
    site : str
        String url of the site to fetch credentials for;
        e.g. 'earthexplorer.usgs.gov'.

    Returns
    -------
    Union[list, str]
        Returns either a string (if there is only a single
        line in the credentials file), or a list of all 
        lines in the file. 

    Raises
    ------
    InvalidSelectionError
        Raises exception if an invalid site is requested.

    """
    from subprocess import getoutput

    username = getoutput('whoami')
    auth_folder = Path(__file__).parent.parent.joinpath('credentials').joinpath(username)
    #auth_folder = Path('/tis/m2cross/scratch/f002/roshea/Simultaneous/workspace/pipeline/authentication/')
    valid_sites = [
        'earthexplorer.usgs.gov',         # Username + Password
        'scihub.copernicus.eu',           # Username + Password
        'urs.earthdata.nasa.gov',         # Username + Password
        'ladsweb.modaps.eosdis.nasa.gov', # API Key
    ]
    assert_contains(valid_sites, site=site)
    path=Path(auth_folder).joinpath(f'{site}.txt')
    print("Loading authentication files from path:",path)
    with path.open() as f:
        data = [line.strip() for line in f.readlines() if line.strip()]
    return data if len(data) > 1 else data[0]
