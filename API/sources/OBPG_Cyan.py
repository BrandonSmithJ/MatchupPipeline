#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 12:47:17 2023

@author: roshea
"""

from .BaseSource import BaseSource
from ...utils import Location, DatetimeRange, get_credentials, decompress

from datetime import datetime as dt
from pathlib import Path 
from typing import Union 
from lxml import etree

import logging


logger = logging.getLogger('MatchupPipeline')

class OBPG(BaseSource):
    """ 
    API to search and download from OBPG: https://oceandata.sci.gsfc.nasa.gov/
    VIIRS, MODIS, OLCI, HICO are all able to be downloaded
            
    Docs: https://oceancolor.gsfc.nasa.gov/data/download_methods/
    Configure netrc file to resolve redirect issues.
    """
    site_url    = 'urs.earthdata.nasa.gov'
    search_url  = 'https://oceancolor.gsfc.nasa.gov'
    data_url    = 'https://oceandata.sci.gsfc.nasa.gov'
    valid_dates = { # Dates available for the sensors
        'MOD'     : (dt(2000,  2,  1), dt.now()),
        'MODA'    : (dt(2002,  7,  1), dt.now()),
        'MODT'    : (dt(2000,  2,  1), dt.now()),
        'MOD_L2'  : (dt(2002,  2,  1), dt.now()),
        'VI'      : (dt(2012,  1,  1), dt.now()),
        'OLCI'    : (dt(2016,  5,  1), dt.now()),
        'S3A'     : (dt(2016,  5,  1), dt.now()),
        'S3B'     : (dt(2018,  5,  9), dt.now()),
        'HICO'    : (dt(2009,  9, 25), dt(2014,  9, 12)),
        'MERIS'   : (dt(2002,  3,  1), dt(2012,  5,  9)),
        'SEAWIFS' : (dt(1997,  9,  1), dt(2010, 12, 11)),
        'OCTS'    : (dt(1996, 11,  1), dt(1997,  6, 30)),
        'GOCI'    : (dt(2011,  4,  1), dt(2021,  3, 31)),
        'CZCS'    : (dt(1978, 10, 30), dt(1986,  6, 22)),
        'HAWK'    : (dt(2021,  4, 16), dt.now()),
    }

    # Converting our sensor label to the ID used by OBPG
    # Also available is SeaWiFS, OCTS, GOCI, CZCS, and HawkEye
    valid_sensors = { 
        'MOD'     : ['amod', 'tmod'], # Aqua / Terra
        'MODA'    : 'amod', 
        'MODT'    : 'tmod', 
        'MOD_L2'  : 'amod', 
        'VI'      : ['vrsn', 'vrj1'], # Suomi-NPP / NOAA-20
        'OLCI'    : ['s3af', 's3bf'], # OLCI-A/B full resolution; Use [s3ar, s3br] for reduced resolution
        'S3A'     : 's3af',
        'S3B'     : 's3bf',
        'HICO'    : 'hico',
        'MERIS'   : 'mefr',           # Full resolution; Use merr for reduced resolution
        'SEAWIFS' : ['swga', 'swml'], # GAC, MLAC
        'OCTS'    : 'octs',
        'GOCI'    : 'goci',
        'CZCS'    : 'czcs',
        'HAWK'    : 'hawk',           # HawkEye (SeaHawk)
    }


    def __init__(self, *args, **kwargs):
        BaseSource.__init__(self, *args, **kwargs)
        self._login()



    def _login(self):
        username, password = get_credentials(self.site_url)
        self.session.auth  = (username, password)
            
        resp = self.session.get(f'https://{self.site_url}')
        resp = etree.HTML(resp.text)
        meta = resp.xpath('//meta[contains(@name, "csrf-token")]')
        csrf = meta[0].get('content')
        resp = self.session.post(f'https://{self.site_url}/login', 
                data={'username': username, 'password': password, 'authenticity_token': csrf})
        assert('urs_user_already_logged' in resp.cookies and resp.cookies['urs_user_already_logged'] == 'yes'), resp.text



    def search_scenes(self, 
        sensor          : str,            # Sensor to search scenes for 
        location        : Location,       # Object representing location to search at
        dt_range        : DatetimeRange,  # Object representing start & end datetime to search between
        **kwargs,                         # Any other keyword arguments
    ) -> dict:                            # Return a dictionary of found scenes: {scene_id: scene_detail_dict}
        """ Search for scenes on OBPG matching the given criteria """
        self.check_sensor(sensor)

        # Avoid unnecessary search; skip dates prior to first data for sensor
        if not self.dates_available(sensor, dt_range): return {}

        # Need to get days since epoch for start date and first day of next month
        dse  = lambda d: int(d.timestamp() / (24 * 60 * 60)) # days since epoch
        date = dt_range.start
        day  = f'{dse(date)} {dt_range.distance.days + 1}'                         # days since epoch & days in range

        mon  = dse(dt(date.year + ((date.month+1) // 12), (date.month % 12) +1, 1)) # first day of next month
        sen  = self.valid_sensors[sensor]

        # Create request payload
        config = {
            'sub' : 'level1or2list',  # request type
            'per' : 'CSTM',           # date range mode (CSTM=custom)
            'prm' : 'TC',             # parameter = True Color
            'ndx' : '0',              # result index
            'dnm' : 'D',              # day / night selection (D=day, N=night, [D,N]=both)
            'rad' : '0',              # radius around location, 0=72km
            'frc' : '0',              # % of swath which must be overlapping selected area (0=any overlap, 1=complete overlap required)
            'set' : '10',             # max results per page
            'day' : day,              # start day (in days since epoch) 
            'mon' : mon,              # month (in days since epoch) - who knows why they need both of these
            'sen' : sen,              # sensor ID
        }

        # OBPG search requires a bbox location
        config.update( location.get_bbox(as_dict=True) )

        url = f'{self.search_url}/cgi/browse.pl'
        req = self.session.post(url, data=config, timeout=60)

        if req.text.strip():
            tree = etree.HTML(req.text)
            ele  = tree.xpath('//img[contains(@src, "List.png")]')

            # If the element exists, it means there are multiple matches and we can get the results in list form
            if len(ele):
                href = ele[0].getparent().get('href')
                url  = f'{self.search_url}{href}'
                req  = self.session.get(url, timeout=60)
                return {Path(e).stem: {'instrument': sensor} for e in req.text.strip().split('\n')}

            # Otherwise, there's only a single result and we need to extract the url directly (or it's an error)
            else:
                s1  = f'contains(@href, "{self.data_url}")'
                s2  = f'contains(@href, "/getfile/")'
                url = tree.xpath(f'//a[{s1} and {s2}]')
                if not len(url):
                    logger.error(f'Possible error: response from OBPG for {sensor} @ {location} for {dt_range}, but no tiles were found; Response:\n{req.text}')
                return {Path(url[0].get('href')).stem: {'instrument': sensor}}
        return {}



    def download_scene(self, 
        sensor        : str,              # Sensor which created this scene
        scene_id      : str,              # ID of the scene to download
        scene_details : dict,             # Any additional details about the scene
        scene_folder  : Union[Path, str], # Folder which holds all downloaded scenes
        overwrite     : bool = False,     # Whether to overwrite an already existing file
    ) -> Path:                            # Return path to the downloaded scene
        """ Download the requested scene from OBPG """
        complete, output = self.get_output(scene_folder, scene_id, overwrite)

        if not complete:
            def download_suffix(suffix):
                scene_id_VIIRS = '.'.join(scene_id.split('.')[:-1])
                dl_url  = f'{self.data_url}/ob/getfile/{scene_id_VIIRS}.{suffix}' if 'VIIRS' in scene_id else f'{self.data_url}/ob/getfile/{scene_id}.{suffix}'
                suffix  = suffix.replace('GEO.nc', 'GEO').replace('L1A.nc','nc')
                archive = output.joinpath(f'{scene_id}.{suffix}')

                self.stream_download(dl_url, archive, **{
                    'stream'          : True,
                    'allow_redirects' : True,
                    'timeout'         : 60 * 25,
                })
                return archive

            suffixes =  {
                'MOD_L2' : ['L2_LAC_OC.nc'], # L2 product direct 
                'MOD'    : ['L1A_LAC.bz2'],
                'VI'     : ['GEO.nc', 'L1A.nc'],
                'OLCI'   : ['zip'],
                'HICO'   : ['L1B_ISS.bz2'],
                'MERIS'  : ['ZIP'],
            }

            for suffix in suffixes[sensor]:
                archive = download_suffix(suffix)

            if sensor in ['MOD', 'OLCI', 'HICO', 'MERIS']:
                decompress(archive, output)
            output.joinpath('.complete').touch()
        return output.joinpath(f'{scene_id}.SEN3') if sensor == 'OLCI' else output
        


if __name__ == '__main__':
    api  = OBPG()
    loc  = Location(lon=-77, lat=36.5)
    date = DatetimeRange(start='20180914', end='20180915')

    scenes = api.search_scenes('OLCI', loc, date)
    print(f'Found {len(scenes)} matching scenes')

    for sid, info in scenes.items():
        api.download_scene(sid, info, Path(__file__).parent.joinpath('Test_Outputs'), overwrite=False)
