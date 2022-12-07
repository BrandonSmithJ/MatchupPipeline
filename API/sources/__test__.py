from ...tests import test_function, get_results_path
from ...utils import Location, DatetimeRange
from .. import API
from . import SOURCES

from tempfile import TemporaryDirectory
from pathlib import Path 
import json


@test_function
def search_scenes(Source, **kwargs):
    """ Test search scenes with the given Source """
    scenes = Source().search_scenes(**kwargs)
    return scenes, f'Found {len(scenes)} matching scenes'


@test_function
def download_scene(Source, sensor, **kwargs):
    """ Test downloading the first found scene with the given Source """
    kwargs.update({
        'Source'   : Source,
        'sensor'   : sensor,
        'function' : 'search_scenes',
    })
    hash_file = get_results_path(**kwargs)
    if not hash_file.exists():
        return None, f'WARN: No search_scenes output found at {hash_file}'

    with hash_file.open() as f:
        search_result = json.load(f)

    source = Source()
    scenes = search_result['output'] 
    # scenes = source.search_scenes(sensor=sensor, **kwargs)

    
    if len(scenes):
        with TemporaryDirectory() as tmpdir:
            tmpdir = hash_file.parent.joinpath('Scenes')
            tmpdir.mkdir(exist_ok=True, parents=True)

            tmpdir = Path(tmpdir)
            scene  = sorted(scenes.keys())[0]
            detail = scenes[scene]
            source.download_scene(**{
                'sensor'        : sensor,
                'scene_id'      : scene,
                'scene_details' : detail,
                'scene_folder'  : tmpdir,
                'overwrite'     : False,
            })

            output = tmpdir.joinpath(scene)
            assert(output.joinpath('.complete').exists()), (
                f'Missing completion file: {list(output.glob("*"))}')
            return scene, 'Downloaded scene'
    return None, 'No scene downloaded'



def get_tests():
    sensors   = list(API.keys())
    functions = [search_scenes, download_scene]
    configs   = {
        'Test 1' : {
            'location' : Location(lon=-76, lat=37),
            'dt_range' : DatetimeRange(start='20180115', end='20180123'),
        },
        'Test 2' : {
            'location' : Location(n=38, s=36, e=-78, w=-76),
            'dt_range' : DatetimeRange(center='20180119', window=4),        
        },
        'Test 3' : {
            'location' : Location(lon=-76, lat=37),
            'dt_range' : DatetimeRange(start='20140212', end='20140212'),
        },
        'Test 4' : {
            'location' : Location(lon=-76, lat=37),
            'dt_range' : DatetimeRange(start='19980115', end='19980123'),
        },
    }

    sources = dict(SOURCES)
    # del sources['EarthExplorer']
    del configs['Test 1']
    del configs['Test 2']
    del configs['Test 3']
    sensors = [s for s in sensors if s != 'MSI']
    sensors = ['TM']

    return [
        ('sensor',   sensors),
        ('Source',   sources),
        ('function', functions),
        ('kwargs',   configs),
    ]
