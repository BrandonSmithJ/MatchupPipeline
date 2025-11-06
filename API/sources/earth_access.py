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


def get_scenes_from_query(satellite,start,end,min_cloud_cover=0,max_cloud_cover=100,max_records=10000,bbox="-21,23,-24,15",tileID=""):
        end = (dt.strptime(end,'%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        list_of_datetimes = list(split_date_time(start,end))
        w,s,e,n = bbox.split(',')
        if satellite in ['OCI','PACE']:
            short_names = ["PACE_OCI_L1B_SCI"]

        if satellite in ['EMIT']:
            short_names = ["EMITL1BRAD"]
  
        if satellite in ['MOD']:
            short_names = ["MODISA_L1","MODIST_L1"] #MODIST_L1 #MODIST_L1_GEO #MODISA_L1_GEO
        
        if satellite in ['VI']:
            short_names = ["VIIRSN_L1","VIIRSJ1_L1"]

        if satellite in ['OLCI']:
            short_names = ["OLCIS3A_L1_EFR","OLCIS3B_L1_EFR"]

        w=float(w)
        s=float(s)
        e=float(e)
        n=float(n)
        print(f"Querying Earth Access for {satellite} imagery of {bbox},{w},{s},{e},{n}, from {start} to {end} within {short_names}")
        
        full_dictionary = {}
        for short_name in short_names:
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
                dictionary_out = {p:s for p,s in zip(scene_ids,product_ids) if 'V3' in p or satellite not in ['OCI','PACE']}
                print("Found: ", len(dictionary_out), 'for: ',start,end)
                full_dictionary.update(dictionary_out)
        return full_dictionary 


def OCIDownloadManager(prod_ID,sceneID,destination_path,remove_uncompressed=True,suffix=''):
    assert type(sceneID) == str
    #outdir = f"{destination_path}/{sceneID}/"

    #if not os.path.isdir(outdir):
    #    os.makedirs(outdir,mode=0o777)

    
    url = prod_ID #f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({prod_ID})/$value"
    headers = {}
    session = requests.Session()
    #session.headers.update(headers)
    response = session.get(url, stream=True)

    print(f"Downloading {prod_ID} to {sceneID}{suffix}")
    
    with open(f"{destination_path}/{sceneID}{suffix}", "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

    assert os.path.isfile(f"{destination_path}/{sceneID}{suffix}")
    return f"{destination_path}/{sceneID}{suffix}"

class earth_access(BaseSource):
    """
    API to search and download from

    """
    #site_url      = 'scihub.copernicus.eu'
    valid_dates   = { # Dates available for the sensors
        'OCI'     : (dt(2024, 2, 8),     dt.now()),
        'EMIT'    : (dt(2022, 7, 14),    dt.now()),
        'MOD'     : (dt(2000,  2,  1),   dt.now()),
        'MODA'    : (dt(2002,  7,  1),   dt.now()),
        'MODT'    : (dt(2000,  2,  1),   dt.now()),
        'MOD_L2'  : (dt(2002,  2,  1),   dt.now()),
        'VI'      : (dt(2011,  10,  28), dt.now()),
        'OLCI'    : (dt(2016,  2,  16),  dt.now())
        }


    valid_sensors = {
        'OCI'     : 'PACE',
        'EMIT'    : 'EMIT',
        'MOD'     : ['amod', 'tmod'], # Aqua / Terra
        'MODA'    : 'amod',
        'MODT'    : 'tmod',
        'MOD_L2'  : 'amod',
        'VI'      : ['vrsn', 'vrj1'], # Suomi-NPP / NOAA-20
        'OLCI'    : ['s3a',  's3b']

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
        from pathlib import Path
        suffixes = {'EMIT': '.nc',
                    'MOD' : '.bz2',
                    'PACE': '.nc',
                    'OCI' : '.nc',
                    'VI'  : '.nc',}
        

        suffix = suffixes[sensor]
        if not complete:
            if sensor == "EMIT":
                scene_id_OBS      = scene_id.replace('_RAD_',"_OBS_")
                scene_details_OBS = '/'.join(str(scene_details).split('/')[:-1]) + '/' + scene_id_OBS + '.nc'
                OCIDownloadManager(scene_details_OBS,scene_id_OBS,output,remove_uncompressed=False,suffix='.nc')
            
            if sensor == "VI":
                scene_id_GEO      = scene_id.replace('.L1A.','.GEO.')
                scene_details_GEO = scene_details.replace('.L1A.','.GEO.')

                OCIDownloadManager(scene_details_GEO,scene_id_GEO,output,remove_uncompressed=False,suffix='.GEO')


            if sensor == "MOD":
                from datetime import datetime,timedelta
                scene_id_GEO      = Path(scene_details.replace('cmr/','')).parent


                aqua_or_terra     = 'AQUA_MODIS.' if scene_id.split('.')[0][0] == 'A' else 'AQUA_TERRA.'
                format_string     = "%Y%j%H%M%S"
                datetime_object   = datetime.strptime(scene_id.split('.')[0][1:], format_string)
                formatted_scene_id_GEO_0 = datetime_object.strftime("%Y%m%dT%H%M%S.GEO.hdf")
                formatted_scene_id_GEO_1 = (datetime_object+timedelta(seconds=1)).strftime("%Y%m%dT%H%M%S.GEO.hdf")
                scene_id_GEO_0           = scene_id_GEO.joinpath(aqua_or_terra + formatted_scene_id_GEO_0)
                scene_id_GEO_1           = scene_id_GEO.joinpath(aqua_or_terra + formatted_scene_id_GEO_1)
                if 'https://' not in str(scene_id_GEO_0): scene_id_GEO_0 = str(scene_id_GEO_0).replace('https:/','https://')
                if 'https://' not in str(scene_id_GEO_1): scene_id_GEO_1 = str(scene_id_GEO_1).replace('https:/','https://')
                
                archive_0 = OCIDownloadManager(str(scene_id_GEO_0),formatted_scene_id_GEO_0,output,remove_uncompressed=False)
                archive_1 = OCIDownloadManager(str(scene_id_GEO_1),formatted_scene_id_GEO_1,output,remove_uncompressed=False)
                #rename the output to match that of the downloaded scene
                arc_0_size = Path(archive_0).stat().st_size
                arc_1_size = Path(archive_1).stat().st_size
                if arc_1_size > arc_0_size:
                    os.rename(archive_1,Path(archive_1).parent.joinpath(scene_id+'.GEO') )
                else:
                    os.rename(archive_0,Path(archive_0).parent.joinpath(scene_id+'.GEO') )

            archive = OCIDownloadManager(scene_details,scene_id,output,remove_uncompressed=False,suffix=suffix)
            if sensor in ['MOD', 'OLCI', 'HICO', 'MERIS']:
                decompress(Path(archive), output)
   #archive = output.joinpath(f'{scene_id}.zip')
            output.joinpath('.complete').touch()
        return output.joinpath(f'{scene_id}.nc') 
