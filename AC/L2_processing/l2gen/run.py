from typing import Union, Iterable, Optional
from pathlib import Path
import os, subprocess, shutil, logging

from .default_config import DEFAULT_CONFIG, SENSOR_CONFIG
from ..sensor_parameters import SENSOR_ALIASES, SENSOR_GAINS
from ...atm_utils import execute_cmd
from ....utils import Location, assert_contains
from ....exceptions import (
    MissingProcessorError, 
    OutOfBoundsError, 
    AtmosphericCorrectionError,
    MultipleSensorsError,
)


logger = logging.getLogger('MatchupPipeline')


# Files used for l2gen correction
FILENAME = {
    # Sentinel
    'MSI'   : '**/manifest.safe',
    'S2A'   : '**/manifest.safe',
    'S2B'   : '**/manifest.safe',
    'OLCI'  : '**/xfdumanifest.xml',
    'S3A'   : '**/xfdumanifest.xml',
    'S3B'   : '**/xfdumanifest.xml',

    # Landsat
    'OLI'   : '**/*_MTL.txt',
    'ETM'   : '**/*_MTL.txt',
    'TM'    : '**/*_MTL.txt',

    # Other
    'MERIS' : '**/xfdumanifest.xml',
    'MOD'   : '**/*.L1A_LAC',
    'VI'    : '*.nc',
}


def run_l2gen(
    sensor    : str, 
    inp_file  : Union[str, Path],
    out_dir   : Union[str, Path],
    ac_path   : Union[str, Path]   = '',
    overwrite : bool               = False,
    timeout   : float              = 30, 
    location  : Optional[Location] = None,
    **extra_cmd, 
) -> Path: 
    """Atmospherically correct the given input file using SeaDAS (l2gen).

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
        Number of minutes l2gen is allowed to run before a TimeoutError 
        is raised.
    location  : Location, optional
        Location object which defines a bounding box to perform atmospheric
        correction on. Allows much faster processing if only a small area of
        the L2 output is actually required. 
    **extra_cmd
        Additional keywords that can be passed to this function are:
            * l2prod      
                Explicitly set products l2gen will create. For instance, to
                run the atmospheric correction faster, only retrieve Rrs/chl:
                    out_file = run_l2gen(..., l2prod=['Rrs_nnn', 'chlor_a'])
            * l2prod_exclude
                Products to exclude from the default parameter list (see
                default_config.py for defaults).
            * outband_opt
                Set outband_opt=0 if you do not want l2gen's RSR out-of-band
                correction to be applied. 
            * Any other l2gen command line parameter; see default_config.py.

    Returns
    -------
    Path
        Path to the L2 output file (i.e. `out_dir`/l2gen.nc). 

    Raises
    ------
    TimeoutError
        If execution of any subprocess takes longer than `timeout` minutes.
    InvalidSelectionError
        If an invalid sensor is given as input.
    MissingProcessorError
        If the SeaDAS installation is not found.
    OutOfBoundsError
        If the requested `location` is out of bounds for the input file.
    AtmosphericCorrectionError
        If l2gen fails for any reason; check the error message for reason.
    MultipleSensorsError
        If multiple aliases are found in a filename (e.g. S2A_S2B.nc)

    """
    assert_contains(FILENAME, sensor, 'l2gen sensor')

    # Setup paths
    out_file = Path(out_dir).absolute().joinpath('l2gen.nc')
    inp_file = Path(inp_file).absolute()

    # Use the appropriate file, if not already given
    if inp_file.is_dir():
        try: 
            inp_file = list(inp_file.glob(FILENAME[sensor]))[0]
        except: 
            contents = list(inp_file.glob('*'))
            logger.warning(f'Suffix file not found for {sensor}: {contents}')
   
    # Only run if output doesn't yet exist, or we want to overwrite
    if not out_file.exists() or overwrite:

        # Ensure the SeaDAS installation exists
        ac_path = Path(ac_path or 'SeaDAS').absolute()
        if not ac_path.exists():
            message = f'SeaDAS installation does not exist at "{ac_path}"'
            raise MissingProcessorError(message)

        # Add the bounding box to the commands if a location is given
        if location is not None:
            keys = ['north', 'south', 'east', 'west']
            bbox = location.get_bbox('nsew', dict_keys=keys)
            extra_cmd.update(bbox)

        # Generate the command we'll use to execute l2gen
        cmd = generate_cmd(sensor, inp_file, out_file, ac_path, **extra_cmd)

        # Create the execution environment
        env = dict(os.environ)
        env.update({
            'OCDATAROOT' : ac_path.joinpath('share').as_posix(),
            'OCVARROOT'  : ac_path.joinpath('var').as_posix(),
        })

        # Run the l2gen atmospheric correction
        exec_kwargs    = {'timeout': timeout, 'raise_e': False}
        code, out, err = execute_cmd(cmd, env, **exec_kwargs)

        # A few possible reasons why the command did not succeed
        if code != 0:

            # Bounding box that was passed in is not valid for the file
            if 'north, south, east, west box not in this file' in out.lower():
                raise OutOfBoundsError(f'Out of Bounds. Command: {cmd}')

            # Image is in tiled format - need to fix with gdalwarp
            if 'can not read scanlines from a tiled image' in err.lower():
                inp_idx = [i for i, c in enumerate(cmd) if '--ifile=' in c][0]
                new_inp = convert(inp_file, env, timeout)
                cmd[inp_idx] = f'--ifile={new_inp}'
                
                # Try to run l2gen again with the new file as input
                code, out, err = execute_cmd(cmd, env, **exec_kwargs)

        # Raise an exception if we still don't have a successful execution
        if code != 0:
            sep = ''.join(['-'] * 20)
            msg = f'Error executing command "{cmd}":\n'
            msg+= '\n'.join([sep, 'Subprocess Output:', out, ''])
            msg+= '\n'.join([sep, 'Subprocess Error:',  err, ''])
            logger.error(msg)
            raise AtmosphericCorrectionError(msg)

    return out_file



def generate_cmd(   
    sensor   : str, 
    inp_file : Path,
    out_file : Path,
    ac_path  : Path,
    **extra_cmd,   
) -> Iterable[str]: 
    """Generate the command used to execute l2gen.

    Parameters
    ----------
    sensor    : str
        Satellite sensor (e.g. OLI, MSI, OLCI, ...).
    inp_file  : Path
        Path to the L1 input file to atmospherically correct.
    out_file  : Path
        Directory to write the L2 result to.
    ac_path   : Path
        SeaDAS installation directory.
    **extra_cmd
        Additional keywords that can be passed to this function are:
            * l2prod      
                Explicitly set products l2gen will create. For instance, to
                run the atmospheric correction faster, only retrieve Rrs/chl:
                    out_file = run_l2gen(..., l2prod=['Rrs_nnn', 'chlor_a'])
            * l2prod_exclude
                Products to exclude from the default parameter list (see
                default_config.py for defaults).
            * outband_opt
                Set outband_opt=0 if you do not want l2gen's RSR out-of-band
                correction to be applied. 
            * Any other l2gen command line parameter; see default_config.py.

    Returns
    -------
    Iterable[str]
        Returns l2gen command as a list.

    Raises
    ------
    MultipleSensorsError
        If multiple aliases are found in a filename (e.g. S2A_S2B.nc)

    """
    # Use the non-tiled files if we've already converted the original
    converted = inp_file.parent.joinpath('converted', inp_file.name)
    if converted.exists(): inp_file = converted

    # Initialize the command definition
    cmd = {
        'ifile' : inp_file.as_posix(), # Input file
        'ofile' : out_file.as_posix(), # Output file
    }

    # Add general l2gen default parameters
    cmd.update(DEFAULT_CONFIG)

    # Use a null landmask (removes shorelines otherwise)
    land = ac_path.joinpath('share', 'common', 'landmask_null.dat')
    cmd.update( {'land' : land.as_posix()} )

    # Add geofile
    geo = inp_file.with_suffix('.GEO')
    cmd.update( {'geofile' : geo.as_posix()} if geo.exists() else {} )

    # If the sensor has any aliases (e.g. MSI -> S2A), ensure exactly 
    # one alias is contained in the filename
    aliases = SENSOR_ALIASES.get(sensor, [])
    n_alias = sum([alias in str(inp_file) for alias in aliases])
    if aliases and n_alias != 1:
        message  = f'Exactly one of {aliases} for sensor {sensor} must be '
        message += f'found within the filename "{inp_file}"; found {n_alias}.'
        raise MultipleSensorsError(message)        

    # Add all parameters existing for either the sensor, or any of its aliases
    for alias in [sensor] + SENSOR_ALIASES.get(sensor, []):
        if alias == sensor or alias in inp_file.as_posix():
        
            # Add sensor-specific default parameters and gains
            if alias in SENSOR_CONFIG: cmd.update(SENSOR_CONFIG[alias])
            if alias in SENSOR_GAINS:  cmd.update({'gain':SENSOR_GAINS[alias]})

            # Add filter
            cwd         = Path(__file__).absolute().parent
            filter_file = cwd.joinpath('filters', f'{alias}.dat')
            cmd.update({
                'filter_file' : filter_file.as_posix(), 
                'filter_opt'  : 1,
            } if filter_file.exists() else {})

    # Add / update any commands that were directly passed in
    cmd.update(extra_cmd)

    # Get excluded products (if any)
    exclude = cmd.pop('l2prod_exclude', [])

    # Format the output products appropriately
    if 'l2prod' in cmd: 
        l2prod = [prod for prod in cmd['l2prod'] if prod not in exclude]
        cmd.update( {'l2prod' : ' '.join(l2prod)} )

    # Format the command appropriately and return it
    executable = ac_path.joinpath('bin', 'l2gen').as_posix()
    return [executable] + [f'--{key}={val}' for key, val in cmd.items()]



def convert(
    inp_file : Path,  # 
    env      : dict,  # 
    timeout  : float, # 
) -> Path:            # Returns path of the new input file
    """Image is in tiled format, which is fixed with gdalwarp.

    Parameters
    ----------
    inp_file : Path
        Path to the L1 input file.
    env      : dict
        Environment variables to set in the execution process.
    timeout  : float
        Number of minutes the conversion is allowed to run before 
        a TimeoutError is raised.

    Returns
    -------
    Path
        Returns path of the new input file, which is contained in a new
        'converted' directory. 

    Raises
    ------
    TimeoutError
        If execution of any subprocess takes longer than `timeout` minutes.
        
    """
    # Convert all TIF files with gdalwarp
    for tif in inp_file.parent.glob('*.TIF'):
        converted = tif.parent.joinpath('converted', tif.name)
        conv_cmd  = ['gdalwarp', '-co', 'TILED=NO']
        conv_cmd += [tif.as_posix(), converted.as_posix()]

        if not converted.exists():
            converted.parent.mkdir(parents=True, exist_ok=True)
            execute_cmd(conv_cmd, env, timeout=timeout)

    # Copy all txt files into the new 'converted' folder
    for txt in inp_file.parent.glob('*.txt'):
        converted = txt.parent.joinpath('converted', txt.name)
        if not converted.exists():
            shutil.copyfile(txt.as_posix(), converted.as_posix())

    return inp_file.parent / 'converted' / inp_file.name
