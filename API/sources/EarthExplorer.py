from .BaseSource import BaseSource
from ...utils import Location, DatetimeRange, get_credentials, decompress

from datetime import datetime as dt
from functools import partial
from pathlib import Path 
from typing import Union 
from tqdm import tqdm

from landsatxplore.util import guess_dataset, is_display_id
from landsatxplore import earthexplorer
from landsatxplore.api import API
from landsatxplore.earthexplorer import (
    EarthExplorer as EE,
    EarthExplorerError,
    DATA_PRODUCTS,
    EE_LOGIN_URL, 
    EE_DOWNLOAD_URL,
)

earthexplorer.tqdm = partial(earthexplorer.tqdm, leave=False)

import requests, re, os



class EE_Fixed(EE):
    """ Multiple issues with available landsatxplore library version """
    DATA_PRODUCTS_II = {
        "landsat_tm_c1"     : "5e83d08fd9932768",
        "landsat_etm_c1"    : "5e83a507d6aaa3db",
        "landsat_8_c1"      : "5e83d0b84df8d8c2",
        "landsat_tm_c2_l1"  : "5e83d0a0f94d7d8d",
        "landsat_etm_c2_l1" : "5e83d0d08fec8a66",
        "landsat_ot_c2_l1"  : "5e81f14f92acf9ef",
        "landsat_tm_c2_l2"  : "5e83d11933473426",
        "landsat_etm_c2_l2" : "5e83d12aed0efa58",
        "landsat_ot_c2_l2"  : "5e83d14fec7cae84",
        "sentinel_2a"       : "5e83a42c6eba8084",
    }

    def login(self, username, password):
        """ Login is broken due to changed html tags """
        login_page = self.session.get(EE_LOGIN_URL)
        login_data = {
            "username" : username,
            "password" : password,
            "csrf"     : re.findall(r'name="csrf" value="(.+?)"', login_page.text)[0],
        }
        resp = self.session.post(EE_LOGIN_URL, data=login_data, allow_redirects=True)
        assert(resp.status_code == 200), [resp.text, resp.status_code, resp.reason]
        assert(self.logged_in()), 'EarthExplorer login failed'


    def download(self, identifier, output_dir, dataset=None, timeout=300, skip=False):
        """ Scenes before a certain date use different IDs """
        os.makedirs(output_dir, exist_ok=True)
        if not dataset:
            dataset = guess_dataset(identifier)
        if is_display_id(identifier):
            entity_id = self.api.get_entity_id(identifier, dataset)
        else:
            entity_id = identifier
        try:
            url = EE_DOWNLOAD_URL.format(
                data_product_id=DATA_PRODUCTS[dataset], entity_id=entity_id
            )
            filename = self._download(url, output_dir, timeout=timeout, skip=skip)
        except:
            url = EE_DOWNLOAD_URL.format(
                data_product_id=self.DATA_PRODUCTS_II[dataset], entity_id=entity_id
            )
            filename = self._download(url, output_dir, timeout=timeout, skip=skip)
        return filename

    def _download(self, url, output_dir, timeout, chunk_size=1024, skip=False):
        """Download remote file given its URL."""
        # Check availability of the requested product
        # EarthExplorer should respond with JSON
        with self.session.get(
            url, allow_redirects=False, stream=True, timeout=timeout
        ) as r:
            r.raise_for_status()
            error_msg = r.json().get("errorMessage")
            if error_msg:
                raise EarthExplorerError(error_msg)
            download_url = r.json().get("url")

        try:
            with self.session.get(
                download_url, stream=True, allow_redirects=True, timeout=timeout
            ) as r:
                file_size = int(r.headers.get("Content-Length"))
                with tqdm(
                    total=file_size, unit_scale=True, unit="B", unit_divisor=1024
                ) as pbar:
                    try:
                        local_filename = r.headers["Content-Disposition"].split("=")[-1]
                        local_filename = local_filename.replace('"', "")
                        local_filename = os.path.join(output_dir, local_filename)
                    except Exception as e:
                        message = f'Exception parsing EarthExplorer response: {e}'
                        message+= f'\nResponse headers: {r.headers}'
                        message+= f'\nResponse text:\n{r.text}'
                        raise EarthExplorerError(message)

                    if skip:
                        return local_filename
                    with open(local_filename, "wb") as f:
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                pbar.update(chunk_size)
        except requests.exceptions.Timeout:
            raise EarthExplorerError(
                "Connection timeout after {} seconds.".format(timeout)
            )
        return local_filename



class EarthExplorer(BaseSource, API):   
    """
    API to search and download from EarthExplorer

    Docs: https://m2m.cr.usgs.gov/api/docs/json/#section-overview
    """
    site_url      = 'earthexplorer.usgs.gov'
    valid_sensors = { # EarthExplorer dataset names
        'OLI' : 'landsat_ot_c2_l1', #LANDSAT_8_C1
        'ETM' : 'landsat_etm_c2_l1', # 'LANDSAT_ETM_C1',
        'TM'  : 'landsat_tm_c2_l1', #'LANDSAT_TM_C1',
    }
    valid_dates = { # Dates available for the sensors
        'OLI' : (dt(2013,  2, 11), dt.now()),
        'ETM' : (dt(1999,  4, 15), dt(2021,  9, 27)),
        'TM'  : (dt(1984,  3,  1), dt(2013,  6,  5)),
    }

    def __init__(self, *args, **kwargs):
        username, password = get_credentials(self.site_url)
        self.ee = EE_Fixed(username, password)
        BaseSource.__init__(self, *args, **kwargs)
        API.__init__(self, username, password)



    def search_scenes(self, 
        sensor          : str,            # Sensor to search scenes for 
        location        : Location,       # Object representing location to search at
        dt_range        : DatetimeRange,  # Object representing start & end datetime to search between
        **kwargs,                         # Any other keyword arguments
    ) -> dict:                            # Return a dictionary of found scenes: {scene_id: scene_detail_dict}
        """ 
        Function which searches for scenes on EarthExplorer matching the given criteria

        Additional possible keyword arguments:
            months          : List[int] # Limit results to list of specific months (1-12)
            max_cloud_cover : int       # Max cloud cover in percent (1-100)
            max_results     : int       # Max number of results returned (default: 20)
        """
        self.check_sensor(sensor)

        # Avoid unnecessary search; skip dates prior to first data for sensor
        if not self.dates_available(sensor, dt_range): return {}

        config = {
            'dataset'         : self.valid_sensors[sensor],
            'months'          : kwargs.get('months', None),
            'max_cloud_cover' : kwargs.get('max_cloud_cover', None),
            'max_results'     : kwargs.get('max_results', 20),
        }

        # ISO 8601 formatted date
        config.update( dt_range.strftime(**{
            'fmt'       : '%Y-%m-%d', 
            'dict_keys' : ['start_date', 'end_date'],
        }) )

        # Get lat/lon if it was originally given, and bbox otherwise
        config.update( location.get_point(**{
            'given'     : True, 
            'dict_keys' : ['latitude', 'longitude'],
        }) or {'bbox': location.get_bbox('wsen')} )
        return {scene['display_id']: scene for scene in self.search(**config)}



    def download_scene(self, 
        sensor        : str,              # Sensor which created this scene
        scene_id      : str,              # ID of the scene to download
        scene_details : dict,             # Any additional details about the scene
        scene_folder  : Union[Path, str], # Folder which holds all downloaded scenes
        overwrite     : bool = False,     # Whether to overwrite an already existing file
    ) -> Path:                            # Return path to the downloaded scene
        """ Downloads the requested scene from EarthExplorer """
        complete, output = self.get_output(scene_folder, scene_id, overwrite)

        if not complete:
            assert(self.ee.logged_in()), 'EarthExplorer session expired.'

            archive = self.ee.download(scene_id, output)
            decompress(Path(archive), output) 
            output.joinpath('.complete').touch()
        return output


