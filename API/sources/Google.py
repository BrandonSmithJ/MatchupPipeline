from .BaseSource import BaseSource
from ...AC.atm_utils import execute_cmd
from ...utils import Location, DatetimeRange

from pathlib import Path 
from typing import Union 


class Google(BaseSource):
    """
    API to download from Google Cloud (no search available)

    Docs: 
        https://cloud.google.com/storage/docs/public-datasets/landsat
        https://cloud.google.com/storage/docs/public-datasets/sentinel-2
    """
    valid_sensors = { # GCP bucket labels for each sensor
        'OLI' : 'landsat',
        'ETM' : 'landsat',
        'TM'  : 'landsat',
        'MSI' : 'sentinel-2',
    }

    def download_scene(self, 
        sensor        : str,              # Sensor which created this scene
        scene_id      : str,              # ID of the scene to download
        scene_details : dict,             # Any additional details about the scene
        scene_folder  : Union[Path, str], # Folder which holds all downloaded scenes
        overwrite     : bool = False,     # Whether to overwrite an already existing file
    ) -> Path:                            # Return path to the downloaded scene
        """ Downloads the requested scene from Google Cloud """
        from subprocess import getoutput
        username = getoutput('whoami')

        self.check_sensor(sensor)
        
        complete, output = self.get_output(scene_folder, scene_id, overwrite)

        if not complete:
            root_path   = Path(__file__).parent.joinpath('gsutil')
            exec_path   = root_path.joinpath('gsutil').as_posix()
            config_path = root_path.parent.parent.parent.joinpath('credentials').joinpath(username).joinpath('.boto') #Path(f'/home/{username}/.boto') #root_path.joinpath('gsutil_config').as_posix()
            search_path = 'gs://gcp-public-data-{bucket}/{search}'.format(**{
                'bucket' : self.valid_sensors[sensor],
                'search' : get_params(sensor, scene_id)['search'],
            })

            cmd = [exec_path, '-m']
            env = {'BOTO_PATH': config_path}

            # Need to verify the available file is able to be atmospherically corrected
            if sensor == 'MSI':
                code, out, err = execute_cmd(cmd + ['ls', search_path], env)
                assert(code == 0), err

                is_valid = lambda f: '_OPER_' not in Path(f).name
                filelist   = out.split('\n')
                assert(len(filelist)), f'No files found via Google with key "{search_path}"'
                assert(all(map(is_valid, filelist))), f'Google is hosting old version of tile with key "{search_path}"'

            code, out, err = execute_cmd(cmd + ['cp', '-r', search_path, output.as_posix()], env)
            assert(code == 0), err
            output.joinpath('.complete').touch()
        return output



def get_params(sensor : str, scene_id : str):
    """ Get the parameters for different sensors """

    def get_params_OLI(scene_id : str):
        sat, _, pathrow, *_ = scene_id.split('_')
        assert(len(pathrow) == 6), scene_id
        path = pathrow[:3]
        row  = pathrow[3:]
        return {
            'prefix'     : f'{sat}/01/{path}/{row}/{scene_id}/',
            'maxResults' : 20,      
            'search'     : f'{sat}/01/{path}/{row}/{scene_id}/',

        }

    def get_params_MSI(scene_id : str):
        sat, level, date, id1, id2, zone_band_grid, _ = scene_id.split('_')
        assert(date[:4] != 2016 and date[:4] != 2015), 'Cannot process images before 2017 due to google storing the old multi-granule format'
        assert(len(zone_band_grid) == 6), scene_id
        zone = zone_band_grid[1:3]
        band = zone_band_grid[3:4]
        grid = zone_band_grid[4:]
        sid  = f'{scene_id}.SAFE'
        return {
            'prefix'     : f'tiles/{zone}/{band}/{grid}/{sid}/',
            'maxResults' : 300,
            'search'     : f'tiles/{zone}/{band}/{grid}/{sat}_{level}_{date.split("T")[0]}T*_{id1}_{id2}_{zone_band_grid}_*.SAFE/'
        }

    # Parsers for each sensor
    parsers = {
        'OLI' : get_params_OLI,
        'ETM' : get_params_OLI,
        'TM'  : get_params_OLI,
        'MSI' : get_params_MSI,
    } 
    return parsers[sensor](scene_id)
