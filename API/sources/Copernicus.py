from .BaseSource import BaseSource
from ...utils import Location, DatetimeRange, get_credentials, decompress

from datetime import datetime as dt
from functools import partial
from pathlib import Path 
from typing import Union 

from sentinelsat import SentinelAPI



class Copernicus(BaseSource, SentinelAPI):
    """
    API to search and download from Copernicus

    Docs: https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/FullTextSearch?redirectedfrom=SciHubUserGuide.3FullTextSearch
    """
    site_url      = 'scihub.copernicus.eu'
    valid_dates   = { # Dates available for the sensors
        'MSI'  : (dt(2015, 6, 23), dt.now()),
        'OLCI' : (dt(2016, 2, 16), dt.now()),
    }
    valid_sensors = {
        'MSI'  : 'Sentinel-2',
        'OLCI' : 'Sentinel-3',
    }


    def __init__(self, *args, **kwargs):
        username, password = get_credentials(self.site_url)
        SentinelAPI.__init__(self, username, password)
        BaseSource.__init__(self, *args, **kwargs)


    def _tqdm(self, **kwargs):
        """ Ensure progress bars created by sentinelsat are removed """
        kwargs.update({'leave':False})
        return super()._tqdm(**kwargs)


    def search_scenes(self, 
        sensor          : str,            # Sensor to search scenes for 
        location        : Location,       # Object representing location to search at
        dt_range        : DatetimeRange,  # Object representing start & end datetime to search between
        limit           : int = 20,       # Max number of results returned
        max_cloud_cover : int = 100,      # Max cloud cover in percent (1-100)
        **kwargs,                         # Any other keyword arguments
    ) -> dict:                            # Return a dictionary of found scenes: {scene_id: scene_detail_dict}
        """ 
        Function which searches for scenes on Copernicus matching the given criteria

        See https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/3FullTextSearch 
        for a full list of additional keyword arguments that can be used
        """
        self.check_sensor(sensor)
        
        # Avoid unnecessary search; skip dates prior to first data for sensor
        if not self.dates_available(sensor, dt_range): return {}

        config = {
            'platformname' : self.valid_sensors[sensor],
            'date'         : dt_range.ensure_unique().strftime(),
            'area'         : location.get_footprint(as_string=True),
            'limit'        : limit,
        }

        # For whatever reason, Copernicus decided not to actually use WKT for
        # point representations...so we need to fix our area search string
        # if 'POINT' in config['area']:
        #     config['area'] = '{lat:.5f}, {lon:.5f}'.format(
        #         **location.get_point(dict_keys=['lat', 'lon']) )

        # Sensor-specific kwargs
        config.update({
            'productlevel' : 'L1',
            'producttype'  : 'OL_1_EFR___',
        } if sensor == 'OLCI' else {
            'processinglevel'      : 'Level-1C',
            'cloudcoverpercentage' : (0, max_cloud_cover),
        })

        # Manually passed kwargs
        config.update(kwargs)

        return { scene['title']: scene 
                 for _, scene in self.query(**config).items() }



    def download_scene(self, 
        sensor        : str,              # Sensor which created this scene
        scene_id      : str,              # ID of the scene to download
        scene_details : dict,             # Any additional details about the scene
        scene_folder  : Union[Path, str], # Folder which holds all downloaded scenes
        overwrite     : bool = False,     # Whether to overwrite an already existing file
    ) -> Path:                            # Return path to the downloaded scene
        """ Download the requested scene from Copernicus """
        complete, output = self.get_output(scene_folder, scene_id, overwrite)

        if not complete:
            self.download(**{
                'id'              : scene_id,#scene_details['uuid'], 
                'directory_path'  : output,
                'checksum'        : False,
            })

            archive = output.joinpath(f'{scene_id}.zip')
            decompress(archive, output)
            output.joinpath('.complete').touch()
        return output 
        


    def filename(self, 
        scene_id : str,  # Filename the given scene ID should have once downloaded
    ) -> str:           
        return f'{pid}/{pid}.SAFE'