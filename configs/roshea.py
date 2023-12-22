from subprocess import getoutput
from pathlib import Path 
import os
import sys
username = getoutput('whoami') 

#===============***** This is for f001 - av3 - Matchup processing
proc = "MSI"

if proc == "OLI":
	datasets = ['OLI_test_image_Oyster_farm']
	sensors  = ['OLI'] # 'MOD','VI'

if proc == "MSI":
	datasets = ['MSI_test_image_Honga_TS_1']
	sensors  = ['MSI']

#===================================
#         Path Definitions
#===================================
tiles = {'OLI' : {'IRL' : '016040', 'GB': '024029','CB':'014034'},
        'MSI' : {'CB'  : 'T18SUG', '20201017': ''},}

# AC processors' paths 
l2gen_path     = '/run/cephfs/m2cross_scratch/f003/skabir/Aquaverse/matchup_deployment_SLURM/atm_corr/ac_processors/SeaDAS/SeaDAS_V2022_3/ocssw'
acolite_path   = '/run/cephfs/m2cross_scratch/f003/skabir/Aquaverse/matchup_deployment_SLURM/atm_corr/ac_processors/acolite/acolite-20221114.0/acolite' 
polymer_path   = '/run/cephfs/m2cross_scratch/f003/skabir/Aquaverse/matchup_deployment_SLURM/atm_corr/ac_processors/polymer/polymer-v4.16.1/polymer'

aquaverse_path = str(Path(__file__).resolve().parent.parent.joinpath('AC').joinpath('L2_processing').joinpath('aquaverse'))

stream_backend_path = '/tis/m2cross/scratch/f002/wwainwr1/stream/backend'
stream_env_path     = '/tis/m2cross/scratch/f002/wwainwr1/venv/bin/activate'

#scratch_path   = Path(f'/data/{username}').joinpath('SCRATCH')
scratch_path   = Path('/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH') 
insitu_path    = scratch_path.joinpath('Insitu') 
output_path    = scratch_path.joinpath('Gathered')

#===================================
#    Processing Parameters
#===================================
local_processing       = True
test_pipeline_celery   = False
#===================================
#    Data Search Parameters
#===================================  
max_cloud_cover        = 100 #Max cloud cover for downloading/processing. Only works for Sentinel 2 and OLI
search_day_window      = None
search_minute_window   = None
search_year_range      = None
timeseries_or_matchups = 'timeseries'
scene_id               = '' # will only process scenes with this substring if set
max_processing_scenes  = 40
download_via_aquaverse = False

#===================================
# Atmospheric Correction Parameters
#===================================
ac_timeout = 120 # number of minutes an AC processor can run before being terminated
ac_methods = ['l2gen'] # Atmospheric Correction methods to apply
apply_bounding_box = True

#===================================
#    Data Extraction Parameters
#===================================
extract_window = 1 # pixels to extract around the center pixel (e.g. 1 -> 3x3 window)

#===================================
#    Plotting Parameters
#===================================
fix_projection_Rrs= False
plot_products     = True
plot_Rrs          = False

#===================================
#    Data Cleanup Parameters
#===================================
remove_L2_tile = False
overwrite      = False
remove_scene_folder = False
remove_L1_tile=False

#===================================
#    Atmospheric correction arguments
#===================================
extra_cmd = {}

#===================================
#    Location specific overrides
#===================================
# if  'MERIS_test_image' in datasets[0] or 'MOD_VI_test_image' in datasets[0]: 
    # overwrite           = True
    # ac_methods          = ['polymer']  #['l2gen','acolite','aquaverse','polymer']

    # remove_scene_folder = True 
    # remove_L1_tile      = True
    # fix_projection_Rrs  = False
    # search_day_window   = 0 
    # plot_products       = False
    # extract_window      = 1 #3x3

    # extra_cmd = {'l2gen': {'MOD' : {'aer_opt' : '-2','aer_wave_short' : '869','aer_wave_long'  : '2130','l2prod' : [ 'Rrs_nnn', 'rhos_nnn', 'Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},
                            # 'VI' : {'aer_opt' : '-2','aer_wave_short' : '868','aer_wave_long'  : '2258','l2prod' : [ 'Rrs_nnn', 'rhos_nnn','Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},
                         # 'MERIS' : {'aer_opt' : '-2','aer_wave_short' : '779','aer_wave_long'  :  '865','l2prod' : [ 'Rrs_nnn', 'rhos_nnn','Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},

                            # },
                  # 'acolite': {},
                  # 'polymer': {},}
    # timeseries_or_matchups = 'matchups'
    
if  'OLI_test_image' in datasets[0]  or 'MSI_test_image' in datasets[0] : 
    overwrite              = False # what does it overwrite - everything - yes, even pikle file
    ac_methods             = ['aquaverse'] #'l2gen','acolite','polymer','aquaverse'
    download_via_aquaverse = True
    timeseries_or_matchups = 'timeseries' #'matchups' # matchups was not working - key error scene id
    remove_scene_folder    = True 
    remove_L1_tile         = True
    fix_projection_Rrs     = False
    plot_products          = False # for which AC processor it works
    plot_Rrs               = False
    extract_window         = 1 #3x3
    apply_bounding_box     = True # what is this - process only a portion of the image
    search_day_window      = 100 # looks like it is searching for one day range
    max_cloud_cover        = 20 
    #scene_id               = '014034_20210420'#'T18SUG' if 'MSI' in sensors[0] else '014034' if 'OLI' in sensors[0] else '' #'019031' '044033' 020031 #T18SUG
    #scene_id               = tiles[sensors[0]][datasets[0].split('_')[-1]]

#Checks
if 'ctest' in datasets[0]:
    test_pipeline_celery=True

if search_day_window is None  and search_year_range is None and search_minute_window is None:
    search_day_window=0

if 'aquaverse' not in ac_methods and download_via_aquaverse == True: assert(0)

if 'aquaverse' in ac_methods and 'OLI' not in sensors and 'MSI' not in sensors: assert(0)

if 'aquaverse' in ac_methods and 'MSI' in sensors: print('MSI Images after Jan 2022 will not successfully process with Aquaverse')
