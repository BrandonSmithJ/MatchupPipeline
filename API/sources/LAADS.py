from .BaseSource import BaseSource
from ...utils import Location, DatetimeRange, get_credentials, decompress

from pathlib import Path 
from typing import Union 
from lxml import etree 


BLACKLISTED_URLS = []


class LAADS(BaseSource):
    """
    API to search and download from LAADS

    Docs: https://ladsweb.modaps.eosdis.nasa.gov/tools-and-services/#api-v2
    """
    site_url      = 'ladsweb.modaps.eosdis.nasa.gov'
    valid_sensors = { # LAADS product labels
        'MERIS' : 'EN1_MDSI_MER_FRS_1P', #level 1 B
        'OLCI'  : 'S3A_OL_1_EFR,S3B_OL_1_EFR',
    }


    def search_scenes(self, 
        sensor          : str,            # Sensor to search scenes for 
        location        : Location,       # Object representing location to search at
        dt_range        : DatetimeRange,  # Object representing start & end datetime to search between
        **kwargs,                         # Any other keyword arguments
    ) -> dict:                            # Return a dictionary of found scenes: {scene_id: scene_detail_dict}
        """
        Function which searches for scenes on LAADS matching the given criteria
        
        The LAADS APIv2 for search does not seem to work - search criteria are not 
        applied correctly, and scenes are missing from the results. Instead, APIv1
        is used to search, as well as to download. As a backup option, APIv2 does 
        appear to work for downloads.
        """
        self.check_sensor(sensor)

        config = {
            'url'     : self.site_url,
            'product' : self.valid_sensors[sensor],
        }

        # ISO 8601 formatted date
        config.update( dt_range.strftime(**{
            'fmt'       : '%Y-%m-%dT%H:%M', 
            'dict_keys' : ['start', 'end'],
        }) )

        # LAADS search requires a bbox location
        config.update( location.get_bbox('wnes', as_dict=True) )
        
        # APIv1 search requires the collection id
        config.update( {'cid': 450 if sensor == 'OLCI' else 489} )

        # APIv2 does not work
        search_url_v1 = 'https://{url}/api/v1/files/product={product}&collection={cid}&dateRanges={start}..{end}&areaOfInterest=x{w}y{n},x{e}y{s}'
        # search_url_v2 = 'https://{url}/api/v2/content/archives?products={product}&temporalRanges={start}..{end}&regions=[BBOX]W{w}%20N{n}%20E{e}%20S{s}'             

        results = self.session.get(search_url_v1.format(**config), timeout=60)
        return {Path(v['name']).stem: v for v in dict(results.json()).values()}



    def download_scene(self, 
        sensor        : str,              # Sensor which created this scene
        scene_id      : str,              # ID of the scene to download
        scene_details : dict,             # Any additional details about the scene
        scene_folder  : Union[Path, str], # Folder which holds all downloaded scenes
        overwrite     : bool = False,     # Whether to overwrite an already existing file
    ) -> Path:                            # Return path to the downloaded scene
        """ Function which downloads the requested scene """
        complete, output = self.get_output(scene_folder, scene_id, overwrite)

        if not complete:    
            archive = output.joinpath(scene_details['name'])
            auth    = f'Bearer {get_credentials(self.site_url)}'
            url_v1  = f'https://{self.site_url}{scene_details["fileURL"]}'
            url_v2  = f'https://{self.site_url}/api/v2/content/archives/{scene_details["name"]}'
            dl_url  = url_v2 if url_v1 in BLACKLISTED_URLS else url_v1

            if dl_url not in BLACKLISTED_URLS:
                self.stream_download(dl_url, archive, **{
                    'stream'          : True,
                    'allow_redirects' : True,
                    'timeout'         : 60 * 15,
                    'headers'         : {
                        'Authorization' : auth,
                    },
                })

                try: 
                    decompress(archive, output)
                    output.joinpath('.complete').touch()

                # Track failed urls with a blacklist
                except Exception as e: 
                    BLACKLISTED_URLS.append(dl_url)
                    raise e
        return output

