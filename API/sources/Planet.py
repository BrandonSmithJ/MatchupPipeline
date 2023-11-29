from .BaseSource import BaseSource
from ...utils import Location, DatetimeRange, get_credentials, decompress

from datetime import datetime as dt
from functools import partial
from pathlib import Path 
from typing import Union 
import requests
from requests.auth import HTTPBasicAuth
from geojson import Polygon

class Planet(BaseSource):
    """
    API to search from Planet

    Docs: https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/FullTextSearch?redirectedfrom=SciHubUserGuide.3FullTextSearch
    """
    site_url      = 'dataspace.copernicus.eu'
    
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
        # self.api = SentinelAPI.__init__(self, username, password)
        #self.api  = SentinelAPI(username, password,show_progressbars =False)
        BaseSource.__init__(self, *args, **kwargs)
        
        self.API_KEY = 'PLAK8f10738cddb043ec8b011cb60ff7b636'
        self.item_type = "Sentinel2L1C"


    def _tqdm(self, **kwargs):
        """ Ensure progress bars created by sentinelsat are removed """
        kwargs.update({'leave':False})
        return super()._tqdm(**kwargs)


    def search_scenes(self, 
        sensor          : str,            # Sensor to search scenes for 
        location        : Location,       # Object representing location to search at
        dt_range        : DatetimeRange,  # Object representing start & end datetime to search between
        limit           : int = 2000,       # Max number of results returned
        max_cloud_cover : int = 100,      # Max cloud cover in percent (1-100)
        **kwargs,                         # Any other keyword arguments
    ) -> dict:                            # Return a dictionary of found scenes: {scene_id: scene_detail_dict}
        """ 
        Function which searches for scenes on Copernicus matching the given criteria

        See https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/3FullTextSearch 
        for a full list of additional keyword arguments that can be used
        """
        
        geojson_location = Polygon([[(location.w, location.s), (location.e, location.s), (location.e, location.n), (location.w, location.n), (location.w, location.s)]])
                
        geometry_filter = {
          "type": "GeometryFilter",
          "field_name": "geometry",
          "config": geojson_location
        }
        
        # print(dt_range.start)
        #print(dt_range.end.strftime('%Y-%m-%d')+"T00:00:00.000Z")
        #breakpoint()
        # get images acquired within a date range         <--- Date Range
        date_range_filter = {
          "type": "DateRangeFilter",
          "field_name": "acquired",
          "config": {
            "gte": dt_range.start.strftime('%Y-%m-%d')+"T00:00:00.000Z",#"2023-01-01T00:00:00.000Z",
            "lte": dt_range.end.strftime('%Y-%m-%d')+"T23:59:00.000Z" #"2023-01-10T00:00:00.000Z"
          }
        }

        # only get images which have <50% cloud coverage <--- Cloud cover
        cloud_cover_filter = {
          "type": "RangeFilter",
          "field_name": "cloud_cover",
          "config": {
            "lte": max_cloud_cover/100
          }
        }

        # combine our geo, date, cloud filters
        combined_filter = {
          "type": "AndFilter",
          "config": [geometry_filter, date_range_filter, cloud_cover_filter]
        }
        search_request = {
          "item_types": [self.item_type], 
          "filter": combined_filter
        }
        
        # fire off the POST request
        search_result = \
          requests.post(
            'https://api.planet.com/data/v1/quick-search',
            auth=HTTPBasicAuth(self.API_KEY, ''),
            json=search_request)
        
        geojson = search_result.json()

        # extract image IDs only
        properties = [feature['properties'] for feature in geojson['features']]
        product_id = [scene_info['product_id'] for scene_info in properties]
        
        # self.check_sensor(sensor)
        
        # # Avoid unnecessary search; skip dates prior to first data for sensor
        # if not self.dates_available(sensor, dt_range): return {}

        # config = {
            # 'platformname' : self.valid_sensors[sensor],
            # 'date'         : dt_range.ensure_unique().strftime(),
            # 'area'         : location.get_footprint(as_string=True),
            # 'limit'        : limit,
        # }

        # # For whatever reason, Copernicus decided not to actually use WKT for
        # # point representations...so we need to fix our area search string
        # # if 'POINT' in config['area']:
        # #     config['area'] = '{lat:.5f}, {lon:.5f}'.format(
        # #         **location.get_point(dict_keys=['lat', 'lon']) )

        # # Sensor-specific kwargs
        # config.update({
            # 'productlevel' : 'L1',
            # 'producttype'  : 'OL_1_EFR___',
            # #'cloudcoverpercentage' : (0, max_cloud_cover), # not supported for OLCI
        # } if sensor == 'OLCI' else {
            # 'processinglevel'      : 'Level-1C',
            # 'cloudcoverpercentage' : (0, max_cloud_cover),
        # })

        # # Manually passed kwargs
        # config.update(kwargs)

        # return {scene['title']: scene 
                 # for _, scene in self.api.query(**config).items() }
        
        #print(properties)

        all_propertiee = {}

        for propertiee in properties:
            if propertiee['product_id'].split('_')[1] == "MSIL1C":
                all_propertiee[propertiee['product_id']] = propertiee
    
        return all_propertiee


    def download_scene(self, 
        sensor        : str,              # Sensor which created this scene
        scene_id      : str,              # ID of the scene to download
        scene_details : dict,             # Any additional details about the scene
        scene_folder  : Union[Path, str], # Folder which holds all downloaded scenes
        overwrite     : bool = False,     # Whether to overwrite an already existing file
    ) -> Path:                            # Return path to the downloaded scene
        """ Download the requested scene from Copernicus """
        complete, output = self.get_output(scene_folder, scene_id, overwrite)
        import datetime
        if type(scene_details) == str:
            scene_details = eval(scene_details)
        if not complete:
            self.api.download_all(products = [scene_details['uuid']],directory_path = output, checksum = False )

            archive = output.joinpath(f'{scene_id}.zip')
            decompress(archive, output)
            output.joinpath('.complete').touch()
        return output 
        


    def filename(self, 
        scene_id : str,  # Filename the given scene ID should have once downloaded
    ) -> str:           
        return f'{pid}/{pid}.SAFE'
