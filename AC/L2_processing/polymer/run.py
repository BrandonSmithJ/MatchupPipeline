import pyximport
pyximport.install()
import sys
from pathlib import Path 
from importlib import import_module
from subprocess import getoutput

username = getoutput('whoami')
config   = import_module('.....configs.'+username,package=__name__)
polymer_path = config.polymer_path
#from ....config import polymer_path
#polymer_path = '/home/bsmith16/AC/polymer/polymer-v4.16.1/polymer-v4.16.1/polymer'
sys.path.append(str(Path(polymer_path).parent))
try:
     from polymer.level1_landsat8 import Level1_OLI
     from polymer.level1_hico import Level1_HICO
     from polymer.level1_msi import Level1_MSI
     from polymer.level1_olci import Level1_OLCI
     from polymer.level1_nasa import Level1_MODIS, Level1_VIIRS
     from polymer.level2_nc import Level2_NETCDF
     from polymer.main import run_atm_corr
     from polymer.gsw import GSW
     from polymer.params import params_v3_5, params_v3_5_OLCI_MM01, Params
except Exception as e: 
     print(f'Could not import polymer: {e}')
from ....utils import Location
from ...atm_utils import subprocess_wrapper, extract_xy_from_lonlat
from ...L1_processing.run_l1 import run_angles

from pathlib import Path
from typing import Union, Optional
import os, subprocess, logging

logger = logging.getLogger('MatchupPipeline')

try:
     Level1 = {
     'MSI'  : Level1_MSI,
     'S2A'  : Level1_MSI,
     'S2B'  : Level1_MSI,
     'OLI'  : Level1_OLI,
     'HICO' : Level1_HICO,
     'OLCI' : Level1_OLCI,
     'VI'   : Level1_VIIRS,
     'MODA' : Level1_MODIS,
     'MODT' : Level1_MODIS,
     'MOD'  : Level1_MODIS,
     }
except:
     pass

#@subprocess_wrapper
def run_polymer(    
    sensor    : str,                        # Satellite sensor
    inp_file  : Union[str, Path],           # Path to the L1 input file 
    out_dir   : Union[str, Path],           # Directory to write the L2 result
    ac_path   : Union[str, Path] = '',      # Polymer installation directory 
    overwrite : bool             = False,   # Overwrite the output file if it already exists
    location  : Optional[Location] = None,  # Location object for bounding box
    lat=None, lon=None,
    **extra_cmd,                            # Any extra commands to pass to polymer
) -> Path:                                  # Returns path to the acolite.nc result netcdf

    # Setup paths
    out_file = Path(out_dir).absolute().joinpath('polymer.nc')
    inp_file = Path(inp_file).absolute()
    
    # Perform any additional preprocessing which is necessary
    if sensor in ['OLI', 'MSI', 'S2A', 'S2B', 'TM', 'ETM']:
        inp_file = inp_file.parent if sensor not in ['OLI','MSI'] else  inp_file.joinpath(str(inp_file.stem) + '.SAFE') if sensor in ['MSI'] else inp_file

        # OLI requires angle files to be generated
        if sensor in ['OLI']:
            run_angles(list(inp_file.glob('*_ANG.txt'))[0], overwrite=overwrite)

    # MODIS & VIIRS require l2gen to be run first
    if sensor in ['VI', 'MOD', 'MODA', 'MODT']:
        inp_file = out_file.with_name('l2gen.nc')
        assert(inp_file.exists()), 'Must run l2gen prior to polymer for MODIS & VIIRS'

    # Add bounding box
    if location is not None:
        extra_cmd.update({
            'coords' : {
                'south' : [location.s, (location.e + location.w)/2.],
                'west'  : [(location.n + location.s)/2., location.w],
                'north' : [location.n, (location.e + location.w)/2.],
                'east'  : [(location.n + location.s)/2., location.e],
            }
        })

    # Only run if output doesn't yet exist, or we want to overwrite
    if not out_file.exists() or overwrite:
        kwargs = {'blocksize':2000}

        # Approximate the line / column for a given coordinate set
        if sensor in ['MSI', 'S2A', 'S2B', 'OLI', 'ETM', 'TM']:
            if lon is not None and lat is not None:
                box = 50
                x,y, nrow, ncol = extract_xy_from_lonlat(sensor, filename, lon, lat)
                kwargs['sline'] = max(0, y - box)    # start row 
                kwargs['scol']  = max(0, x - box)    # start col
                kwargs['eline'] = min(nrow, y + box) # end row
                kwargs['ecol']  = min(ncol, x + box) # end col

        # Use the lonlat2pixline program to determine the line / column
        elif sensor in ['OLCI', 'HICO']:
            if lon is not None and lat is not None:
                assert(root), 'Must provide root SeaDAS location'
                box = 50
                cmd = [f'{root}/bin/lonlat2pixline', str(filename), str(lon), str(lat)]
                env = dict(os.environ)

                if '/tis' in str(root):
                    root = Path(__file__).resolve().parent.parent.parent.joinpath('SeaDAS')

                env['OCDATAROOT'] = f'{root}/share'
                env['OCVARROOT']  = f'{root}/var'
                process  = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = process.communicate()
                
                if process.returncode != 0:
                    err = err.decode('utf-8')
                    out = out.decode('utf-8')
                    logger.error(f'{out}\n{err}\n{process.returncode}')
                    raise Exception(f'{err}\n{out}\n{process.returncode}\nCMD: {cmd}')

                out = [line for line in out.decode('utf-8').split('\n') if line.strip()]
                y   = out[-4]
                x   = out[-2]
                assert('sline' in y and 'spixl' in x), out
                y   = int(y.replace('sline=',''))
                x   = int(x.replace('spixl=',''))

                if sensor == 'HICO':
                    nrow, ncol = 2000, 512
                else:
                    _,_, nrow, ncol = extract_xy_from_lonlat(sensor, filename, lon, lat)
                kwargs['sline'] = max(0, y - box)    # start row 
                kwargs['scol']  = max(0, x - box)    # start col
                kwargs['eline'] = min(nrow, y + box) # end row
                kwargs['ecol']  = min(ncol, x + box) # end col

        if sensor in ['MSI', 'S2A', 'S2B']:
            inp_file = Path(inp_file).joinpath('GRANULE') #list(Path(inp_file).joinpath('GRANULE').glob('*/'))[0]
            inp_file = inp_file.joinpath(os.listdir(inp_file)[0])
            kwargs['resolution'] = '60' # anything less than 60 fails to run. also need to change ncol/nrow if this changes

        if sensor in ['OLI', 'MODA', 'MODT', 'VI', 'TM', 'ETM', 'MOD']:
            kwargs['blocksize'] = (1000, 1000)

        if sensor not in ['VI', 'MODA', 'MODT', 'MOD']:
            if 'SCRATCH' in os.environ:
                gsw_path = Path(os.environ['SCRATCH'])
            else:
                gsw_path = Path(__file__).parent.resolve().joinpath('polymer')
            gsw_path = gsw_path.joinpath('data_landmask_gsw')
            gsw_path.mkdir(parents=True, exist_ok=True)
            kwargs['landmask'] = GSW(directory=gsw_path.as_posix(), agg=1)

        # name = 'GENERIC'
        # if sensor in ['S2A', 'S2B']:
        #     name = 'MSI'
        # elif sensor in ['VI']:
        #     name = 'VIIRS'
        # elif sensor in ['MOD', 'MODA', 'MODT']:
        #     name = 'MODIS'
        # elif sensor in ['OLI', 'MSI', 'OLCI', 'SeaWiFS', 'HICO']:
        #     name = sensor

        atm_kwargs = {}
        # param = Params(name)
        # bands = param.bands_lut
        # if len(bands) and name == 'OLCI':
        #     atm_kwargs['bands_rw'] = sorted(bands + [681, 709])

        #force_ipv4()
        os.environ['WGETRC'] = Path(__file__).parent.parent.parent.parent.resolve().joinpath('credentials', 'eosdis_wgetrc').as_posix()
        ancillary_path = inp_file.joinpath('ANCILLARY', 'METEO') if 'l2gen.nc' not in str(inp_file) else inp_file.parent.joinpath('ANCILLARY', 'METEO') 
        Path(ancillary_path).mkdir(parents=True, exist_ok=True)
        # monkeypatch to fix pardees certificate errors
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        inp_file = str(inp_file)
        out_file = str(out_file)
        run_atm_corr(
            Level1[sensor](inp_file, **kwargs),
            Level2_NETCDF(filename=out_file, overwrite=overwrite),
            **atm_kwargs,
        )#multiprocessing=4)#, **params_v3_5)
    return Path(out_file)
