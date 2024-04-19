#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 09:56:09 2021

Function to process timeseries of geotiff imagery
"""

import datetime, warnings, os,pickle 
from datetime import timedelta

# from ..MDNs.MDN_MODIS_VIIRS_OLCI.plot_utils import add_identity, add_stats_box
# from ..MDNs.MDN_MODIS_VIIRS_OLCI.metrics import slope, sspb, mdsa, count , rmsle

import matplotlib             as mpl
mpl.use('agg')
mpl.rcParams['figure.dpi'] = 600
mpl.rcParams['text.usetex'] = True
#mpl.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}'] 

import matplotlib.pyplot      as plt
plt.rcParams["font.weight"] = "bold"
plt.rcParams["axes.labelweight"] = "bold"

from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
import matplotlib.colors      as mcolors
import matplotlib.ticker      as ticker
import matplotlib.patheffects as pe 
import seaborn                as sns

if os.name == 'nt':
    mpl.rc('font', family='Arial')
else:  
    mpl.rc('font', family='DejaVu Sans')

import pandas as pd
import numpy as np
from pathlib import Path
#from .utils import convert_CyAN, default_dd, load_insitu, is_float , find_filenames, align_matchups, pull_timeseries, extract_datetime, adjust_cdom, group_prod_monthly


def default_dd(d={}, f=lambda k: k):
	''' Helper function to allow defaultdicts whose default value returned is the queried key '''

	class key_dd(d):
		''' DefaultDict which allows the key as the default value '''
		def __missing__(self, key):
			if self.default_factory is None:
				raise KeyError(key)
			val = self[key] = self.default_factory(key)
			return val 
	return key_dd(f, d)

def find_filenames(sensor, basefile,atmospheric_correction):
    final_filenames_list = []
    os.chdir(basefile+'/'+sensor)
    file_list = sorted(Path().resolve().rglob("*"+atmospheric_correction+"*.tif"))
    #print(file_list)
    os.chdir(basefile)

    return file_list

# Function to calculate datetime from input filename
def extract_datetime(fname,sensor,index = 1):
    
    if sensor == 'MOD': datetime_convertor = '%Y%j%H%M%S'
    if sensor in [ 'VI','OLCI']: datetime_convertor = '%Y%m%dT%H%M%S'
    if sensor == 'OLI': 
        datetime_convertor = '%Y%m%d'
        index = 3
    if sensor == 'MSI':
        datetime_convertor = '%Y%m%dT%H%M%S'
        index = 2
    if sensor == 'MOD':
        out = [datetime.datetime.strptime(str(file_name[1:]),datetime_convertor) if type(file_name) == str else datetime.datetime.now() for file_name in fname ]
    else:
        out = [datetime.datetime.strptime(str(file_name).split('_')[index],datetime_convertor) if type(file_name) == str else datetime.datetime.now() for file_name in fname ]
    return out #[datetime.datetime.strptime(file.split('_')[index],datetime_convertor) for file in fname]

def load_csv(csv_path,header=0):
    csv = pd.read_csv(csv_path,header=header)
    #csv = csv.dropna()
    return csv
    
def pretty_text(product,ylabel="",xlabel=""):
	product_labels = {
		'chla' : 'Chl\\textit{a}',
		'aph' : '\\textit{a}_{ph}',
		'tss' : 'TSS',
		'cdom': '\\textit{a}_{CDOM}(440)',
        'pc'  : 'PC',
        'secchi'  : 'Secchi',

	}
	
	product_units = {
		'chla' : '[mg m^{-3}]',
		'tss' : '[g m^{-3}]',
		'aph' : '[m^{-1}]',
		'cdom': '[m^{-1}]',
        'pc' : '[mg m^{-3}]',
        'secchi' : '[m]',

	}
    
	estimate_label = ylabel
	x_pre  = xlabel
	y_pre  = estimate_label.replace('-', '\\textbf{-}')
	space  = "\:"
	plabel = f'{product_labels[product]}{space} {product_units[product]}'
	xlabel = fr'$\mathbf{{{x_pre} {plabel}}}$'
	ylabel = fr'$\mathbf{{{y_pre}}}$'+'' +fr'$\mathbf{{ {plabel}}}$'
    
	return xlabel,ylabel
    

warnings.filterwarnings("ignore",category=DeprecationWarning)

####################################
#Assign date time based on scene id
input_directory = Path("/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH")
gathered_path   = input_directory.joinpath("Gathered/")
insitu_path     = input_directory.joinpath("Insitu").joinpath("Insitu")
save_path       = input_directory.joinpath("Plots")

product_rename_dictionary = {'Chla'  : 'chla',
                             'Zsd'   : 'secchi',
                             'TSS'   : 'tss', 
                             'chla'  : 'Chla',
                             'secchi': 'Zsd' ,
                             'tss'   : 'TSS',
                             'CDOM'  : 'cdom',}
# os.mkdir(save_path)
#load data from the matchups files into a very standardized format
def load_gathered_data(gathered_path,folder_names=[],products=[],overwrite=True):
    #identify all folders in gathered path
    sensors        = ["MOD","MSI","OLI"] #,"OLI","MSI"]
    atm_corrs      = ["aquaverse","l2gen"]
    datasets       = ["GSL_1999_2022","OLI_test_image_MS_AC","OLI_test_image_CB_subset","OLI_test_image_CB_ET42_EE31","OLI_test_image_Boston_timeseries","OLI_test_image_Erie_stations","OLI_test_image_Damariscotta_1",'OLI_test_image_Damariscotta_2',"OLI_test_image_Oyster_farm","OLI_test_image_Honga_TS_1","OLI_test_image_Honga_TS_2","OLI_test_image_Wachusett_reservoir_timeseries","OLI_test_image_Quabbin_reservoir_timeseries"] #,"OLI_test_image_Honga_TS_1","OLI_test_image_Honga_TS_2"
    datasets = ['OLI_test_image_Quabbin_reservoir_timeseries']#,"OLI_test_image_Wachusett_reservoir_timeseries"] #["OLI_test_image_MS_AC"]#["OLI_test_image_Honga_TS_1"]
    ######
    #datasets = ["OLI_test_image_Erie_stations"]
    gathered_data     = {}
    gathered_data_uid = {}
    unique_uids       = {}
    products        = ['Chla','TSS','CDOM','Zsd'] #['Chla','Zsd','TSS']
    for dataset in datasets:
        gathered_data[dataset]     = {}
        for sensor in sensors:

            gathered_data[dataset][sensor] = {}
            for atm_corr in atm_corrs:
                gathered_data[dataset][sensor][atm_corr] = {}
                output_folders = gathered_path.resolve().glob(f"{dataset}/{sensor}/{atm_corr}/Matchups.csv")             
                for output_folder in output_folders:
                    print(output_folder)
                    loaded_csv                               = load_csv(output_folder)
                    gathered_data[dataset][sensor][atm_corr] = loaded_csv
                    scene_ids                                = gathered_data[dataset][sensor][atm_corr]['scene_id'].values
                    scene_datetimes                          = extract_datetime(scene_ids,sensor)
                    gathered_data[dataset][sensor][atm_corr]['datetime_from_scene_id'] = scene_datetimes

                    for product in products:
                        gathered_data[dataset][sensor][atm_corr][product_rename_dictionary[product]] = gathered_data[dataset][sensor][atm_corr][product] if product in gathered_data[dataset][sensor][atm_corr].keys() else  np.empty(len(gathered_data[dataset][sensor][atm_corr]))*np.nan
                        #gathered_data[dataset][sensor][atm_corr][product_rename_dictionary[product]+'_max'] = gathered_data[dataset][sensor][atm_corr][product+'_max']
                        #gathered_data[dataset][sensor][atm_corr][product_rename_dictionary[product]+'_min'] = gathered_data[dataset][sensor][atm_corr][product+'_min']
                    if 'uid' in gathered_data[dataset][sensor][atm_corr].keys() and ('timeseries' in dataset or 'Erie' in dataset or 'CB' in dataset or 'MS_AC' or 'GSL'):

                        unique_uids[dataset]            = gathered_data[dataset][sensor][atm_corr].uid.unique()
                        dataframe_split_by_uid          = {uid : pd.DataFrame() for uid in unique_uids[dataset]}
                        for uid in dataframe_split_by_uid.keys():
                            dataframe_split_by_uid[uid] = gathered_data[dataset][sensor][atm_corr][:][gathered_data[dataset][sensor][atm_corr].uid == uid]

                    else:
                        uid                                 = 'Undefined'
                        unique_uids[dataset]                = [uid]
                        dataframe_split_by_uid              = {uid : pd.DataFrame() for uid in unique_uids[dataset]}
                        dataframe_split_by_uid[uid]         = gathered_data[dataset][sensor][atm_corr][:]

                    gathered_data[dataset][sensor][atm_corr] = dataframe_split_by_uid 



    for dataset in datasets:
        gathered_data_uid[dataset] = {}
        for uid in unique_uids[dataset]:
            gathered_data_uid[dataset][uid] = {}
            for sensor in sensors:
                gathered_data_uid[dataset][uid][sensor] = {}
                for atm_corr in atm_corrs:
                    #if uid in gathered_data[dataset][sensor][atm_corr].keys():

                    gathered_data_uid[dataset][uid][sensor][atm_corr] = gathered_data[dataset][sensor][atm_corr][uid] if uid in gathered_data[dataset][sensor][atm_corr].keys() else {atm_corr:{}}
                    

    # save the loaded dictionary to a pickle file 
    #return a dictionary of data from all of the folders
    return gathered_data_uid

insitu_data_dictionary = {"OLI_test_image_Oyster_farm"                     : ['',0],
                          "OLI_test_image_Honga_TS_1"                      : ["Honga_insitu_1",7],
                          "OLI_test_image_Honga_TS_2"                      : ["Honga_insitu_2",7], 
                          "OLI_test_image_Damariscotta_1"                  : ["lowerDRE_full",0],
                          "OLI_test_image_Damariscotta_2"                  : ["upperDRE_full",0],
                          "OLI_test_image_Wachusett_reservoir_timeseries"  : ["Wachusett",0],
                          "OLI_test_image_Quabbin_reservoir_timeseries"    : ["Quabbin",0],
                          "OLI_test_image_Erie_stations"                   : ["WLE_Summary_2008_2019_Nima",1],
                          "OLI_test_image_Boston_timeseries"               : ["boston_combined",0],
                          "OLI_test_image_CB_ET42_EE31"                    : ["CPB_WaterQualityWaterQualityStation",0],
                          "OLI_test_image_CB_subset"                       : ["CPB_WaterQualityWaterQualityStation",0],
                          "OLI_test_image_MS_AC"                           : ["",0],
                          "GSL_1999_2022"                                  : ["",0],
                          }

# title_dictionary  

#filter strs and nans
def clean_data(insitu_data_product):
   #print(insitu_data_product)
   return pd.to_numeric(insitu_data_product,errors="coerce")

def load_insitu_data(insitu_path,insitu_data_dictionary):
    insitu_data={}
    for dataset in insitu_data_dictionary.keys():
        insitu_filename = insitu_data_dictionary[dataset][0]
        insitu_header_location = insitu_data_dictionary[dataset][1]
        output_folders = insitu_path.resolve().glob(f"{insitu_filename}.csv")             
        for output_folder in output_folders:
            print(output_folder)
            
            insitu_data[dataset] = load_csv(output_folder,header=insitu_header_location)

            if 'date' in insitu_data[dataset].keys() and 'Time' in insitu_data[dataset].keys():
                insitu_data[dataset]['date'] =  insitu_data[dataset]['date'].astype('str')
                insitu_data[dataset]['Time'] =  insitu_data[dataset]['Time'].astype('str')

                datetime_array = insitu_data[dataset]['date'].values +'T' + insitu_data[dataset]['Time'].values
                datetime_convertor = '%m/%d/%YT%H:%M:%S'
                datetime_array = [datetime.datetime.strptime(file_i,datetime_convertor)  if 'nan' not in file_i else np.nan for file_i in datetime_array ]
                insitu_data[dataset]['datetime'] = datetime_array
            for product in ['chl','tss','cdom','pc','secchi']:
                if product in insitu_data[dataset].keys():
                    insitu_data[dataset][product] = clean_data(insitu_data[dataset][product]) 
    #iterate through in situ data
     
    return insitu_data

def average_output(datetimes,products,products_max=None,products_min=None):
    data = pd.DataFrame()
    import seaborn as sns

    datetimes = [datetime.datetime.strptime(datetime.datetime.strftime(date_time, '%Y-%m-%d'),'%Y-%m-%d') for date_time in datetimes] 
    data['datetimes']     = datetimes
    data['products']      = products
    if products_max is not None and products_min is not None:
        data['products_max']  = products_max
        data['products_min']  = products_min
    data                  = data.set_index('datetimes')
    data                  = data.groupby(level=0)
    if products_max is not None and products_min is not None:
        grouped_data          = data.agg({'products':'mean','products_max':'mean','products_min':'mean'})
    else:
        grouped_data          = data.agg({'products':'mean',})
    data                  = grouped_data.reindex(pd.date_range('01-01-2015','02-02-2024'),fill_value=np.nan)
    data['30day_average'] = data.products.rolling(window=30,min_periods=1,center=True,win_type='gaussian').mean(std=7)
    data['30day_std'] = data.products.rolling(window=30,min_periods=1,center=True,win_type='gaussian').std(std=7)
    data['1day_average']  = data.products.rolling(window=1,min_periods=1,center=True,win_type='gaussian').mean(std=1)
    #data['datetimes']     = data.index
    
    if products_max is not None and products_min is not None:
            #grouped_data          = data.agg({'products_max':'mean'})
            #data                  = grouped_data.reindex(pd.date_range('01-01-2015','02-02-2024'),fill_value=np.nan)
            data['30day_average_max'] = data.products_max.rolling(window=30,min_periods=1,center=True,win_type='gaussian').mean(std=7)
            
            #grouped_data          = data.agg({'products_min':'mean'})
            #data                  = grouped_data.reindex(pd.date_range('01-01-2015','02-02-2024'),fill_value=np.nan)
            data['30day_average_min'] = data.products_min.rolling(window=30,min_periods=1,center=True,win_type='gaussian').mean(std=7)

    data['datetimes']     = data.index

    #data['1day_average']  = data.products.rolling(window=1,min_periods=1,center=True,win_type='gaussian').mean(std=1) 


    return data

def plot_products(gathered_data,insitu_data,save_location,products=['chla','tss','secchi','cdom'],plot_matchups=0):
    markers       = {'OLI' : 'o',
                     'MSI' : 'X',
                     'MOD' : '.',}

    alphas        = [0.8,0.35]
    colors        = {'MSI': {'aquaverse': 'xkcd:red',    'acolite': 'xkcd:red',   'l2gen': 'xkcd:red',   'polymer':'xkcd:red',    'cyan': 'xkcd:teal'},
		     'OLI': {'aquaverse': 'xkcd:violet', 'acolite': 'xkcd:violet','l2gen': 'xkcd:violet','polymer':'xkcd:violet', 'cyan': 'xkcd:teal'},
                     'MOD': {'aquaverse': 'xkcd:blue',   'acolite': 'xkcd:blue',  'l2gen': 'xkcd:blue',  'polymer':'xkcd:blue',   'cyan': 'xkcd:teal'},}    #[ 'k','xkcd:red']
    
    colors_insitu = 'xkcd:black'
    
    n_rows_fig    = len(products)
    n_cols_fig    = 1
    
    limits        = {
                    'chla'    : [0.1,100],
                    'tss'     : [0.1,100],
                    'secchi'  : [0.1,10],
                    'cdom'    : [0.05,5],
                    }
    
    limits_eutrophic = {
                    'chla'    : [1,1000],
                    'tss'     : [1,100],
                    'secchi'  : [0.1,10],
                    'cdom'    : [0.05,5],
                    }

    sensor_label   = {"MSI":"Sentinel-2",
                      "OLI":"Landsat-8/9",
                      "MOD":"MODIS"}

    atm_corr_label = {'aquaverse':'Aquaverse','l2gen':'L2gen'}
    plot_scatter=False
    plot_insitu_average=False
    for dataset in gathered_data.keys():
        #if True:
        for uid in gathered_data[dataset].keys():
            fig, axs      = plt.subplots(nrows=n_rows_fig, ncols=n_cols_fig,
                             figsize=(int(24*n_rows_fig/4), 16), sharex=True, sharey=False)#24,9
            years         = YearLocator()
            months        = MonthLocator()
            years_format  = DateFormatter('%Y')
            months_format = DateFormatter('%b')
            plot_iterator = 0
            for sensor in gathered_data[dataset][uid].keys():
            #fig, axs      = plt.subplots(nrows=n_rows_fig, ncols=n_cols_fig,
            #                figsize=(int(24*n_rows_fig/4), 12), sharex=True, sharey=False)#24,9 
                for atm_corr in gathered_data[dataset][uid][sensor].keys():
                    if type(uid) == float:
                        if np.isnan(uid):
                        #print('Dataset 5')
                            continue
                    lat = gathered_data[dataset][uid][sensor][atm_corr]['lat'].values[0] if 'lat' in gathered_data[dataset][uid][sensor][atm_corr].keys() else ''
                    lon = gathered_data[dataset][uid][sensor][atm_corr]['lon'].values[0] if 'lon' in gathered_data[dataset][uid][sensor][atm_corr].keys()  else ''
                    plot_iterator=plot_iterator+1
                    for i,ax in enumerate(axs):
                        product = products[i]
                        if (product == 'chla' or 'Boston' in dataset) and sensor == 'OLI': 
                            ax.plot([0],[0.001],label=f'{sensor_label[sensor]} {atm_corr_label[atm_corr]} 30-day average' if i == 0 else None, linewidth=2,color=colors[sensor][atm_corr],zorder=103)
                            continue 
                        

                        if product in      gathered_data[dataset][uid][sensor][atm_corr].keys():
                            datetimes_in = gathered_data[dataset][uid][sensor][atm_corr]['datetime_from_scene_id']
                            products_in  = gathered_data[dataset][uid][sensor][atm_corr][product]
                            products_max_in = gathered_data[dataset][uid][sensor][atm_corr][product]+1#[product+'_max']
                            products_min_in = gathered_data[dataset][uid][sensor][atm_corr][product]-1#[product+'_min']

                            def filter_products(datetimes_in,products_in,products_max_in,products_min_in):
                                min_limit = -1
                                if 'Honga_TS_1' in dataset: min_limit = 0.1
                                datetime_filtered = [ datetime.datetime.strptime(datetime.datetime.strftime(date_time, '%Y-%m-%d'),'%Y-%m-%d') for date_time,product,product_max,product_min in zip(datetimes_in,products_in,products_max_in,products_min_in) if product > min_limit]
                                product_filtered = [ product for datetime,product,product_max,product_min in zip(datetimes_in,products_in,products_max_in,products_min_in) if product > min_limit ]
                                product_max_filtered = [ product_max for datetime,product,product_max,product_min in zip(datetimes_in,products_in,products_max_in,products_min_in) if product > min_limit ]
                                product_min_filtered = [ product_min for datetime,product,product_max,product_min in zip(datetimes_in,products_in,products_max_in,products_min_in) if product > min_limit ]
                                return datetime_filtered, product_filtered, product_max_filtered, product_min_filtered

                            datetimes_filtered, products_filtered, products_max_filtered, products_min_filtered = filter_products(datetimes_in,products_in,products_max_in,products_min_in)
                        #Insitu data
                        if dataset in insitu_data.keys():
                            if product in insitu_data[dataset].keys():
                                if 'station' in insitu_data[dataset].keys():
                                    station_id = uid.split('_')[-1]
                                    insitu_dataset = insitu_data[dataset][insitu_data[dataset]['station']==station_id]
                                    if 'depth' in insitu_dataset.keys():

                                        print(station_id,"FILTERING BY DEPTH < 3 m",sum(insitu_dataset['depth']<3),len(insitu_dataset))
                                        insitu_dataset = insitu_dataset[insitu_dataset['depth']<3]
                                        #print("FILTERING BY DEPTH < 1.1 m",sum(insitu_dataset['depth']<1.1),sum(insitu_dataset),max(insitu_dataset['depth']))
                                    insitu_dataset.reset_index(inplace=True)
                                else:
                                    insitu_dataset = insitu_data[dataset]
                                data_ins = average_output(insitu_dataset['datetime'],insitu_dataset[product])

                                #if plot_matchups<2: ax.scatter(insitu_dataset['datetime'], insitu_dataset[product],color='xkcd:dodger blue',marker='*',alpha=0.9,zorder = 99,label=f'in situ',edgecolors='none',s=80)
                                print("Insitu",dataset,uid,sensor,atm_corr,product)
                                if plot_matchups<2 and plot_iterator==1 and plot_insitu_average: sns.lineplot(x = 'datetimes',y='30day_average',data=data_ins,label=f'In-situ 30-day average',ax=ax, linewidth=2,color=colors_insitu,zorder=101)
                                 
                                if plot_matchups<2 and plot_iterator==1 and plot_insitu_average: ax.fill_between(data_ins['datetimes'], data_ins['30day_average']-0.3*data_ins['30day_average'],data_ins['30day_average']+0.3*data_ins['30day_average'], alpha=.3,color = colors_insitu)
                                if plot_iterator==1: ax.scatter(insitu_dataset['datetime'], insitu_dataset[product],color=colors_insitu,alpha=0.7,zorder = 102,label=f'In-situ')
                                ##if plot_matchups<2: sns.lineplot(x = 'datetimes',y='30day_average',data=data_ins,label=f'30-day average in situ',ax=ax, linewidth=2,color='xkcd:vivid blue',zorder=101)
                                #sns.lineplot(x = 'datetimes',y='1day_average',data=data_ins,label=f'30-day average in situ',ax=ax, linewidth=2,color='xkcd:vivid blue')
                                #gathered_data[dataset][uid][sensor][atm_corr]['datetime_from_scene_id']
                                #min_dt = [min(gathered_data[dataset][uid][sensor][atm_corr]['datetime'], key=lambda d: abs(d - item)) for item in insitu_dataset['datetime']]
                                #print(min_dt)
                                
                                def identify_matchups(datetimes_in,datetimes_in_insitu):
                                    min_locations_gathered = []
                                    min_locations_insitu   = []

                                    for min_location_insitu,insitu_datetime in enumerate(datetimes_in_insitu):
                                        abs_diff              = abs(datetimes_in-insitu_datetime)
                                        min_location_gathered = np.argmin(abs_diff)

                                        min_diff_gathered     = abs_diff[min_location_gathered]
                                        if min_diff_gathered < datetime.timedelta(1):
                                            min_locations_gathered.append(min_location_gathered)
                                            min_locations_insitu.append(  min_location_insitu)
                                    return min_locations_gathered, min_locations_insitu
                                if product in      gathered_data[dataset][uid][sensor][atm_corr].keys():
                                    if not len(products_filtered): continue
                                    matchups_gathered, matchups_insitu = identify_matchups(pd.Series(datetimes_filtered),insitu_dataset['datetime'])
                                    if plot_matchups>0: ax.scatter([datetimes_filtered[i] for i in matchups_gathered],[products_filtered[i] for i in matchups_gathered],color=colors[sensor][atm_corr],marker='o',alpha=0.9,zorder = 100,label=f'Matchups: {sensor_label[sensor]} {atm_corr_label[atm_corr]}',s=60,edgecolors='none')
                                    if plot_matchups>0: ax.scatter([insitu_dataset['datetime'][i] for i in matchups_insitu],[insitu_dataset[product][i] for i in matchups_insitu],color='xkcd:vivid blue',marker=markers[sensor],alpha=0.9,zorder = 100,label=f'Matchups: in situ',s=60,edgecolors='none')

                        if product in      gathered_data[dataset][uid][sensor][atm_corr].keys():
                            print("Gathered",dataset,uid,sensor,atm_corr,product)

                            #datetimes_in = gathered_data[dataset][uid][sensor][atm_corr]['datetime_from_scene_id']
                            #products_in  = gathered_data[dataset][uid][sensor][atm_corr][product]

                            #def filter_products(datetimes_in,products_in):
                            #    datetime_filtered = [ datetime.datetime.strptime(datetime.datetime.strftime(date_time, '%Y-%m-%d'),'%Y-%m-%d') for date_time,product in zip(datetimes_in,products_in) if product > -1]
                            #    product_filtered = [ product for datetime,product in zip(datetimes_in,products_in) if product > -1 ]
                            #    return datetime_filtered, product_filtered

                            #datetimes_filtered, products_filtered = filter_products(datetimes_in,products_in)

                            #def identify_matchups(datetimes_in,datetimes_in_insitu): 
                            #    min_locations_gathered = []
                            #    min_locations_insitu   = []

                             #   for min_location_insitu,insitu_datetime in enumerate(datetimes_in_insitu):
                            #        abs_diff              = abs(datetimes_in-insitu_datetime)
                            #        min_location_gathered = np.argmin(abs_diff)
                            #        
                            #        min_diff_gathered     = abs_diff[min_location_gathered]
                            #        if min_diff_gathered < datetime.timedelta(1):
                            #            min_locations_gathered.append(min_location_gathered)
                            #            min_locations_insitu.append(  min_location_insitu)
                            #    return min_locations_gathered, min_locations_insitu

                            #matchups_gathered, matchups_insitu = identify_matchups(datetimes_in,insitu_dataset['datetime'])


                            data = average_output(datetimes_filtered,products_filtered,products_max_filtered,products_min_filtered)
                            #sns.lineplot(x = 'datetimes',y='products',data=data,label=f'sns {sensor} {atm_corr}',ax=ax)
                            if plot_matchups<2: sns.lineplot(x = 'datetimes',y='30day_average',data=data,label=f'{sensor_label[sensor]} {atm_corr_label[atm_corr]} 30-day average' if i == 0 else None,ax=ax, linewidth=2,color=colors[sensor][atm_corr],zorder=103)
                            
                            #if plot_matchups<2: sns.lineplot(x = 'datetimes',y='30day_std',data=data,label=f'30-day std {sensor} {atm_corr}' if i == 0 else None,ax=ax, linewidth=2,color=colors[sensor][atm_corr],zorder=103)
                            if plot_matchups<2: ax.fill_between(data['datetimes'], data['30day_average']-0.6*data['30day_average'],data['30day_average']+0.6*data['30day_average'], alpha=.3,color = colors[sensor][atm_corr])
                            #if plot_matchups<2: ax.fill_between(data['datetimes'], data['30day_average_min'],data['30day_average_max'], alpha=.3,color = colors[sensor][atm_corr])


                            #if plot_matchups<2: ax.fill_between(data['datetimes'], data['30day_average']-data['30day_std'],data['30day_average']+data['30day_std'], alpha=.3,color = colors[sensor][atm_corr])

                            #if plot_matchups<2: ax.plot(data['datetimes'].values, data['30day_average'].values,'k',linewidth=3)
                            if plot_matchups<2 and plot_scatter: ax.scatter(datetimes_filtered, products_filtered,color=colors[sensor][atm_corr],marker=markers[sensor],alpha=0.5,zorder = 100,label=f'{sensor_label[sensor]} {atm_corr_label[atm_corr]}',s=60,edgecolors='none')
                            
                            #ax.scatter([datetimes_filtered[i] for i in matchups_gathered],[products_filtered[i] for i in matchups_gathered],color='m',marker=markers[sensor],alpha=0.75,zorder = 100,label=f'{sensor} {atm_corr}',s=60,edgecolors='none')
                            #ax.scatter([insitu_dataset['datetime'][i] for i in matchups_insitu],[insitu_dataset[product][i] for i in matchups_insitu],color='c',marker=markers[sensor],alpha=0.75,zorder = 100,label=f'{sensor} {atm_corr}',s=60,edgecolors='none')     
                            #datetimes_out, product_out= zip(*sorted(zip(datetimes_filtered,  products_filtered)))
                                    #ax.plot(datetimes_out, product_out,color=colors[sensor][atm_corr],alpha=1,zorder = 97,linewidth=2)
                            #grouped_product       = pd.DataFrame(data=product_out)
                            #grouped_product.index = datetimes_out
                            #monthly_average       = grouped_product.groupby(pd.Grouper(freq='M')).median()
                            #ax.plot(monthly_average.index.to_pydatetime(),monthly_average.values,color=colors[sensor][atm_corr],alpha=1,zorder = 97,linewidth=2)

                        # Formatting
                        ax.set_xlim(pd.Timestamp('2015-01-01 00:00:00'), pd.Timestamp('2024-01-01 00:00:00'))
                        ax.xaxis.set_major_locator(years)
                        ax.xaxis.set_major_formatter(years_format)
                        ax.xaxis.set_minor_locator(months)
                        ax.xaxis.set_minor_formatter(months_format)
                        ax.tick_params(axis='x', which='major', labelsize=16,pad=32)
                        ax.tick_params(axis='y', which='major', labelsize=16)
                        ax.tick_params(axis='x'   , which='minor', labelsize=14)
    
                        plt.setp(ax.xaxis.get_minorticklabels(), rotation = 90)
                        plt.setp(ax.xaxis.get_majorticklabels(), fontweight='bold')
                        plt.setp(ax.yaxis.get_majorticklabels(), fontweight='bold')
                        ax.set_yscale('log')
                        if 'MS_AC' in dataset:
                            ax.set_ylim(limits_eutrophic[product])
                        else:
                            ax.set_ylim(limits[product])
                        ax.set_ylabel(f'{pretty_text(product)[1]}',fontsize=20)
                        ax.grid(True,which='major',color = 'xkcd:slate grey')
                        ax.grid(True,which='minor',color = 'xkcd:light grey')
                        ax.set_axisbelow(True)
                        if i == 0:
                            print("Setting legend",i,product, sensor, dataset)
                            dataset_title = dataset.replace('_','-').replace('OLI-test-image-','').replace('MSI-test-image-','')+'-'+uid.split('_')[-1] + ":" + str(lat) + "," + str(lon)
                            ax.set_title(fr'$\mathbf{{{dataset_title}}}$' ,fontsize=22,fontweight="bold")
                            ax.legend(fontsize=12,fancybox=True, framealpha=0.75,loc='lower left',prop={'size': 15})

                            #handles, labels = ax.get_legend_handles_labels()
                            #order = [0,2,3,1]
                            #ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order])
                        else:
                            ax.legend().set_visible(False)

                        if i == 2:
                            ax.set_xlabel('')

            plt.tight_layout()
            if type(uid) == float:
                uid_name = 'nan'
            else:
                uid_name = uid.split('_')[-1]
            plt.savefig(str(save_location) + f'/{dataset}_{sensor}_{atm_corr}_{uid_name}_timeseries.png',dpi=400)
            plt.close()        

        
    #iterate through datasets
    # for dataset in gathered_data.keys()
    
    
    
    return

#load data from insitu with a specific naming convention, 
gathered_data = load_gathered_data(gathered_path)
with open('/tis/m2cross/scratch/f003/roshea/For_Arun/gathered_data.pickle', 'wb') as handle:
    pickle.dump(gathered_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

insitu_data   = load_insitu_data(insitu_path,insitu_data_dictionary)
with open('/tis/m2cross/scratch/f003/roshea/For_Arun/insitu_data.pickle', 'wb') as handle:
    pickle.dump(insitu_data, handle, protocol=pickle.HIGHEST_PROTOCOL)


plot_products(gathered_data,insitu_data,save_path,plot_matchups=0)
