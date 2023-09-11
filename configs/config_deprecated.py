from subprocess import getoutput
from pathlib import Path 
import os
import sys
username = getoutput('whoami') #SaltonSea_08_27_2016
datasets = ['OLI_test_image_Erie_2023']#['OLI_test_image_Erie_2023'] # MSI_test_image_20201017 # OLI_test_image_san_fran_2023 # 'MOD_VI_test_image' #MERIS_test_image #'Chesapeake_Bay_2016_2023'] #Erie_2021 #SaltonSea_2022 #SaltonSea_10_09_2022 #SaltonSea_shifted SaltonSea_1999_2022 GSL_02_13_2019 #GSL_High_quality
sensors  = ['OLI'] # 'MOD','VI'


#===================================
#         Path Definitions
#===================================
# MSI, OLI, MOD (OLI Collection 2): '/home/roshea/SeaDAS/SeaDAS_V2022_3/ocssw'
# VI and MERIS: '/tis/m2cross/scratch/f004/roshea/Seadas_versions/Seadas_V2022_3/ocssw'
# OLCI

l2gen_path     = '/tis/m2cross/scratch/f004/roshea/Seadas_versions/Seadas_V2022_3/ocssw' #'/tis/m2cross/scratch/f004/roshea/Seadas_versions/Seadas_V2022_3/ocssw' #'/tis/m2cross/scratch/f004/roshea/Seadas_versions/Seadas_8_2_0/SeaDAS/ocssw' # '/tis/m2cross/scratch/f004/roshea/Seadas_versions/Seadas_V2022_0/ocssw' #/tis/m2cross/scratch/f004/roshea/Seadas_versions/Seadas_V2021_2/ocssw'#/tis/m2cross/scratch/f004/roshea/test_folder/SeaDAS_01_13_2022'#'/home/bsmith16/workspace/SeaDAS'#'/tis/m2cross/scratch/f002/bsmith/SeaDAS_01_13_2022' # '/tis/m2cross/scratch/f002/roshea/SeaDAS_06_13_2022/ocssw_R_2022_3' supports collection 2 imagery
if 'OLI' or 'MSI'  in sensors:
    l2gen_path = '/home/roshea/SeaDAS/SeaDAS_V2022_3/ocssw'
if 'MOD' in sensors:
    #l2gen_path = '/data/roshea/SCRATCH/AC/seadas_2022_3/ocssw'
    l2gen_path =  '/data/roshea/SCRATCH/AC/ocssw'
    #l2gen_path = '/tis/m2cross/scratch/f004/roshea/Seadas_versions/Seadas_V2022_3_updated_LUTs/ocssw'
    
polymer_path   = '/home/bsmith16/AC/polymer/polymer-v4.16.1/polymer-v4.16.1/polymer'#'/home/bsmith16/AC/polymer/polymer-unknown/polymer' #Path(__file__).parent.joinpath('AC', 'L2_processing', 'polymer', 'polymer')
acolite_path   = '/home/roshea/AC/acolite/acolite-20221114.0/acolite' #'/home/bsmith16/AC/acolite/acolite-20220222.0/acolite' #Path(__file__).parent.joinpath('AC', 'L2_processing', 'acolite', 'acolite')
aquaverse_path = '/home/roshea/matchup_pipeline_development/pipeline/AC/L2_processing/aquaverse'

stream_backend_path = '/tis/m2cross/scratch/f002/wwainwr1/stream/backend'
stream_env_path     = '/tis/m2cross/scratch/f002/wwainwr1/venv/bin/activate'

scratch_path   = Path(f'/data/{username}').joinpath('SCRATCH') #Path(__file__).parent.parent.
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
ac_timeout = 120 # number of minutes an AC processor can run before being terminated
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
if  'SaltonSea' in datasets[0] or 'GSL' in datasets[0]: 
    extra_cmd = {'l2gen': {'MOD' : {'aer_wave_short' : '1240','aer_wave_long'  : '2130','resolution':'500','l2prod' : [ 'Rrs_nnn', 'rhos_nnn', 'Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},
                            'VI' : {'aer_wave_short' : '1240','aer_wave_long'  : '2257','resolution':'500','l2prod' : [ 'Rrs_nnn', 'rhos_nnn','Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},
                            },
                  'acolite': {},
                  'polymer': {},}
    overwrite=True
    remove_scene_folder=True
    remove_L1_tile=True
    if 'SaltonSea_1999_2022' == datasets[0] or 'GSL_1999_2022' == datasets[0]:
        search_year_range = 24 
    else:
        search_day_window = 0
    fix_projection_Rrs=True

if  'AugGloria' in datasets[0]: 
    search_day_window=2 #30*60 #h*m
    sensors  = ['OLI']

# if  'Erie' in datasets[0] or 'Chesapeake_Bay' in datasets[0]: 
#     overwrite=True
#     ac_methods = ['l2gen','acolite']  #,'l2gen',
#     # search_year_range = 8
#     remove_scene_folder=False #Should be false
#     remove_L1_tile=False
#     fix_projection_Rrs=True
#     search_day_window=0 #91

if  'MERIS_test_image' in datasets[0] or 'MOD_VI_test_image' in datasets[0]: 
    overwrite           = True
    ac_methods          = ['l2gen']  #,'l2gen','acolite','mdn-ac','polymer'

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
    ac_methods             = ['l2gen','acolite','polymer','aquaverse'] #['aquaverse']#['l2gen','acolite','polymer','aquaverse'] # 'l2gen','acolite','polymer', # 'l2gen','acolite','polymer, 'aquaverse'  #,'l2gen','acolite','mdn-ac','polymer' #'mdn-ac',
    timeseries_or_matchups = 'timeseries'
    remove_scene_folder    = False 
    remove_L1_tile         = False
    fix_projection_Rrs     = False
    #search_day_window      = 0 
    plot_products          = False
    plot_Rrs               = True
    extract_window         = 1 #3x3
    apply_bounding_box     = False
    search_day_window      = 2000
    max_cloud_cover        = 5
    scene_id               = 'T18SUG' if 'MSI' in sensors[0] else '019031' if 'OLI' in sensors[0] else '' #'044033' 020031 #T18SUG

if  'Sundar_dataset' in datasets[0] or 'MOD_dataset_chris' in datasets[0] or 'MOD_test_bahamas' in datasets[0] : 
    overwrite           = False
    ac_methods          = ['l2gen','polymer']  #,'l2gen',
    # search_year_range = 8
    remove_scene_folder = False #Should be false
    remove_L1_tile      = False
    fix_projection_Rrs  = False
    #search_day_window   = 0 #91
    search_minute_window = 720
    plot_products       = True
    extract_window      = 1 #3x3
    timeseries_or_matchups = 'timeseries'

    extra_cmd = {'l2gen': {'MOD' : {'aer_opt' : '-2','aer_wave_short' : '869','aer_wave_long'  : '2130',}, #,'l2prod' : [ 'Rrs_nnn', 'rhos_nnn', 'Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]}
                            'VI' : {'aer_opt' : '-2','aer_wave_short' : '862','aer_wave_long'  : '2257','l2prod' : [ 'Rrs_nnn', 'rhos_nnn','Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},
                         'MERIS' : {'aer_opt' : '-2','aer_wave_short' : '779','aer_wave_long'  :  '865','l2prod' : [ 'Rrs_nnn', 'rhos_nnn','Rrs_unc_vvv','latitude', 'longitude', 'l2_flags','chlor_a',]},

                            },
                  'acolite': {},
                  'polymer': {},}
    
if search_day_window is None  and search_year_range is None and search_minute_window is None:
    search_day_window=0

if 'aquaverse' in ac_methods and 'OLI' not in sensors and 'MSI' not in sensors: assert(0)

