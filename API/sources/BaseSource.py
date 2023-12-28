from .BaseAbstract import BaseAbstract, BaseMeta
from ...utils import Location, DatetimeRange, assert_contains

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests import Session
from datetime import datetime as dt
from pathlib import Path
from typing import Union
from lxml import etree
from tqdm import tqdm 

import threading, requests


# Dictionary mapping name to the respective search/download Source object
SOURCES = {}

# Cache Source objects to prevent e.g. repeatedly authenticating
CACHED_SOURCES = {}



class Picklable(BaseAbstract):
    """ Custom definition for pickling an API object to handle sentinelsat semaphore variables """

    def __getstate__(self):
        state = {
            k : v for k, v in self.__dict__.items()
            if 'limit_semaphore' not in k
        }
        if hasattr(self, '_dl_limit_semaphore'):
            state['_dl_limit_semaphore']  = self._concurrent_dl_limit
            state['_lta_limit_semaphore'] = self._concurrent_lta_trigger_limit
        return state


    def __setstate__(self, state):
        for k, v in state.items():
            if 'limit_semaphore' in k:
                setattr(self, k, threading.BoundedSemaphore(v))
            else: setattr(self, k, v) 



class BaseSourceMeta(BaseMeta):
    def __new__(meta, name, bases, attrs):
        """ Register Source handlers """
        cls = type.__new__(meta, name, bases, attrs)
        if name != 'BaseSource': 
            SOURCES[name] = cls
        return cls


    def __call__(cls, *args, **kwargs):
        """ Return a cached object if available """
        if str(cls) not in CACHED_SOURCES:
            # Create new object instantiation
            CACHED_SOURCES[str(cls)] = super().__call__(*args, **kwargs)
        return CACHED_SOURCES[str(cls)]
      


class BaseSource(Picklable, metaclass=BaseSourceMeta):
    """Base template class for data Source object.

    Attributes
    ----------
    site_url : str
        Root URL to search / fetch for the data source, 
        defined within the class itself.
    valid_dates : dict
        Provides start/end dates for a given sensor;
        i.e. {sensor: (start_datetime, end_datetime)}
    valid_sensor : iterable
        Contains sensors that are valid for this Source.
    session  : Session
        Session object to make get / post requests.

    Notes
    -----
    - Classes inheriting from `BaseSource` should implement at
      least one of the `search` and `download` methods.
    - Classes inheriting from `BaseSource` will only ever have
      one object instantiation, as the first instantiation will
      be cached and returned for future instantiation calls.
    - The BaseSource.__init__ function will always be called 
      after the inheriting class __init__ is finished.

    """
    site_url      = None # Root URL for this source
    valid_dates   = {
                    'MSI'  : (dt(2016, 6, 16), dt.now()), #Original: dt(2015, 6, 23)
                    'S2A'  : (dt(2016, 6, 16), dt.now()), #Original: dt(2015, 6, 23)
                    'S2B'  : (dt(2017, 3,  7), dt.now()),
                    'OLCI' : (dt(2016, 2, 16), dt.now()),
                    'S3A'  : (dt(2016, 2, 16), dt.now()),
                    'S3B'  : (dt(2018, 4, 25), dt.now()),
                    'OLI'  : (dt(2013, 2, 11), dt.now()),
                    'OLI2' : (dt(2021, 9, 27), dt.now()),
                    'MOD'  : (dt(1999, 12, 1), dt.now()),
                    'VI'   : (dt(2011, 10, 28), dt.now()),
                    }   # Dict mapping sensor: valid start/end datetimes 
    valid_sensors = None # Iterable that contains sensors valid for this Source


    def __init__(self, *args, retry_kwargs: dict = {}, **kwargs):
        """Initialize Session object for this Source.
            
        Initializes a requests.Session object for get / post request 
        handling, using sensible defaults for the retry handler. 

        Alternative retry handler parameters can be passed via a 
        `retry_kwargs` dictionary. For docs and available parameters, see
        https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html
        
        Parameters
        ----------
        retry_kwargs : dict, optional
            Dictionary containing parameters for retrying failed
            requests, handling redirects, etc.
        *args                   
            Arguments for other parent classes.
        **kwargs                
            Keywords for other parent classes.

        """
        default = {
            'total'          : 10,  # Allow 10 total retries for any reason
            'backoff_factor' : 0.5, # Half second increment of retry delay 
        }
        default.update(retry_kwargs)

        retries = Retry(**default)
        adapter = HTTPAdapter(max_retries=retries)

        self.session = Session()
        self.session.mount('http://',  adapter)
        self.session.mount('https://', adapter)
        


    def search_scenes(self, 
        sensor           : str,           # Sensor to search scenes for 
        location         : Location,      # Object representing location to search at
        dt_range         : DatetimeRange, # Object representing start & end datetime to search between
        **kwargs,                         # Any other keyword arguments specific to the API
    ) -> dict:                            # Return a dictionary of found scenes: {scene_id: scene_detail_dict}
        """ Function which searches for scenes matching the given criteria """
        raise NotImplementedError(f'{self}: search_scenes not implemented')



    def download_scene(self, 
        sensor        : str,              # Sensor which created this scene
        scene_id      : str,              # ID of the scene to download
        scene_details : dict,             # Any additional details about the scene
        scene_folder  : Union[Path, str], # Folder which holds all downloaded scenes
        overwrite     : bool = False,     # Whether to overwrite an already existing file
    ) -> Path:                            # Return path to the downloaded scene
        """ Function which downloads the requested scene """
        raise NotImplementedError(f'{self}: download_scene not implemented')



    def filename(self, 
        scene_id : str,  # Filename the given scene ID should have once downloaded
    ) -> str:            # By default, it's just the scene ID itself
        return f'{scene_id}' 
        


    def check_sensor(self, sensor : str) -> None:
        """ Ensure the given sensor is valid """
        if self.valid_sensors is not None:
            assert_contains(**{
                'options' : self.valid_sensors,
                'value'   : sensor,
                'label'   : f'sensor for {self}',
                'e_type'  : NotImplementedError,
            })



    def get_output(self,
        scene_folder : Union[Path, str], # Folder which holds all downloaded scenes
        scene_id     : str,              # ID of the scene to download
        overwrite    : bool = False,     # Whether to overwrite an already existing file
    ) -> (bool, Path):                   # Returns completion flag and output path
        """ 
        Get the output path for the download, as well as a flag
        indicating if the download has already been completed
        """
        output   = Path(scene_folder).joinpath(scene_id)
        complete = (not overwrite) and output.joinpath('.complete').exists() 
        output.mkdir(parents=True, exist_ok=True)
        return complete, output
        


    def dates_available(self,
        sensor      : str,            # Sensor to check valid dates for
        dt_range    : DatetimeRange,  # Object representing datetime range of interest
    ) -> bool:                        # Returns flag indicating if dt_range is valid
        """ Check if there are any valid dates in the range of interest """
        start, end = self.valid_dates.get(sensor, (dt(1960, 1, 1), dt.now()))
        #print("Valid dates are",start,end)
        return ( (dt_range.end   > start) and
                 (dt_range.start < end  ) )



    def stream_download(self,
        url        : str,         # URL to download from
        archive    : Path,        # Path to download the file to
        chunk_size : int = 1024,  # Size of chunks to iterate
        show_pbar  : bool = True, # Show progress bar during download
        **kwargs,                 # Session kwargs
    ) -> None:
        """ Download the file located at the given URL in chunks """
        stream = self.session.get(url, **kwargs)
        
        # Some sites have an authorization redirect that isn't followed
        if 'oauth/authorize' in stream.url:
            text = stream.text
            url  = etree.HTML(text).xpath('//a[contains(@id, "redir_link")]')
            stream.close()
            assert(len(url)), f'Error getting {self} authorization:\n{text}'
            stream = self.session.get(url[0].get('href'), **kwargs)  
        if stream.headers.get('Content-Length') is not None:
            pbar_kwargs = {
                'total'        : int(stream.headers.get('Content-Length')),
                'unit_divisor' : 1024, 
                'unit_scale'   : True,
                'unit'         : 'B',
                'leave'        : False,
                'disable'      : not show_pbar,
                'ascii'        : True,
            }
            with tqdm(**pbar_kwargs) as pbar:
                with archive.open('wb') as f:
                    for chunk in stream.iter_content(chunk_size=chunk_size):
                        if chunk: 
                            f.write(chunk)
                            pbar.update(chunk_size)
        stream.close()
