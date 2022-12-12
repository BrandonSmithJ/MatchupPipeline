from subprocess import getoutput
from pathlib import Path 
import os

username = getoutput('whoami')
datasets = ['SaltonSea_2022']
sensors  = ['MOD']


#===================================
#         Path Definitions
#===================================
l2gen_path   = '/tis/m2cross/scratch/f004/roshea/Seadas_versions/Seadas_V2021_2/ocssw'#/tis/m2cross/scratch/f004/roshea/test_folder/SeaDAS_01_13_2022'#'/home/bsmith16/workspace/SeaDAS'#'/tis/m2cross/scratch/f002/bsmith/SeaDAS_01_13_2022' # '/tis/m2cross/scratch/f002/roshea/SeaDAS_06_13_2022/ocssw_R_2022_3' supports collection 2 imagery
polymer_path = '/home/bsmith16/AC/polymer/polymer-unknown/polymer' #Path(__file__).parent.joinpath('AC', 'L2_processing', 'polymer', 'polymer')
acolite_path = '/home/bsmith16/AC/acolite/acolite-20220222.0/acolite' #Path(__file__).parent.joinpath('AC', 'L2_processing', 'acolite', 'acolite')

scratch_path = Path(__file__).parent.parent.joinpath('SCRATCH')
insitu_path  = scratch_path.joinpath('Insitu') 
output_path  = scratch_path.joinpath('Gathered')


#===================================
#    Data Search Parameters
#===================================  
max_cloud_cover = 100 #Max cloud cover for downloading/processing.
search_day_window = 0


#===================================
# Atmospheric Correction Parameters
#===================================
ac_timeout = 30 # number of minutes an AC processor can run before being terminated
ac_methods = ['l2gen'] # Atmospheric Correction methods to apply

#===================================
#    Data Extraction Parameters
#===================================
extract_window = 2 # pixels to extract around the center pixel (e.g. 1 -> 3x3 window)


############################################## Plotting parameters ##########################################
#Max chl/PC values from MDN (sets values above to NaN to remove extreme outliers due to atm correction)
MAX_CHL=10000

MAX_PC=1000 
MIN_PC=0.1

############################################# Visual Parameters  ##########################################
#PLotPackage/Meta.py

#create_jobs parameters
save_nc = 1 #Saves atmospherically corrected netcdf
SAVE_NC_WITH_PRODUCT=False # if hasattr(config,'SAVE_NC_WITH_PRODUCT') else False
tf_2_products = "chl,tss,cdom"  #"chl,tss,cdom"
JOB_LIMIT = 2000

#Wether or not to plot imagery (False only loads Rrs, i.e. stops at the matchup pipeline)
PLOT_SCENES = True 

#Produce Geotiff or Netcdf, choose one (or neither)
GENEREATE_GEOTIFF = True #Forces FIX_PROJ to be true
GENERATE_NETCDF = False  #Only works with acolite

SHAPEFILE_MASK_FILE='HydroLAKES_polys_v10_shp/HydroLAKES_polys_v10_shp/HydroLAKES_polys_v10.shp'

#L2gen Specific config settings
L2GEN_only_Rrs = True #Only produces Rrs from l2gen 

#Acolite specific settings
USE_ACOLITE_DEFAULTS=True
ACOLITE_l2w_mask_water_parameters = False #True hard masks the Rrs if l2 flags are non-zero
ACOLITE_l2w_mask_negative_rhow = False    #True hard masks the Rrs if l2 data is negative
INCLUDE_SWIR=False                        #True includes SWIR (Bit 1) of acolite in the mask that is applied to imagery

#Output
verbose = False

SAVE_TO_SLURM=False #Save output to slurm output (even from pardees)



#Specify shapefile
#FLAG_MASK = True, Shapefile_MASK=False seems to calculate data at all locations
SHAPEFILE_MASK = True
FLAG_MASK = True       #Masks product with AtmCorr failure bitmask (Does not use SWIR mask of acolite, unless INCLUDE_SWIR = True)
APPLY_BITMASK=True     #Does not process MDN imagery with non-0 atmospheric bit masks
ALLOW_NEG=False        #



###################################################### LOCATION SPECIFIC OVERRIDES ##################################################
# if DATASET == 'Savannah_River_2015':    
#     SHAPEFILE_MASK_FILE="SRGT_shp_final/SRGT_shp_final.shp"

#     SENSORS  = ['OLI'] #'MSI',

# if DATASET == 'SavannahRiver_2015_test':    
#     SHAPEFILE_MASK_FILE="SRGT_shp_final/SRGT_shp_final.shp"
#     ATM_CORR = ['acolite','polymer'] #deprecated after 07/05/22

#     SENSORS  = ['OLI'] #'MSI',
    
# if  any(DATASET == loc for loc in ['Marion_reservoir','Marion_reservoir_2020','Marion_reservoir_2021']):  
#     SHAPEFILE_MASK_FILE='HydroLAKES_polys_v10_shp/HydroLAKES_polys_v10_shp/HydroLAKES_polys_v10.shp'
#     #ALLOW_NEG = False
#     # plotting min/maxes
#     CDOM_MIN_PLOT = 1e-1
#     CDOM_MAX_PLOT = 2e0
#     CHL_MIN_PLOT = 1e0
#     CHL_MAX_PLOT = 2e2
#     PC_MIN_PLOT = 1e0
#     PC_MAX_PLOT = 2e2
#     SENSORS = ['OLCI'] 
    
# if any(DATASET == loc for loc in ['Erie_2010', 'PacificNorthWest_2002_2012']):  
#     SHAPEFILE_MASK_FILE='HydroLAKES_polys_v10_shp/HydroLAKES_polys_v10_shp/HydroLAKES_polys_v10.shp'
#     tf_2_products = "chl"
#     GENEREATE_GEOTIFF=False
#     GENERATE_NETCDF=True  
#     USE_ACOLITE_DEFAULTS=False #Uses the same AtmCorr routines used for OLCI data.
#     SENSORS = ['MERIS']
    
# if DATASET == 'UtahLake':
#     INCLUDE_SWIR=True
#     FLAG_MASK = True
#     USE_ACOLITE_DEFAULTS=False
#     SHAPEFILE_MASK_FILE='Utah_DWQ_Assessed_Waters/DWQAssessedWaters.shp'
#     tf_2_products = "chl"
#     SENSORS = ['MSI','OLCI']         
    
# if  any(DATASET == loc for loc in ['Clear_Lake_California']):  
#     SHAPEFILE_MASK_FILE='HydroLAKES_polys_v10_shp/HydroLAKES_polys_v10_shp/HydroLAKES_polys_v10.shp'
#     SENSORS = ['OLCI'] 
#     APPLY_BITMASK=False
#     ALLOW_NEG = True

    
############################################## Checks and Folder creation ##############################################
#Check to see if combinations are allowed
# assert not (ALLOW_NEG and APPLY_BITMASK and 'acolite' in ATM_CORR), "ACOLITE bitmask will mask all negative values"
# assert not (not FLAG_MASK and GENERATE_NETCDF and 'acolite' in ATM_CORR), "FLAG MASK must be set true for GENERATE NETCDF and acolite"
# assert not (GENERATE_NETCDF and ('l2gen' in ATM_CORR or 'polymer' in ATM_CORR)), "GENERATE_NETCDF only works with acolite"
# # assert not ((SEADAS_ROOT != '/tis/m2cross/scratch/f002/roshea/SeaDAS_06_13_2022/ocssw_R_2022_3') and 'OLI' in SENSORS and 'l2gen' in ATM_CORR), "MUST SET SEADAS TO ocssw_R_2022_3 for OLI and l2gen (though this version does not support all sensors, so is not default)"


# #Print warnings
# if GENERATE_NETCDF and GENEREATE_GEOTIFF : print("The netcdf data may have inconsistencies on edges due to interpolation from FIX_PROJ forced by GENERATE_GEOTIFF")
#SHAPEFILE_MASK_FIle=SHAPEFILE_MASK_FILE #Deprecated after 06_18_2022

####################### Automatically generate folders if they do not exist (initialization) #########################

#Automatically assigned username specific directories
# UNIQUE_PREFIX  = username + '_'
# SCRATCH_FOLDER = USER_LOCATION.joinpath('SCRATCH_DEFAULT')

# if not os.path.isdir('/scratch'):
#     os.environ['SCRATCH'] = SCRATCH_FOLDER.as_posix()
#     print("Using Pardees Scratch", os.environ['SCRATCH'])
# else:
#     print("Using SLRM Scratch",os.environ['SCRATCH'])
    
# # BASE_PARDEES_PIPELINE = USER_LOCATION + 'Simultaneous/workspace/pipeline/' 
# LAUNCHED_TARS = OUTPUT_LOCATION.joinpath('Full_list_of_launched_job_tars.txt')



# SLURM_STORAGE_LOCATION      = USER_LOCATION.joinpath('SLURM_STORAGE')
# SLURM_STORAGE_LOCATION_LIST = SLURM_STORAGE_LOCATION.joinpath('complete_list.txt')

# SLURM_STORAGE_LOCATION_out = SLURM_STORAGE_LOCATION.joinpath('out')
# SLURM_STORAGE_LOCATION_err = SLURM_STORAGE_LOCATION.joinpath('err')

# #for pull_unique_tis_entries.py
# COMPLETED_PID_FOLDER = OUTPUT_LOCATION
# OUTPUT_TARS = OUTPUT_LOCATION.joinpath('output_tars')

# #If directories do not exist, it makes them 
# SLURM_STORAGE_LOCATION_out.mkdir(exist_ok=True, parents=True)
# SLURM_STORAGE_LOCATION_err.mkdir(exist_ok=True, parents=True)
# SCRATCH_FOLDER.mkdir(exist_ok=True, parents=True)

# #Automatically set the path variable, if it is not already available, so we can use homura in the create_jobs.sh
# try:
#     sys.path.index(BASE_PARDEES_PIPELINE) # Or os.getcwd() for this directory
# except ValueError:
#     sys.path.append(BASE_PARDEES_PIPELINE) # Or os.getcwd() for this directory
