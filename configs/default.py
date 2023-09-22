from subprocess import getoutput
from pathlib import Path 
import os
import sys
username = getoutput('whoami') 
datasets = ['OLCI_test_image'] #['OLI_test_image'] #'MSI_test_image_CB'
sensors  = ['OLCI']            #['OLI'] # 'MSI'


#===================================
#         Path Definitions
#===================================
tiles = {'OLI' : {'IRL' : '016040', 'GB': '024029','CB':'014034'},
         'MSI' : {'CB'  : 'T18SUG_20210709', '20201017': ''},}

l2gen_path     = '/tis/m2cross/scratch/f004/roshea/Seadas_versions/Seadas_V2022_3/ocssw' 

if 'OLI' or 'MSI'  in sensors:
    l2gen_path = '/home/roshea/SeaDAS/SeaDAS_V2022_3/ocssw'
if 'MOD' in sensors:
    l2gen_path =  '/data/roshea/SCRATCH/AC/ocssw'
    
polymer_path   = '/home/bsmith16/AC/polymer/polymer-v4.16.1/polymer-v4.16.1/polymer'
acolite_path   = '/home/roshea/AC/acolite/acolite-20221114.0/acolite' 
aquaverse_path = str(Path(__file__).resolve().parent.parent.joinpath('AC').joinpath('L2_processing').joinpath('aquaverse'))

stream_backend_path = '/tis/m2cross/scratch/f002/wwainwr1/stream/backend'
stream_env_path     = '/tis/m2cross/scratch/f002/wwainwr1/venv/bin/activate'

scratch_path   = Path(f'/data/{username}').joinpath('SCRATCH') 
insitu_path    = scratch_path.joinpath('Insitu') 
output_path    = scratch_path.joinpath('Gathered')

#===================================
#    Data Search Parameters
#===================================  
max_cloud_cover        = 100 #Max cloud cover for downloading/processing. Only works for Sentinel 2 and OLI
search_day_window      = None
search_minute_window   = None
search_year_range      = None
timeseries_or_matchups = 'timeseries'
scene_id               = '' # will only process scenes with this substring if set
max_processing_scenes  = 20
#===================================
# Atmospheric Correction Parameters
#===================================
ac_timeout = 180 # number of minutes an AC processor can run before being terminated
ac_methods = ['l2gen'] # Atmospheric Correction methods to apply
apply_bounding_box = True

#===================================
#    Data Extraction Parameters
#===================================
extract_window = 2 # pixels to extract around the center pixel (e.g. 1 -> 3x3 window)

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
if  'MERIS_test_image' in datasets[0] or 'MOD_VI_test_image' in datasets[0]: 
    overwrite           = True
    ac_methods          = ['l2gen']  #['l2gen','acolite','aquaverse','polymer']

    remove_scene_folder = True 
    remove_L1_tile      = True
    fix_projection_Rrs  = False
    search_day_window   = 0 
    plot_products       = False
    extract_window      = 1 #3x3

    extra_cmd = {'l2gen': {'MOD' : {'aer_opt' : '-2','aer_wave_short' : '869','aer_wave_long'  : '2130','l2prod' : [ 'Rrs_nnn', 'rhos_nnn', 'Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},
                            'VI' : {'aer_opt' : '-2','aer_wave_short' : '868','aer_wave_long'  : '2258','l2prod' : [ 'Rrs_nnn', 'rhos_nnn','Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},
                         'MERIS' : {'aer_opt' : '-2','aer_wave_short' : '779','aer_wave_long'  :  '865','l2prod' : [ 'Rrs_nnn', 'rhos_nnn','Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},

                            },
                  'acolite': {},
                  'polymer': {},}
    timeseries_or_matchups = 'matchups'
    
if  'OLI_test_image' in datasets[0]  or 'MSI_test_image' in datasets[0] : 
    overwrite              = True
    ac_methods             = ['l2gen','acolite','polymer','aquaverse'] 
    timeseries_or_matchups = 'timeseries'
    remove_scene_folder    = False 
    remove_L1_tile         = False
    fix_projection_Rrs     = False
    #search_day_window      = 0 
    plot_products          = False
    plot_Rrs               = True
    extract_window         = 1 #3x3
    apply_bounding_box     = False
    search_day_window      = 0 if sensors[0] == 'OLI' else 120
    max_cloud_cover        = 20
    #scene_id               = 'T18SUG' if 'MSI' in sensors[0] else '014034' if 'OLI' in sensors[0] else '' #'019031' '044033' 020031 #T18SUG
    #scene_id               = tiles[sensors[0]][datasets[0].split('_')[-1]]

if  'OLCI_test_image' in datasets[0]:
    overwrite              = False
    ac_methods             = ['acolite']
    timeseries_or_matchups = 'timeseries'
    remove_scene_folder    = True
    remove_L1_tile         = True
    fix_projection_Rrs     = False
    plot_products          = False
    plot_Rrs               = True
    extract_window         = 1
    apply_bounding_box     = True
    search_day_window      = 0
    scene_id               = '20230710T153315'

#Checks
if search_day_window is None  and search_year_range is None and search_minute_window is None:
    search_day_window=0

if 'aquaverse' in ac_methods and 'OLI' not in sensors and 'MSI' not in sensors: assert(0)

if 'aquaverse' in ac_methods and 'MSI' in sensors: print('MSI Images after Jan 2022 will not successfully process with Aquaverse')
