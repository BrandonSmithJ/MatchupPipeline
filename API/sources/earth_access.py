from .BaseSource import BaseSource
from ...utils import Location, DatetimeRange, get_credentials, decompress

from datetime import datetime as dt
from datetime import timedelta
from functools import partial
from pathlib import Path 
from typing import Union 

import os, zipfile, datetime
import requests
import numpy as np
import time
import earthaccess

def split_date_time(start,end, difference=365):
    start_dt   = dt.strptime(start,'%Y-%m-%d').date()
    end_dt     = dt.strptime(end,'%Y-%m-%d').date()
    intervals  = int(np.floor((end_dt-start_dt).days/difference))
    if intervals == 0: 
        yield start
    for i in range(intervals):
        yield (start_dt+timedelta(difference)*i).strftime('%Y-%m-%d')
    yield end_dt.strftime('%Y-%m-%d')


def get_scenes_from_query(satellite,start,end,min_cloud_cover=0,max_cloud_cover=100,max_records=2000,bbox="-21,23,-24,15",tileID=""):
        end = (dt.strptime(end,'%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        list_of_datetimes = list(split_date_time(start,end))
        w,s,e,n = bbox.split(',')
        if satellite in ['OCI','PACE']:
            short_name = "PACE_OCI_L1B_SCI"
        else:
            short_name = "EMITL1BRAD"
        w=float(w)
        s=float(s)
        e=float(e)
        n=float(n)
        print(f"Querying Earth Access for {bbox},{w},{s},{e},{n}, {start} {end}")
        
        full_dictionary = {}
        for i,start in enumerate(list_of_datetimes):
            if i+2>len(list_of_datetimes): continue
            if len(list_of_datetimes)>2: end = (dt.strptime(list_of_datetimes[i+1],'%Y-%m-%d') - timedelta(1)).strftime('%Y-%m-%d')   
            data_list=None
            while data_list is None:
                try:
                    data_list = earthaccess.search_data( short_name = short_name,temporal=(start, end),bounding_box=(w, s, e, n))
                except:
                    time.sleep(2)
                    pass

            scene_ids   = [d.data_links()[0].split('/')[-1].split('.nc')[0] for d in data_list ]
            product_ids = [d.data_links()[0] for d in data_list]
            dictionary_out = {p:s for p,s in zip(scene_ids,product_ids)}
            print("Found: ", len(dictionary_out))

        return dictionary_out 


def OCIDownloadManager(prod_ID,sceneID,destination_path,remove_uncompressed=True):
    assert type(sceneID) == str
    outdir = f"{destination_path}/{sceneID}/"

    if not os.path.isdir(outdir):
        os.makedirs(outdir,mode=0o777)

    
    url = prod_ID #f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({prod_ID})/$value"
    headers = {}
    session = requests.Session()
    #session.headers.update(headers)
    response = session.get(url, stream=True)

    print(f"Downloading {prod_ID} to {sceneID}.zip")
    
    with open(f"{destination_path}/{sceneID}.nc", "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

    assert os.path.isfile(f"{destination_path}/{sceneID}.nc")


class earth_access(BaseSource):
    """
    API to search and download from

    """
    site_url      = 'scihub.copernicus.eu'
    valid_dates   = { # Dates available for the sensors
        'OCI'   : (dt(2024, 2, 8), dt.now()),
        'EMIT'  : (dt(2022, 7, 14), dt.now()),

    }
    valid_sensors = {
        'OCI'  : 'PACE',
        'EMIT' : 'EMIT',
    }


    def __init__(self, *args, **kwargs):
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
        """
        self.check_sensor(sensor)
        
        # Avoid unnecessary search; skip dates prior to first data for sensor
        if not self.dates_available(sensor, dt_range): return {}

        scenes = get_scenes_from_query(sensor,start=dt_range.strftime(fmt="%Y-%m-%d")[0],end=dt_range.strftime(fmt="%Y-%m-%d")[1],min_cloud_cover=0,max_cloud_cover=max_cloud_cover,max_records=2000,bbox=','.join([str(i) for i in location.get_bbox(order='wsen')]),tileID=tileID)
        

        return scenes 



    def download_scene(self, 
        sensor        : str,              # Sensor which created this scene
        scene_id      : str,              # ID of the scene to download
        scene_details : dict,             # Any additional details about the scene
        scene_folder  : Union[Path, str], # Folder which holds all downloaded scenes
        overwrite     : bool = False,     # Whether to overwrite an already existing file
    ) -> Path:                            # Return path to the downloaded scene
        """ Download the requested scene from  """
        complete, output = self.get_output(scene_folder, scene_id, overwrite)
        import datetime
        if not complete:
            if sensor == "EMIT":
                scene_id_OBS      = scene_id.replace('_RAD_',"_OBS_")
                scene_details_OBS = '/'.join(str(scene_details).split('/')[:-1]) + '/' + scene_id_OBS + '.nc'
                OCIDownloadManager(scene_details_OBS,scene_id_OBS,output,remove_uncompressed=False)

            OCIDownloadManager(scene_details,scene_id,output,remove_uncompressed=False)
            #archive = output.joinpath(f'{scene_id}.zip')
            output.joinpath('.complete').touch()
        return output.joinpath(f'{scene_id}.nc') 
