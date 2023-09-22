from netCDF4 import Dataset
from pathlib import Path
from typing import Union, Optional

import numpy as np
import tempfile, sys
import shutil

try: 
    from ...atm_utils import subprocess_wrapper
    from ....utils import get_credentials, Location, assert_contains
    from ....exceptions import MissingProcessorError, AtmosphericCorrectionError


except: 
    # sys.path.append(Path(__file__).parent.parent.parent.as_posix())
    # sys.path.append(Path(__file__).parent.parent.parent.parent.as_posix())
    from atm_utils import subprocess_wrapper
    from utils import get_credentials, Location, assert_contains
    from exceptions import MissingProcessorError, AtmosphericCorrectionError



# Sensors that acolite can process 
VALID = [
    'MERIS', 

    'MSI', 
    'S2B', 
    'S2A', 
    'OLCI', 
    'S3A', 
    'S3B',

    'OLI', 
    'TM', 
    'ETM', 
]


# @subprocess_wrapper
def run_acolite(
    sensor    : str,
    inp_file  : Union[str, Path],
    out_dir   : Union[str, Path],
    ac_path   : Union[str, Path]   = '',
    overwrite : bool               = False, 
    timeout   : float              = 30, 
    location  : Optional[Location] = None, 
    **extra_cmd, 
) -> Path:
    """Atmospherically correct the given input file using acolite.

    Parameters
    ----------
    sensor    : str
        Satellite sensor (e.g. OLI, MSI, OLCI, ...).
    inp_file  : Path, str
        Path to the L1 input file to atmospherically correct.
    out_dir   : Path, str
        Directory to write the L2 result to.
    ac_path   :Path, str, optional
        SeaDAS installation directory. Must be given if atmospheric correction
        is actually being performed (i.e. the L2 file doesn't already exist).
    overwrite : bool, optional
        Overwrite the L2 output file if it already exists.
    timeout   : float, optional
        Number of minutes acolite is allowed to run before a TimeoutError 
        is raised.
    location  : Location, optional
        Location object which defines a bounding box to perform atmospheric
        correction on. Allows much faster processing if only a small area of
        the L2 output is actually required. 
    **extra_cmd
        Additional keywords that can be passed to this function are:
            * Any other acolite parameters.

    Returns
    -------
    Path
        Path to the L2 output file (i.e. `out_dir`/acolite.nc). 

    Raises
    ------
    TimeoutError
        If execution of any subprocess takes longer than `timeout` minutes.
    InvalidSelectionError
        If an invalid sensor is given as input, or credentials are missing
        for urs.earthdata.nasa.gov.
    MissingProcessorError
        If the acolite installation is not found.
    AtmosphericCorrectionError
        If acolite fails for any reason; check the error message for reason.

    References
    ----------
    .. [1] https://github.com/acolite/acolite

    """
    assert_contains(VALID, sensor, 'acolite sensor')

    # Setup paths
    inp_file = Path(inp_file).absolute()
    if sensor in ['MSI']: inp_file = Path(inp_file).joinpath(str(inp_file.stem) + '.SAFE')
    out_file = Path(out_dir).absolute().joinpath('acolite.nc')
    
    # Only run if output doesn't yet exist, or we want to overwrite
    if not out_file.exists() or overwrite:
            
        # Add the acolite installation to the working path, and import acolite
        ac_path = Path(ac_path)
        if not ac_path.exists():
            message = f'Acolite installation does not exist at "{ac_path}"'
            raise MissingProcessorError(message)
        sys.path.insert(0,ac_path.parent.as_posix())
        import acolite as ac 
    
        # Get the earthdata username and password
        username, password = get_credentials('urs.earthdata.nasa.gov')

        # Define the settings that will be used, and update with any additional commands that were given
        settings = {
            'inputfile'      : inp_file.as_posix(),
            'output'         : out_file.parent.as_posix(),
            'l2w_parameters' : 'Rrs_*',
            'EARTHDATA_u'    : username,
            'EARTHDATA_p'    : password,
            'verbosity'      : 2,
        }

        # Add bounding box
        if location is not None:
            settings.update({'limit': location.get_bbox('swne')})
        settings.update(extra_cmd)

        # Run acolite using the given settings
        ac.acolite.acolite_run(settings=settings)

        # Ensure the expected file exists
        outputs = list(out_file.parent.glob('*L2W.nc'))
        if len(outputs) != 1:
            msg = f'Acolite failure. Output directory contents: {outputs}'
            if 'Scenes' in settings['inputfile'] and sensor in settings['inputfile'] and False:
                shutil.rmtree(settings['inputfile'])
            raise AtmosphericCorrectionError(msg)

        # Delete previous output file if it exists
        if out_file.exists(): out_file.unlink()

        # Rename the new L2W output file have the standardized name
        outputs[0].rename(out_file)

        # Add variables from the other L2 file to the acolite.nc file
        l2r = list(out_file.parent.glob('*L2R.nc'))[0].as_posix()
        with Dataset(l2r) as source, Dataset(out_file.as_posix(), 'a') as target:
            for name, variable in source.variables.items():
                if 'rho' in name: 
                    target.createVariable(name, variable.datatype, variable.dimensions) 
                    target[name].setncatts(source[name].__dict__)
                    target[name][:] = source[name][:]

    return out_file         



if __name__ == '__main__':
    folder = '/scratch/job/14121763/Tiles/OLI/20180809/LC08_L1TP_015034_20180809_20180815_01_T1'
    folder = 'D:/Plotting/Simultaneous/Matchup_Pipeline/workspace/SCRATCH/Gathered/Scenes/ETM/LE07_L1TP_007027_20200627_20200824_01_T1/LE07_L1TP_007027_20200627_20200824_01_T1_MTL.txt'
    output = Path(folder).parent.joinpath('out').as_posix()

    print(Path(__file__).parent.absolute().as_posix())
    sys.path.insert(0, Path(__file__).parent.absolute().as_posix() )
    import acolite as ac
    settings = {
        'inputfile'      : Path(folder).parent.as_posix(),
        'output'         : output,
        'l2w_parameters' : 'Rrs_*',
    }
    ac.acolite.acolite_run(settings=settings)   

