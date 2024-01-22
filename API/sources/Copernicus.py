from .BaseSource import BaseSource
from ...utils import Location, DatetimeRange, get_credentials, decompress

from datetime import datetime as dt
from functools import partial
from pathlib import Path 
from typing import Union 

from sentinelsat import SentinelAPI
import requests
#https://documentation.dataspace.copernicus.eu/APIs/OpenSearch.html
#XML description: https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/describe.xml
def get_scenes_from_query(satellite,start,end,min_cloud_cover=0,max_cloud_cover=100,max_records=2000,bbox="-21,23,-24,15",tileID=""):
        if int(start[0:4])<2018: start = '2018-01-01'
        print(f"Querying Copernicus for {bbox} {start} {end}")

        #bbox     = location.get_footprint(as_string=True),
        #dt_range = dt_range.ensure_unique().strftime(),

        alternate_url = "https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json?"+\
        f"cloudCover=%5B{min_cloud_cover},{max_cloud_cover}%5D&"+\
        f"startDate={start}T00:00:00Z&completionDate={end}T23:59:59Z"+\
        f"&maxRecords={max_records}&"+\
        f"processingLevel=S2MSI1C&"+\
        f"box={bbox}"

        if tileID != "": alternate_url = alternate_url + f"&tileId={tileID}"

        url = alternate_url
        #print(url)
        response = requests.get(url)
        data_list = response.json()['features'] 
        
        scene_ids = [d['properties']['title'].replace('.SAFE','') for d in data_list if '.SAFE' in d['properties']['title']]
        product_ids = [d['id'] for d in data_list if '.SAFE' in d['properties']['title']]
        dictionary_out = {p:s for p,s in zip(scene_ids,scene_ids)}
        print("Found: ", len(dictionary_out))


        return dictionary_out



class Copernicus(BaseSource, SentinelAPI):
    """
    API to search and download from Copernicus

    Docs: https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/FullTextSearch?redirectedfrom=SciHubUserGuide.3FullTextSearch
    """
    site_url      = 'scihub.copernicus.eu'
    valid_dates   = { # Dates available for the sensors
        #'MSI'  : (dt(2015, 6, 23), dt.now()),
        'MSI'  : (dt(2018, 1,  1), dt.now()),
        'OLCI' : (dt(2016, 2, 16), dt.now()),
    }
    valid_sensors = {
        'MSI'  : 'Sentinel-2',
        'OLCI' : 'Sentinel-3',
    }


    def __init__(self, *args, **kwargs):
        #username, password = get_credentials(self.site_url)
        # self.api = SentinelAPI.__init__(self, username, password)
        #self.api  = SentinelAPI(username, password,show_progressbars =False)
        BaseSource.__init__(self, *args, **kwargs)


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
        tileID          : str = None,
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

        scenes = get_scenes_from_query("MSI",start=dt_range.strftime(fmt="%Y-%m-%d")[0],end=dt_range.strftime(fmt="%Y-%m-%d")[1],min_cloud_cover=0,max_cloud_cover=100,max_records=2000,bbox=','.join([str(i) for i in location.get_bbox(order='wsen')]),tileID=tileID)
        #config = {
        #    'platformname' : self.valid_sensors[sensor],
        #    'date'         : dt_range.ensure_unique().strftime(),
        #    'area'         : location.get_footprint(as_string=True),
        #    'limit'        : limit,
        #}


        return scenes #{ scene['title']: scene 
               # for _, scene in self.api.query(**config).items() }



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
