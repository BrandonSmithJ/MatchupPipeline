#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 09:56:09 2021

Function to process timeseries of geotiff imagery
"""

import datetime, warnings, os,pickle,rasterio 

import matplotlib as mpl
mpl.use('agg')
mpl.rcParams['figure.dpi'] = 600
mpl.rcParams['text.usetex'] = True
mpl.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}'] 

from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, HPacker, VPacker
import matplotlib.pyplot as plt
plt.rcParams["font.weight"] = "bold"
plt.rcParams["axes.labelweight"] = "bold"
from matplotlib import patheffects
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter

if os.name == 'nt':
    mpl.rc('font', family='Arial')
else:  
    mpl.rc('font', family='DejaVu Sans')

import pandas as pd
from pathlib import Path

import cartopy.crs as ccrs
import numpy as np
from osgeo import gdal, osr

from collections import defaultdict as dd 
from math import floor
from rasterio.plot import show
import xarray as xr
 

warnings.filterwarnings("ignore",category=DeprecationWarning)

gdal.UseExceptions()
####################################
def load_erie_insitu():
    import pandas as pd
    og_cols = {'Station':'station',
               'Date':'date',
               'Lattitude':'lat',
               'Longitude':'lon',
               'TSS\n(mg/L)':'tss',
               'CDOM Absorb\na[400] (m-1)':'cdom',
               'Extracted PC\n(µg/L)':'pc',
               'Extracted Chlorophyll\n(µg/L)':'chl',
               'Arrival Time\nET':'time',
               'Sample Depth (category)':'depthCategory',}
    erie_df = pd.read_csv(r'/data/roshea/SCRATCH/Insitu/Excel_spreadsheets/WLE_Summary_2008_2019_Nima.csv',
                     header=1,usecols=og_cols.keys())
    erie_df = erie_df.rename(columns=og_cols)
    erie_df.drop(erie_df[erie_df['depthCategory'] == 'Bottom'].index, inplace = True)
    erie_df = erie_df[erie_df['time'].notna()]
    erie_df['datetime'] = pd.to_datetime(erie_df.date.astype(str) + ' ' +erie_df.time.astype(str))
    erie_df.drop(erie_df[erie_df['datetime'] <= pd.to_datetime('2016/01/01')].index, inplace = True)
    
    erie_sites = erie_df['station'].value_counts().keys()[erie_df['station'].value_counts().values>10]
    erie_sites_latlon = {}
    # pd.to_datetime(erie_df['date'].values)
    
    products = ['datetime','chl','tss','cdom','pc']
    erie_sites_products = {site: {} for site in erie_sites}
    for erie_site in erie_sites:
        out = erie_df.groupby('station').get_group(erie_site).mean()
        erie_sites_latlon[erie_site] = [out['lat'],out['lon']]
        for product in products:
            erie_sites_products[erie_site][product] = erie_df.groupby('station').get_group(erie_site)[product]
        
    print(erie_df)
    return erie_sites_products,erie_sites_latlon
erie_sites_products,erie_sites_latlon = load_erie_insitu()
gathered_path = '/data/roshea/SCRATCH/Gathered/'
base_file_names = ['Erie_2016_2023' , 'Chesapeake_Bay_2016_2023']
# base_file_name = '/data/roshea/SCRATCH/Gathered/Chesapeake_Bay_2016_2023' 
base_file_names =[gathered_path + base_file_name for base_file_name in base_file_names]
#'/data/roshea/SCRATCH/Gathered/SaltonSea_1999_2022'    
#'/home/ryanoshea/Downloads/MODIS_VIIRS_Imagery/MODIS_VIIRS_Imagery'
sensors = ['OLCI']
atmospheric_correction = ['acolite','l2gen']
overwrite = False
matchup_locations = { #Lat/Lon
    'Erie_2016_2023' : erie_sites_latlon,
        
    #     {
    #     # 'WEX' : [41.7327,-83.3835],
    #     'WE2' : [41.7540,-83.2849],
    #     'WE3' : [41.8341,-83.1899],
    #     'WE4' : [41.8333,-83.1916],
    #     'WE5' : [41.8065,-83.2549],
    #     'WE6' : [41.7100666666667,-83.3803],
    #     #'WE6' : [],
    #     },
    
    'Chesapeake_Bay_2016_2023' : {
        'CB1.1' : [39.54794,-76.08481],
        'CB2.1' : [39.44149,-76.02599],
        'CB2.2' : [39.34873,-76.17579],
        'CB3.3C' : [38.99596,-76.35967],
        'CB4.3C' : [38.55505,-76.42794],
        'CB5.2' : [38.13705,-76.22787],
        'CB6.1' : [37.58847,-76.16216],
        'CB6.4' : [37.23653,-76.20799],
        'CB7.3E' : [37.22875,-76.05383],
        'CB7.4' : [36.9957,-76.02048],
        },
    }

#GSL
# lon = -112.52388
# lat = 41.11353
# lon = -112.76698
# lat = 41.39215
#Salton Sea
# lon = -115.862
# lat = 33.358
# lon = -115.655
# lat = 33.2835

# #OLCI Erie
# lon = -83.3835
# lat = 41.7327

#GL Sanctuary
# lat = 39.1586
# lon=-76.35782



############################################
# Find all filenames that we will use
def find_filenames(sensor, basefile,atmospheric_correction):
    final_filenames_list = []
    os.chdir(basefile+'/'+sensor)
    file_list = sorted(Path().resolve().rglob("*"+atmospheric_correction+"*.tif"))
    #print(file_list)
    os.chdir(basefile)

    return file_list

# Function to calculate datetime from input filename
def extract_datetime(fname,sensor):
    if sensor == 'MOD': datetime_convertor = '%Y%j%H%M%S'
    if sensor in [ 'VI','OLCI']: datetime_convertor = '%Y%m%dT%H%M%S'

    return [datetime.datetime.strptime(file.stem.split('_')[1],datetime_convertor) for file in fname]

##
matchup_dictionary = {}
# matchup_dictionary['monthly_average'][name][sensor][atm_cor][key]
matchup_dictionary = {name.split('/')[-1]: {key: {sensor: {atm_cor: {}  for atm_cor in atmospheric_correction} for sensor in sensors} for key,latlons in matchup_locations[name.split('/')[-1]].items()} for name in base_file_names }
# matchup_dictionary['daily'] =  {name.split('/')[-1]: {key: {sensor: {atm_cor: {}  for atm_cor in atmospheric_correction} for sensor in sensors} for key,latlons in matchup_locations[name.split('/')[-1]].items()} for name in base_file_names }
# matchup_dictionary['daily_DT'] = {n1ame.split('/')[-1]: {key: {sensor: {atm_cor: {}  for atm_cor in atmospheric_correction} for sensor in sensors} for key,latlons in matchup_locations[name.split('/')[-1]].items()} for name in base_file_names }

for base_file_name in base_file_names:
    name = base_file_name.split('/')[-1]
    
    for sensor in sensors:
        for atm_cor in atmospheric_correction:
            print(name,sensor,atm_cor)
            # lat, lon = lat_lon
            available_filenames = find_filenames(sensor, base_file_name,atm_cor)
            
            DT = extract_datetime(available_filenames,sensor=sensor)
            
            pickle_filename = base_file_name + f'/matchups_{name}_{sensor}_{atm_cor}.pkl'
            if os.path.exists(pickle_filename) and not overwrite:
                with open(pickle_filename,'rb') as handle:
                    value_array =  pickle.load(handle)
            else:
                sites_dictionary = {key: [] for  key, lat_lon in matchup_locations[name].items()}
                for i,filename in enumerate(available_filenames): 
                    xarr = xr.open_rasterio(filename)
                    for key, lat_lon in matchup_locations[name].items():
                        lat,lon = lat_lon
                        val = xarr.sel(x=lon, y=lat, method="nearest")
                        sites_dictionary[key].append(list(val.values))
                    if not i%100: print(i)
                # value_array = np.array(sites_dictionary)
                
 
                with open(pickle_filename,'wb') as handle:
                    pickle.dump([sites_dictionary],handle)
            for  key, lat_lon in matchup_locations[name].items():
                value_array = np.array(sites_dictionary[key])
                product_vals = {
                          'chl'  : value_array[:,0],
                          'tss'  : value_array[:,1],
                          'cdom' : value_array[:,2],
                          'pc'   : value_array[:,3],}
                
                prod_dataframe = pd.DataFrame(data=product_vals)
                prod_dataframe.index = DT
                grouped_prod = prod_dataframe.groupby(pd.Grouper(freq='M')).median()
                matchup_dictionary[name][key][sensor][atm_cor]['monthly_average'] = grouped_prod
                matchup_dictionary[name][key][sensor][atm_cor]['daily']           = product_vals
                matchup_dictionary[name][key][sensor][atm_cor]['daily_DT']        = DT
#%%



limits = {'chl': [.9,200],
          'tss': [1, 200],
          'cdom': [0.1, 5],
          'pc': [0.1, 300]}

products = {0 : 'chl',
           1 : 'tss',
           2 : 'cdom',
           3 : 'pc',}

colors = {'chl': 'g',
          'tss': 'r',
          'cdom': 'b',
          'pc'  : 'k',}

def default_dd(d={}, f=lambda k: k):
	''' Helper function to allow defaultdicts whose default value returned is the queried key '''

	class key_dd(dd):
		''' DefaultDict which allows the key as the default value '''
		def __missing__(self, key):
			if self.default_factory is None:
				raise KeyError(key)
			val = self[key] = self.default_factory(key)
			return val 
	return key_dd(f, d)

def pretty_text(product,ylabel="",xlabel=""):
	product_labels = default_dd({
		'chl' : 'Chl\\textit{a}',
		'aph' : '\\textit{a}_{ph}',
		'tss' : 'TSS',
		'cdom': '\\textit{a}_{CDOM}(440)',
        'pc'  : 'PC',
	})
	
	product_units = default_dd({
		'chl' : '[mg m^{-3}]',
		'tss' : '[g m^{-3}]',
		'aph' : '[m^{-1}]',
		'cdom': '[m^{-1}]',
        'pc ' : '[mg m^{-3}]',
	}, lambda k: '')
    
	estimate_label = ylabel#'Estimated' #'Satellite-derived'
	x_pre  = xlabel#'Measured'
	y_pre  = estimate_label.replace('-', '\\textbf{-}')
	space="\:"
	plabel = f'{product_labels[product]}{space} {product_units[product]}'
	xlabel = fr'$\mathbf{{{x_pre} {plabel}}}$'
	ylabel = fr'$\mathbf{{{y_pre}}}$'+'' +fr'$\mathbf{{ {plabel}}}$'
    
	return xlabel,ylabel
    
def is_float(element: any) -> bool:
    #If you expect None to be passed:
    if element is None: 
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False
    
def plot_timeseries(matchup_dictionary,location,site,save_location="/data/roshea/SCRATCH/Gathered/output_timeseries/"):
    markers = ['.','o']
    alphas = [0.8,0.35]
    colors = ['k','xkcd:red']
    colors_daily = ['xkcd:slate','xkcd:bright red']
    n_rows_fig = 4
    n_cols_fig = 1

    fig, axs = plt.subplots(nrows=n_rows_fig, ncols=n_cols_fig,
                            figsize=(24, 9), sharex=True, sharey=False)
    years = YearLocator()
    months = MonthLocator()
    years_format = DateFormatter('%Y')
    months_format = DateFormatter('%b')
    plot_count = 0
    for sensor  in matchup_dictionary[location][site].keys():
        for AC_i, atm_cor in enumerate(matchup_dictionary[location][site][sensor].keys()):
            print(plot_count,location,site,sensor,atm_cor)
            daily_vals = matchup_dictionary[location][site][sensor][atm_cor]['daily']
            daily_DT = matchup_dictionary[location][site][sensor][atm_cor]['daily_DT']
            monthly_average = matchup_dictionary[location][site][sensor][atm_cor]['monthly_average']
            for i,ax in enumerate(axs):
                product = products[i]
            
                ax.scatter(daily_DT, daily_vals[product],color=colors_daily[plot_count],marker=markers[plot_count],alpha=alphas[plot_count],label=f'{sensor} {atm_cor} Daily')
                # ax.scatter(VI_DT, value_array_VI[:,i],color='xkcd:dark red',marker='o',alpha=0.35,label='VI-Daily')
                if site in erie_sites_products.keys() and AC_i == 0:
                    ax.scatter(erie_sites_products[site]['datetime'].values,[float(val) if is_float(val) else np.nan  for val in erie_sites_products[site][product].values ],color='m',marker='x',alpha=alphas[plot_count],label=f'{sensor} matchups')

                ax.plot(monthly_average.index.to_pydatetime(),monthly_average[product],color=colors[plot_count],label=f'{sensor} {atm_cor} Monthly',linewidth=3,alpha = 0.75)
                # ax.plot(grouped_prod_VI.index.to_pydatetime(),grouped_prod_VI[product],color='xkcd:bright red',label='VI-Monthly',linewidth=4,alpha = 0.75)
            
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
                # ax.xaxis.labelpad = 20
                ax.set_yscale('log')
                ax.set_ylim(limits[product])
                ax.set_ylabel(f'{pretty_text(product)[1]}',fontsize=20)
                ax.grid(True,which='major',color = 'xkcd:slate grey')
                ax.grid(True,which='minor',color = 'xkcd:light grey')
                ax.set_axisbelow(True)

                if i==0: 
                    ax.legend(fontsize=14,fancybox=True, framealpha=0.5)
                    location_name = location.replace('_',"\:") + ":\:"
                    ax.set_title(fr'$\mathbf{{{location_name}   {site}}}$' ,fontsize=22,fontweight="bold")
                # print(plot_count)
            plot_count=plot_count+1
    plt.tight_layout()
    plt.savefig(save_location + f'{location}_{site}_{list(matchup_dictionary[location][site].keys())}_{list(matchup_dictionary[location][site][sensor].keys())}_timeseries.png')
            
    plt.show()
    # assert(0)
for location in matchup_dictionary.keys():
    for site in matchup_dictionary[location].keys():
        plot_timeseries(matchup_dictionary,location,site)
