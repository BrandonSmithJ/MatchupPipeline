from .BaseSource import BaseSource
from ...utils import Location, DatetimeRange, get_credentials, decompress

from datetime import datetime as dt
from datetime import timedelta
from functools import partial
from pathlib import Path 
from typing import Union 

import os, zipfile
from sentinelsat import SentinelAPI
import requests
import numpy as np

def split_date_time(start,end, difference=365):
    start_dt   = dt.strptime(start,'%Y-%m-%d').date()
    end_dt     = dt.strptime(end,'%Y-%m-%d').date()
    intervals  = int(np.floor((end_dt-start_dt).days/difference))
    if intervals == 0: 
        yield start
    for i in range(intervals):
        yield (start_dt+timedelta(difference)*i).strftime('%Y-%m-%d')
    yield end_dt.strftime('%Y-%m-%d')


#https://documentation.dataspace.copernicus.eu/APIs/OpenSearch.html
#XML description: https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/describe.xml
def get_scenes_from_query(satellite,start,end,min_cloud_cover=0,max_cloud_cover=100,max_records=2000,bbox="-21,23,-24,15",tileID=""):
        if int(start[0:4])<2018: start = '2018-01-01'
        
        list_of_datetimes = list(split_date_time(start,end))
        print(f"Querying Copernicus for {bbox} {start} {end}")
        
        #bbox     = location.get_footprint(as_string=True),
        #dt_range = dt_range.ensure_unique().strftime(),
        full_dictionary = {}
        for i,start in enumerate(list_of_datetimes):
            if i+2>len(list_of_datetimes): continue
            if len(list_of_datetimes)>2: end = (dt.strptime(list_of_datetimes[i+1],'%Y-%m-%d') - timedelta(1)).strftime('%Y-%m-%d')    #list_of_datetimes[i+1]
            alternate_url = "https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json?"+\
            f"cloudCover=%5B{min_cloud_cover},{max_cloud_cover}%5D&"+\
            f"startDate={start}T00:00:00Z&completionDate={end}T23:59:59Z"+\
            f"&maxRecords={max_records}&"+\
            f"processingLevel=S2MSI1C&"+\
            f"processorVersion=05.00&"+\
            f"box={bbox}"

            if tileID != "": alternate_url = alternate_url + f"&tileId={tileID}"

            url = alternate_url
            #print(url)
            response = requests.get(url)
            data_list = response.json()['features'] 
        
            scene_ids = [d['properties']['title'].replace('.SAFE','') for d in data_list if '.SAFE' in d['properties']['title']]
            product_ids = [d['id'] for d in data_list if '.SAFE' in d['properties']['title']]
            dictionary_out = {p:s for p,s in zip(scene_ids,product_ids)}
            print("Found: ", len(dictionary_out))

            full_dictionary.update(dictionary_out)
            #list_of_dictionaries.append(dictionary_out)
        return full_dictionary #{**i for i in list_of_dictionaries}


def get_access_token(username: str, password: str) -> str:
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    try:
        r = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
        )
        r.raise_for_status()
    except:
        raise Exception(
            f"Access token creation failed. Reponse from the server was: {r.json()}"
        )
    return r.json()["access_token"]


def sentinelDownloadManager(prod_ID,sceneID,destination_path,remove_uncompressed=True):
    assert type(sceneID) == str
    downdir = "down/"
    outdir = f"{destination_path}/{sceneID}/"

    if not os.path.isdir(outdir):
        os.makedirs(outdir,mode=0o777)
    username, password = get_credentials('scihub.copernicus.eu') 
    access_token = get_access_token(username, password)
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({prod_ID})/$value"

    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url, headers=headers, stream=True)

    print(f"Downloading {prod_ID} to {sceneID}.zip")

    with open(f"{destination_path}/{sceneID}.zip", "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

    assert os.path.isfile(f"{destination_path}/{sceneID}.zip")

    #Unzip the scene
    print(f"Uncompressing original .zip for {sceneID}")
    with zipfile.ZipFile(f"{destination_path}/{sceneID}.zip") as zf:
        zf.extractall(outdir)


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
        #self.username = username
        #self.password = password
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

        scenes = get_scenes_from_query("MSI",start=dt_range.strftime(fmt="%Y-%m-%d")[0],end=dt_range.strftime(fmt="%Y-%m-%d")[1],min_cloud_cover=0,max_cloud_cover=max_cloud_cover,max_records=2000,bbox=','.join([str(i) for i in location.get_bbox(order='wsen')]),tileID=tileID)
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
        #if type(scene_details) == str:
        #    scene_details = eval(scene_details)
        if not complete:
            #self.api.download_all(products = [scene_details['uuid']],directory_path = output, checksum = False )
            sentinelDownloadManager(scene_details,scene_id,output,remove_uncompressed=False)

            archive = output.joinpath(f'{scene_id}.zip')
            decompress(archive, output)
            output.joinpath('.complete').touch()
        return output 
        


    def filename(self, 
        scene_id : str,  # Filename the given scene ID should have once downloaded
    ) -> str:           
        return f'{pid}/{pid}.SAFE'
