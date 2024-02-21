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

    out = [datetime.datetime.strptime(file.split('_')[index],datetime_convertor) for file in fname ]
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

product_rename_dictionary = {'Chla' : 'chla',
                             'Zsd'  : 'secchi',
                             'TSS'  :  'tss', }
# os.mkdir(save_path)
#load data from the matchups files into a very standardized format
def load_gathered_data(gathered_path,folder_names=[],products=[],overwrite=True):
    #identify all folders in gathered path
    sensors        = ["OLI","MSI"]
    atm_corrs      = ["aquaverse"]
    datasets       = ["OLI_test_image_Erie_stations","OLI_test_image_Damariscotta_1",'OLI_test_image_Damariscotta_2',"OLI_test_image_Oyster_farm","OLI_test_image_Honga_TS_1","OLI_test_image_Honga_TS_2","OLI_test_image_Wachusett_reservoir_timeseries","OLI_test_image_Quabbin_reservoir_timeseries"] #,"OLI_test_image_Honga_TS_1","OLI_test_image_Honga_TS_2"
    #datasets = ["OLI_test_image_Wachusett_reservoir_timeseries"]
    ######
    gathered_data     = {}
    gathered_data_uid = {}
    unique_uids       = {}

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

                    for product in ['Chla','Zsd','TSS']:
                        gathered_data[dataset][sensor][atm_corr][product_rename_dictionary[product]] = gathered_data[dataset][sensor][atm_corr][product]
                   
                    if 'uid' in gathered_data[dataset][sensor][atm_corr].keys() and ('timeseries' in dataset or 'Erie' in dataset):

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

insitu_data_dictionary = {"OLI_test_image_Oyster_farm" : ['',0],
                          "OLI_test_image_Honga_TS_1"  : ["Honga_insitu_1",7],
                          "OLI_test_image_Honga_TS_2"  : ["Honga_insitu_2",7], 
                          "OLI_test_image_Damariscotta_1"  : ["Damariscotta_1_DockChl",0],
                          "OLI_test_image_Damariscotta_2"  : ["",0],
                          "OLI_test_image_Wachusett_reservoir_timeseries"  : ["",0],
                          "OLI_test_image_Quabbin_reservoir_timeseries"    : ["",0],
                          "OLI_test_image_Erie_stations"                   : ["",0],
                          }

# title_dictionary  

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
                datetime_array = insitu_data[dataset]['date'].values +'T' + insitu_data[dataset]['Time'].values
                datetime_convertor = '%m/%d/%YT%H:%M:%S'
                datetime_array = [datetime.datetime.strptime(file,datetime_convertor) for file in datetime_array ]
                insitu_data[dataset]['datetime'] = datetime_array

    #iterate through in situ data
    
    return insitu_data

def average_output(datetimes,products):
    data = pd.DataFrame()
    import seaborn as sns

    datetimes = [datetime.datetime.strptime(datetime.datetime.strftime(date_time, '%Y-%m-%d'),'%Y-%m-%d') for date_time in datetimes] 
    data['datetimes']     = datetimes
    data['products']      = products
    data                  = data.set_index('datetimes')
    data                  = data.groupby(level=0)
    grouped_data          = data.agg({'products':'mean'})
    data                  = grouped_data.reindex(pd.date_range('01-01-2015','02-02-2024'),fill_value=np.nan)
    data['30day_average'] = data.products.rolling(window=30,min_periods=1,center=True,win_type='gaussian').mean(std=7)
    data['datetimes']     = data.index
    return data

def plot_products(gathered_data,insitu_data,save_location,products=['chla','tss','secchi']):
    markers       = {'OLI' : 'o',
                     'MSI' : 'X',}
    alphas        = [0.8,0.35]
    colors        = {'OLI': {'aquaverse': 'xkcd:black', 'acolite': 'xkcd:red','seadas': 'xkcd:pink','polymer':'xkcd:green', 'cyan': 'xkcd:teal'},
		     'MSI': {'aquaverse': 'xkcd:red', 'acolite': 'xkcd:red','seadas': 'xkcd:pink','polymer':'xkcd:green', 'cyan': 'xkcd:teal'},}    #[ 'k','xkcd:red']
    colors_daily  = ['xkcd:slate','xkcd:bright red']
    insitu_colors = 'xkcd:bright blue'
    
    n_rows_fig    = len(products)
    n_cols_fig    = 1
    
    limits        = {
                    'chla'    : [0.1,100],
                    'tss'     : [0.1,100],
                    'secchi'  : [0.1,10],
                    }


    for dataset in gathered_data.keys():
        #if True:
        for uid in gathered_data[dataset].keys():
            fig, axs      = plt.subplots(nrows=n_rows_fig, ncols=n_cols_fig,
                             figsize=(int(24*n_rows_fig/4), 12), sharex=True, sharey=False)#24,9
            years         = YearLocator()
            months        = MonthLocator()
            years_format  = DateFormatter('%Y')
            months_format = DateFormatter('%b')

            for sensor in gathered_data[dataset][uid].keys():
            #fig, axs      = plt.subplots(nrows=n_rows_fig, ncols=n_cols_fig,
            #                figsize=(int(24*n_rows_fig/4), 12), sharex=True, sharey=False)#24,9 
                for atm_corr in gathered_data[dataset][uid][sensor].keys():
                    lat = gathered_data[dataset][uid][sensor][atm_corr]['lat'].values[0] if 'lat' in gathered_data[dataset][uid][sensor][atm_corr].keys() else ''
                    lon = gathered_data[dataset][uid][sensor][atm_corr]['lon'].values[0] if 'lon' in gathered_data[dataset][uid][sensor][atm_corr].keys()  else ''

                    for i,ax in enumerate(axs):
                        product = products[i]
                        if product == 'chla' and sensor == 'OLI': continue 
                        #Insitu data
                        if dataset in insitu_data.keys():
                            if product in insitu_data[dataset].keys():

                                data_ins = average_output(insitu_data[dataset]['datetime'],insitu_data[dataset][product])

                                ax.scatter(insitu_data[dataset]['datetime'], insitu_data[dataset][product],color='xkcd:dodger blue',marker='*',alpha=0.5,zorder = 101,label=f'in situ',edgecolors='none',s=80)
                                #ax.plot(insitu_data[dataset]['datetime'], insitu_data[dataset][product],color='xkcd:vivid blue',alpha=1,zorder = 102,linewidth=2)
                                sns.lineplot(x = 'datetimes',y='30day_average',data=data_ins,label=f'30-day average in situ',ax=ax, linewidth=2,color='xkcd:vivid blue')

                        if product in      gathered_data[dataset][uid][sensor][atm_corr].keys():
                            datetimes_in = gathered_data[dataset][uid][sensor][atm_corr]['datetime_from_scene_id']
                            products_in  = gathered_data[dataset][uid][sensor][atm_corr][product]

                            def filter_products(datetimes_in,products_in):
                                datetime_filtered = [ datetime.datetime.strptime(datetime.datetime.strftime(date_time, '%Y-%m-%d'),'%Y-%m-%d') for date_time,product in zip(datetimes_in,products_in) if product > -1]
                                product_filtered = [ product for datetime,product in zip(datetimes_in,products_in) if product > -1 ]
                                return datetime_filtered, product_filtered

                            datetimes_filtered, products_filtered = filter_products(datetimes_in,products_in)

                            data = average_output(datetimes_filtered,products_filtered)
                            #sns.lineplot(x = 'datetimes',y='products',data=data,label=f'sns {sensor} {atm_corr}',ax=ax)
                            sns.lineplot(x = 'datetimes',y='30day_average',data=data,label=f'30-day average {sensor} {atm_corr}' if i == 0 else None,ax=ax, linewidth=2,color=colors[sensor][atm_corr])

                            ax.scatter(datetimes_filtered, products_filtered,color=colors[sensor][atm_corr],marker=markers[sensor],alpha=0.5,zorder = 100,label=f'{sensor} {atm_corr}',s=60,edgecolors='none')
                            
                                 
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
                        ax.set_ylim(limits[product])
                        ax.set_ylabel(f'{pretty_text(product)[1]}',fontsize=20)
                        ax.grid(True,which='major',color = 'xkcd:slate grey')
                        ax.grid(True,which='minor',color = 'xkcd:light grey')
                        ax.set_axisbelow(True)
                        if i == 0:
                            print("Setting legend",i,product, sensor, dataset)
                            dataset_title = dataset.replace('_','-').replace('OLI-test-image-','').replace('MSI-test-image-','')+'-'+uid.split('_')[-1] + ":" + str(lat) + "," + str(lon)
                            ax.set_title(fr'$\mathbf{{{dataset_title}}}$' ,fontsize=22,fontweight="bold")
                            ax.legend(fontsize=12,fancybox=True, framealpha=0.75,loc='upper left')

                            #handles, labels = ax.get_legend_handles_labels()
                            #order = [0,2,3,1]
                            #ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order])
                        else:
                            ax.legend().set_visible(False)

            plt.tight_layout()
            uid_name = uid.split('_')[-1]
            plt.savefig(str(save_location) + f'/{dataset}_{sensor}_{atm_corr}_{uid_name}_timeseries.png',dpi=225)
            plt.close()        

        
    #iterate through datasets
    # for dataset in gathered_data.keys()
    
    
    
    return

#load data from insitu with a specific naming convention, 
gathered_data = load_gathered_data(gathered_path)

insitu_data   = load_insitu_data(insitu_path,insitu_data_dictionary)
plot_products(gathered_data,insitu_data,save_path)
