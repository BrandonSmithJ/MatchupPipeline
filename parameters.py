from pathlib import Path
import argparse

from . import config



parser = argparse.ArgumentParser(prog='pipeline', epilog="""
_________________________________________________
 In Situ <-> Satellite Overpass Matchup Pipeline
""", formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-d', '--datasets',    type=str, nargs='+', 
    default=config.datasets,
    help='Name of the in situ dataset(s) to find matchups for\n\n')

parser.add_argument('-s', '--sensors',     type=str, nargs='+', 
    default=config.sensors,
    help='Name of the satellite sensor(s) find matchups for\n\n')

parser.add_argument('-a', '--ac_methods',  type=str, nargs='+', 
    default=config.ac_methods,
    help='Atmospheric Correction methods to apply\n(options: %(choices)s)\n\n',
    choices=['l2gen', 'polymer', 'acolite'])

parser.add_argument('-u', '--username',    type=str,            
    default=config.username, 
    help='Username for storage / job labeling\n(default: %(default)s)\n\n')

parser.add_argument('-i', '--insitu_path', type=str,            
    default=config.insitu_path, 
    help='Path to in situ dataset folders\n(default: %(default)s)\n\n')

parser.add_argument('-o', '--output_path', type=str, 
    default=config.output_path, 
    help='Path where outputs will be saved\n(default: %(default)s)\n\n')

parser.add_argument('--overwrite', action='store_true', 
    default=config.overwrite,
    help='Redownload and correct scenes already saved\n(default: False)')


#===================================
#    Data Search Parameters
#===================================  
search_parameters = parser.add_argument_group(
    'Scene Search Parameters', 
    'Set any parameters associated with searching for a scene',
)

dt_range = search_parameters.add_mutually_exclusive_group()
dt_range.add_argument('--search_day_window', type=int,
    default=config.search_day_window,
    help='Number of days surrounding an in situ sample to match\n'+
         '(default: %(default)s)')

dt_range.add_argument('--search_minute_window', type=int,
  default=config.search_minute_window,
    help='Number of minutes surrounding an in situ sample to match\n'+
    'Only one of search_day_window or search_minute_window can be set')

dt_range.add_argument('--search_year_range', type=int,
  default=config.search_year_range,
    help='Number of years after provided date to search\n'+
    'Overrides both search_day_window and search_minute_window')

dt_range.add_argument('--timeseries_or_matchups', nargs=2, action='append',
  default=config.timeseries_or_matchups,
    help='Should we search as if it is a timeseries of a location, or as if it is matchups from different locations')

#===================================
# Atmospheric Correction Parameters
#===================================
ac_parameters = parser.add_argument_group(
    'Atmospheric Correction Parameters', 
    'Set any parameters associated with specific AC processors',
)

ac_parameters.add_argument('--ac_path',   nargs=2, action='append', 
    metavar=('AC_METHOD', 'PATH [--ac_path AC_METHOD PATH ...]'), 
    default=[[  'l2gen', config.l2gen_path], 
             ['polymer', config.polymer_path], 
             ['acolite', config.acolite_path]],
    help='Set the install path for any AC methods\n'+
         'Multiple AC paths can be set by using --ac_path multiple times\n\n')

ac_parameters.add_argument('--ac_kwargs', nargs=3, action='append',
    metavar=('AC_METHOD','KEY','VALUE [--ac_kwargs AC_METHOD KEY VALUE ...]'),
    help='Pass arguments directly to the AC processors\n'+
         'e.g. to discard l2gen\'s RSR out-of-band correction:\n'+
         '\t--ac_kwargs l2gen outband_opt 0')

ac_parameters.add_argument('--extra_cmd',   nargs=2, action='append', 
    metavar=('AC_METHOD', 'PATH [--ac_path AC_METHOD PATH ...]'), 
    default=config.extra_cmd,
    help='Set a dictionary of AC kwargs')

ac_parameters.add_argument('--ac_timeout',  type=int,
    default=config.ac_timeout, 
    help='Number of minutes an AC processor can run before being terminated\n'+
         'Timeout can also be set for AC processors individually, by using '+
         'the --ac_kwargs flag')


#===================================
#    Data Extraction Parameters
#===================================
extract_parameters = parser.add_argument_group(
    'Data Extraction Parameters', 
    'Set any parameters associated with extracting data from scenes',
)

extract_parameters.add_argument('--extract_window', type=int, 
    default=config.extract_window,
    help='Pixels to extract around the center pixel (e.g. 1 -> 3x3 window)')

#===================================
#    Plotting Parameters
#===================================
plot_parameters = parser.add_argument_group(
    'Plot Parameters', 
    'Set any parameters associated with plotting data from scenes',
)

plot_parameters.add_argument('--fix_projection_Rrs', type=int, 
    default=config.fix_projection_Rrs,
    help='Fix projection of Rrs.')

plot_parameters.add_argument('--plot_products', type=int, 
    default=config.plot_products,
    help='plot water quality products.')

#===================================
#    Data Cleanup Parameters
#===================================
cleanup_parameters = parser.add_argument_group(
    'Cleanup Parameters', 
    'Set any parameters associated with removing unnecesary data from scenes',
)
cleanup_parameters.add_argument('--remove_L1_tile', type=bool, 
    default=config.remove_L1_tile,
    help='Removes the Level 1 file after correction')

cleanup_parameters.add_argument('--remove_L2_tile', type=bool, 
    default=config.remove_L2_tile,
    help='Removes the Level 2 file')

cleanup_parameters.add_argument('--remove_scene_folder', type=bool, 
    default=config.remove_scene_folder,
    help='Removes the entire scene folder')

def get_args(kwargs={}, use_cmdline=True, **kwargs2):
    kwargs2.update(kwargs)

    # Whether or not to use command line flags
    if use_cmdline: args = parser.parse_args()
    else:           args = parser.parse_args([])

    # Update parsed args with anything specifically passed to get_args
    for k, v in kwargs2.items():
        setattr(args, k, v)

    # Perform some clean up on various parameters
    args.ac_methods   = list(set(args.ac_methods))
    args.ac_path      = {ac: path for ac, path in args.ac_path}
    args.ac_kwargs    = {ac: {k:v for a,k,v in args.ac_kwargs if a == ac} for ac in set([v[0] for v in (args.ac_kwargs or [])])}
    args.insitu_path  = Path(args.insitu_path)
    args.output_path  = Path(args.output_path)

    if getattr(args, 'search_minute_window', None) is not None:
        args.search_day_window = None

    # Perform some validation checks
    for ac in args.ac_methods: 
        assert(Path(args.ac_path[ac]).exists()), f'Install path for {ac} does not exist at "{args.ac_path[ac]}"'
    for ds in args.datasets:
        assert(Path(args.insitu_path, ds).exists()), f'Dataset {ds} does not exist at "{Path(args.insitu_path, ds)}"'

    return args