from ..exceptions import FetchAPIError
from ..utils import Location, DatetimeRange
from .sources import BaseAbstract, SOURCES

from celery.utils.log import get_task_logger
from pathlib import Path
from typing import List, Union
from abc import abstractmethod 
import traceback

logger = get_task_logger('pipeline')


class BaseAPI(BaseAbstract):
    """Base template class for API objects.

    Attributes
    ----------
    search_sources     : [str]
        Names of Source classes for searching.
    download_sources   : [str]
        Names of Source classes for downloading.

    Notes
    -----
    - The `search_sources` and `download_sources` attributes
      should be set in the inheriting class definition.

    """

    @property
    @abstractmethod
    def search_sources(self):
        raise NotImplementedError(f'{self}: no search_sources available')
    


    @property
    @abstractmethod
    def download_sources(self):
        raise NotImplementedError(f'{self}: no download_sources available')



    def _try_source_method(self, method: str, *args, **kwargs):
        """Try to perform `method` for all available Sources.
        
        Parameters
        ----------
        method : str
            Method to call on the available sources (e.g. 'search').
        *args
            Arguments passed to the Source `method`. 
        **kwargs
            Keywords passed to the Source `method`.

        Raises
        ------
        FetchAPIError
            If all Sources fail for the requested `method` call.

        """
        exceptions  = []
        source_name = method.split('_')[0]
        for name in getattr(self, f'{source_name}_sources'):
            try: 
                Source = SOURCES[name]()
                return getattr(Source, method)(*args, **kwargs)
            except Exception as e: 
                message = f'{name}: {e}\n{traceback.format_exc()}\n'
                logger.warn(message)
                exceptions.append(message)

        exceptions = '\n'.join(exceptions)
        message    = f'{self} {method} failed for all Sources:\n{exceptions}'
        logger.error(message)
        raise FetchAPIError(message)



    def search_scenes(self, 
        sensor           : str,           # Sensor to search scenes for 
        location         : Location,      # Object representing location to search at
        dt_range         : DatetimeRange, # Object representing start & end datetime to search between
        **kwargs,                         # Any other keyword arguments specific to the API
    ) -> dict:                            # Return a dictionary of found scenes: {scene_id: scene_detail_dict}
        """ Function which searches for scenes matching the given criteria """
        kwargs.update({
            'sensor'   : sensor,
            'location' : location,
            'dt_range' : dt_range,
        })
        return self._try_source_method('search_scenes', **kwargs)



    def download_scene(self, 
        sensor        : str,              # Sensor which created this scene
        scene_id      : str,              # ID of the scene to download
        scene_details : dict,             # Any additional details about the scene
        scene_folder  : Union[Path, str], # Folder which holds all downloaded scenes
        overwrite     : bool = False,     # Whether to overwrite an already existing file
    ) -> Path:                            # Return path to the downloaded scene
        """ Function which downloads the requested scene """
        kwargs = {
            'sensor'        : sensor,
            'scene_id'      : scene_id,
            'scene_details' : scene_details,
            'scene_folder'  : scene_folder,
            'overwrite'     : overwrite,
        }
        return self._try_source_method('download_scene', **kwargs)
        
