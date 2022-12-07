from ...tests import test_function, get_results_path
from ...utils import Location, DatetimeRange
from ...config import l2gen_path, acolite_path
from . import AC_FUNCTIONS

from tempfile import TemporaryDirectory
from pathlib import Path 
import json

AC_PATHS = {
    'acolite' : acolite_path,#Path(__file__).parent.joinpath('acolite', 'acolite'),
    'l2gen'   : l2gen_path, #'/home/bsmith16/workspace/SeaDAS',
}


@test_function
def run_correction(method, **kwargs):
    """ Test atmospheric correction with the given method """
    kwargs.update({
        'function' : 'download_scene',
    })
    hash_file = get_results_path(**kwargs)
    if not hash_file.exists():
        message = f'WARN: No download_scenes output found at {hash_file}'
        message+= '\nTry running search/download tests first'
        return None, message

    with hash_file.open() as f:
        download_result = json.load(f)

    if download_result['output'] is None:
        return None, f'WARN: No file downloaded for {hash_file}'

    scene  = hash_file.parent.joinpath('Scenes', download_result['output'])
    kwargs = {
        'sensor'   : kwargs['sensor'],
        'inp_file' : scene,
        'out_dir'  : scene.joinpath('out'),
        'ac_path'  : AC_PATHS[method],
        'overwrite': True, 
        'location' : kwargs['location'],
    }
    if not kwargs['inp_file'].joinpath('.complete').exists():
        return None, f'WARN: scene not downloaded to {kwargs["inp_file"]}'
    kwargs['out_dir'].mkdir(exist_ok=True, parents=True)

    output = AC_FUNCTIONS[method](**kwargs)
    assert(output.exists()), (
        f'Missing atmospherically corrected file: {output}')
    return output, 'Corrected scene'



def get_tests():
    sensors    = ['ETM', 'OLI', 'TM'][-1:]
    functions  = [run_correction]
    sources    = ['EarthExplorer']
    ac_methods = ['l2gen', 'acolite'][1:]
    configs    = {
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
    del configs['Test 1']
    del configs['Test 2']
    del configs['Test 3']

    return [
        ('sensor',   sensors),
        ('method',   ac_methods),
        ('Source',   sources),
        ('function', functions),
        ('kwargs',   configs),
    ]
