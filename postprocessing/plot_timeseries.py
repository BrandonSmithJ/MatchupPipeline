#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 09:56:09 2021

Function to process timeseries of geotiff imagery
"""

import datetime, warnings, os,pickle,rasterio 
from datetime import timedelta

from ..MDNs.MDN_MODIS_VIIRS_OLCI.plot_utils import add_identity, add_stats_box
from ..MDNs.MDN_MODIS_VIIRS_OLCI.metrics import slope, sspb, mdsa, count 

import matplotlib             as mpl
mpl.use('agg')
mpl.rcParams['figure.dpi'] = 600
mpl.rcParams['text.usetex'] = True
mpl.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}'] 

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
from .utils import convert_CyAN, default_dd, load_insitu, is_float , find_filenames, align_matchups, pull_timeseries, extract_datetime, adjust_cdom

warnings.filterwarnings("ignore",category=DeprecationWarning)

####################################

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
        'pc' : '[mg m^{-3}]',
	}, lambda k: '')
    
	estimate_label = ylabel
	x_pre  = xlabel
	y_pre  = estimate_label.replace('-', '\\textbf{-}')
	space  = "\:"
	plabel = f'{product_labels[product]}{space} {product_units[product]}'
	xlabel = fr'$\mathbf{{{x_pre} {plabel}}}$'
	ylabel = fr'$\mathbf{{{y_pre}}}$'+'' +fr'$\mathbf{{ {plabel}}}$'
    
	return xlabel,ylabel
    

    
def plot_timeseries(matchup_dictionary,location,site,products,erie_sites_products,CB_sites_products,limits,matchups_cyan,matchups_NOAA,save_location="/data/roshea/SCRATCH/Gathered/output_timeseries/"):
    markers       = ['.','o']
    alphas        = [0.8,0.35]
    colors        = ['k','xkcd:red']
    colors_daily  = ['xkcd:slate','xkcd:bright red']
    n_rows_fig    = 4
    n_cols_fig    = 1

    fig, axs      = plt.subplots(nrows=n_rows_fig, ncols=n_cols_fig,
                            figsize=(24, 9), sharex=True, sharey=False)
    years         = YearLocator()
    months        = MonthLocator()
    years_format  = DateFormatter('%Y')
    months_format = DateFormatter('%b')
    plot_count    = 0
    
    for sensor  in matchup_dictionary[location][site].keys():
        for AC_i, atm_cor in enumerate(matchup_dictionary[location][site][sensor].keys()):
            print(plot_count,location,site,sensor,atm_cor)
            daily_vals      = matchup_dictionary[location][site][sensor][atm_cor]['daily']
            daily_DT        = matchup_dictionary[location][site][sensor][atm_cor]['daily_DT']
            monthly_average = matchup_dictionary[location][site][sensor][atm_cor]['monthly_average']
            for i,ax in enumerate(axs):
                product = products[i]
            
                ax.scatter(daily_DT, daily_vals[product],color=colors_daily[plot_count],marker=markers[plot_count],alpha=alphas[plot_count],zorder = 3,label=f'{sensor} {atm_cor} Daily')
                # ax.scatter(VI_DT, value_array_VI[:,i],color='xkcd:dark red',marker='o',alpha=0.35,label='VI-Daily')
                
                #Erie Truth
                if site in erie_sites_products.keys() and AC_i == 0:
                    ax.scatter(erie_sites_products[site]['datetime'].values,[float(val) if is_float(val) else np.nan  for val in erie_sites_products[site][product].values ],color='xkcd:light sky blue',marker='*',alpha=alphas[plot_count],zorder = 100,label=f'{sensor} matchups',edgecolors='xkcd:vivid blue')
                
                #CYaN
                if site in matchups_cyan[location]['daily'].keys() and product in ['chl'] and AC_i == 0:
                    ax.scatter(matchups_cyan[location]['daily_DT'],[convert_CyAN(float(val[0])) if is_float(val[0]) else np.nan  for val in matchups_cyan[location]['daily'][site] ],color='xkcd:cyan',marker='^',alpha=alphas[plot_count],zorder = 1,label=f'{sensor} CyAN',edgecolors='xkcd:teal green')
                
                #NOAA
                if product in matchups_NOAA[location].keys():
                    if site in matchups_NOAA[location][product]['daily'].keys() and product in ['chl','tss'] and AC_i == 0:
                        ax.scatter(matchups_NOAA[location][product]['daily_DT'],[float(val[0]) if is_float(val[0]) else np.nan  for val in matchups_NOAA[location][product]['daily'][site] ],color='xkcd:dark lavender',marker='p',alpha=alphas[plot_count],zorder = 1,label=f'{sensor} NOAA',edgecolors='xkcd:neon purple')

                # if site in matchups_cyan['Chesapeake_Bay_2016_2023']['daily'].keys and product in ['chl']:
                #     ax.scatter(matchups_cyan['Chesapeake_Bay_2016_2023']['daily_DT'][site].values,[float(val) if is_float(val) else np.nan  for val in matchups_cyan['Chesapeake_Bay_2016_2023']['daily'][site] ],color='xkcd:cyan',marker='^',alpha=alphas[plot_count],zorder = 80,label=f'{sensor} matchups',edgecolors='xkcd:turquoise')

                # CB Truth
                if site in CB_sites_products.keys() and AC_i == 0 and product in ['chl','tss',]:
                    product_vals            = {i:CB_sites_products[site][i]  for i in CB_sites_products[site].keys()}
                    
                    prod_dataframe          = pd.DataFrame(data=product_vals)
                    prod_dataframe.index    = CB_sites_products[site]['datetime']
                    grouped_prod_site_daily = prod_dataframe.groupby(pd.Grouper(freq='D')).mean()
                    
                    ax.scatter(CB_sites_products[site]['datetime'].values,[float(val) if is_float(val) else np.nan  for val in CB_sites_products[site][product].values ],color='xkcd:neon blue',marker='*',alpha=alphas[plot_count],zorder = 100,label=f'{sensor} matchups',edgecolors='xkcd:vivid blue')
                   
                    x      = grouped_prod_site_daily.index.to_pydatetime()
                    y      = grouped_prod_site_daily[product]
                    y_mask = np.isfinite(y)
                    ax.plot(x[y_mask],y[y_mask],color='xkcd:primary blue',label=f'Daily Matchups',linewidth=2.25,alpha = 0.75,linestyle='-',marker='o')

                # monthly average for products
                ax.plot(monthly_average.index.to_pydatetime()-datetime.timedelta(days=14),monthly_average[product],color=colors[plot_count],label=f'{sensor} {atm_cor} Monthly',linewidth=3,alpha = 0.75)
                # ax.plot(grouped_prod_VI.index.to_pydatetime(),grouped_prod_VI[product],color='xkcd:bright red',label='VI-Monthly',linewidth=4,alpha = 0.75)
            
                # Formatting
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
                ax.set_ylim(limits[location][product])
                ax.set_ylabel(f'{pretty_text(product)[1]}',fontsize=20)
                ax.grid(True,which='major',color = 'xkcd:slate grey')
                ax.grid(True,which='minor',color = 'xkcd:light grey')
                ax.set_axisbelow(True)

                if i==0: 
                    ax.legend(fontsize=12,fancybox=True, framealpha=0.5,loc='center left')
                    location_name = location.replace('_',"\:") + ":\:"
                    ax.set_title(fr'$\mathbf{{{location_name}   {site}}}$' ,fontsize=22,fontweight="bold")
            plot_count=plot_count+1
            
    plt.tight_layout()
    plt.savefig(save_location + f'{location}_{site}_{list(matchup_dictionary[location][site].keys())}_{list(matchup_dictionary[location][site][sensor].keys())}_timeseries.png')
    plt.close()        

def plot_matchups(aligned_matchups_dictionary,limits,save_location="/data/roshea/SCRATCH/Gathered/output_timeseries/", sites_dict =[],aligned_matchups_dictionary_combined=None):
    n_rows_fig   = 2
    n_cols_fig   = 2
    plot_number  = {'chl':[0,0],'tss':[0,1],'cdom':[1,0],'pc':[1,1]}
    colors       = mcolors.CSS4_COLORS
    by_hsv       = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgb(color))),name) for name, color in colors.items())
    names        = [name for hsv, name in by_hsv]
    plot_sites   = aligned_matchups_dictionary_combined is None
    
    for atm_cor in ['acolite','l2gen'] :
        for location in aligned_matchups_dictionary.keys():
            n_rows_fig            = 1 if location =='Chesapeake_Bay_2016_2023' else 2
            fig, axs              = plt.subplots(nrows=n_rows_fig, ncols=n_cols_fig,
                                    figsize=(9, 4.5*n_rows_fig), sharex=False, sharey=False)
            len_represented_sites = len(aligned_matchups_dictionary[location].keys()) if not len(sites_dict[location]) else len(sites_dict[location])
            color_indices         = np.linspace(0,len(names)-1,num=len_represented_sites).astype(int) if plot_sites else np.linspace(0,len(names)-1,num=4).astype(int)
            colors_to_plot        = [names[i] for i in color_indices ]
            color_index           = 0

            for site_number,site in enumerate(aligned_matchups_dictionary[location].keys()):
                if not plot_sites and site_number>1: continue
                if len(sites_dict[location]) and site not in sites_dict[location]: continue
                location_name = location.split('_')[0]
                plt.suptitle(fr' ' ,fontsize=22,fontweight="bold")
        
                for sensor in aligned_matchups_dictionary[location][site].keys():
                    if  not plot_sites:
                        insitu         = aligned_matchups_dictionary_combined[location][sensor][atm_cor]['insitu']
                        remote         = aligned_matchups_dictionary_combined[location][sensor][atm_cor]['remote']
                        color_index    = 0
                        colors_to_plot = ['xkcd:moss','xkcd:scarlet','xkcd:dark lavender','xkcd:teal',]
                        if 'Chesapeake' in location : 
                            if 'pc'   in insitu.keys(): insitu.pop('pc')
                            if 'cdom' in insitu.keys(): insitu.pop('cdom')
                    else:
                        insitu = aligned_matchups_dictionary[location][site][sensor][atm_cor]['insitu']
                        remote = aligned_matchups_dictionary[location][site][sensor][atm_cor]['remote']
                        
                    for product in insitu.keys():
                        if product == 'datetime': continue
                        ax   = axs[plot_number[product][0]][plot_number[product][1]] if location !='Chesapeake_Bay_2016_2023' else  axs[plot_number[product][1]]
                        minv = -2 if product == 'cdom' or product == 'pc' else 0
                        maxv = 3  if product == 'tss'  else 3 if product == 'chl' else 3 if product == 'pc' else 1 

                        loc  = ticker.LinearLocator(numticks=int(round(maxv-minv+1.5)))
                        fmt  = ticker.FuncFormatter(lambda i, _: r'$10$\textsuperscript{%i}'%i)

                        ax.set_ylim((minv, maxv))
                        ax.set_xlim((minv, maxv))
                        ax.xaxis.set_major_locator(loc)
                        ax.yaxis.set_major_locator(loc)
                        ax.xaxis.set_major_formatter(fmt)
                        ax.yaxis.set_major_formatter(fmt)
                        
                        if  not plot_sites: 
                            color=colors_to_plot[color_index]
                            y_true = np.array(insitu[product])
                            y_est = np.array(remote[product])
                            y_est_log  = np.log10(y_est).flatten()
                            y_true_log = np.log10(y_true).flatten()
                            valid = np.logical_and(np.isfinite(y_true_log), np.isfinite(y_est_log))
                            l_kws = {'color': color, 'path_effects': [pe.Stroke(linewidth=4, foreground='k'), pe.Normal()], 'zorder': 22, 'lw': 1}
                            s_kws = {'alpha': 0.4, 'color': color}
                            if valid.sum():
                                sns.regplot(y_true_log[valid], y_est_log[valid], ax=ax, scatter_kws=s_kws, line_kws=l_kws, fit_reg=True, truncate=False, robust=True, ci=None)
                                kde = sns.kdeplot(y_true_log[valid], y_est_log[valid], shade=False, ax=ax, bw='scott', n_levels=4, legend=False, gridsize=100, color=color)
                                kde.collections[2].set_alpha(0)

                                add_stats_box(ax, y_true[valid], y_est[valid],metrics=[count,mdsa,sspb,slope])
                        # ax.scatter(insitu[product],remote[product],
                        #            label = site , #if atm_cor == 'acolite' else None
                        #            marker=markers[atm_cor],
                        #            color=colors_to_plot[color_index] if plot_sites else 'r',
                        #            edgecolors='k',
                        #            alpha=0.75)
                                color_index = color_index+1
                        
                        ax.tick_params(axis='x', which='major', labelsize=16)
                        ax.tick_params(axis='y', which='major', labelsize=16)

                        ax.tick_params(axis='x'   , which='minor', labelsize=14)

                        ax.set_title(f'{pretty_text(product)[1]}',fontsize=20)
                        estimated = 'Remotely\:Estimated'
                        insitu_measured='\\textit{In situ}\:Measured'
                        title = location_name + '\:' + atm_cor
                        # ax.set_ylabel(fr'$\mathbf{{{estimated}   }}$' ,fontsize=18,fontweight="bold")
                        # ax.set_xlabel(fr'$\mathbf{{{insitu_measured}   }}$' ,fontsize=18,fontweight="bold")

                        ax.grid(True,which='major',color = 'xkcd:slate grey')
                        ax.grid(True,which='minor',color = 'xkcd:light grey')
                        ax.set_axisbelow(True)
                        add_identity(ax, ls='--', color='k', zorder=20)
                        if  product == 'chl': 
                            if plot_sites and 'Erie' in location or (len(sites_dict[location]) and plot_sites): ax.legend(fontsize=8,fancybox=True, framealpha=0.5)
                            fig.text(0.5, 0.011 if 'Erie' in location else  0.02, fr'$\mathbf{{{insitu_measured}   }}$' ,fontsize=18,fontweight="bold", ha='center', va='center')
                            fig.text(0.015, 0.5, fr'$\mathbf{{{estimated}   }}$' ,fontsize=18,fontweight="bold", ha='center', va='center', rotation='vertical')
                            fig.text(0.53, 0.96 if 'Erie' in location else  0.94 , fr'$\mathbf{{{title}   }}$' ,fontsize=22,fontweight="bold", ha='center', va='center')
                            ax.set_ylabel(fr'' ,fontsize=18,fontweight="bold")
                            plt.gcf().subplots_adjust(bottom=0.065 if 'Erie'  in location else 0.11)
                            plt.gcf().subplots_adjust(left=0.085)

                    if plot_sites: 
                        continue
                    
                color_index = color_index+1 
            plt.tight_layout()
            plt.gcf().subplots_adjust(bottom=0.065 if 'Erie' in location  else 0.11)
            plt.gcf().subplots_adjust(left=0.085)

            save_loc = save_location + f'{location}_{atm_cor}_matchups_{plot_sites}.png'
            plt.savefig(save_loc)
        
def plot_matchups_main(plotting_logic,overwrite = False):
    Erie_csv_filename = r'/data/roshea/SCRATCH/Insitu/Excel_spreadsheets/WLE_Summary_2008_2019_Nima.csv'
    Erie_col_name_dictionary = {'Station':'station',
               'Date':'date',
               'Lattitude':'lat',
               'Longitude':'lon',
               'TSS\n(mg/L)':'tss',
               'CDOM Absorb\na[400] (m-1)':'cdom',
               'Extracted PC\n(µg/L)':'pc',
               'Extracted Chlorophyll\n(µg/L)':'chl',
               'Arrival Time\nET':'time',
               'Sample Depth (category)':'depthCategory',
               }
        
    erie_sites_products,erie_sites_latlon = load_insitu(Erie_csv_filename,Erie_col_name_dictionary,header=1,drop_rows = ['depthCategory','Bottom','=='])
    
    for site in erie_sites_products:
        
        erie_sites_products[site]['cdom'] = erie_sites_products[site]['cdom'].apply(adjust_cdom)
    CB_csv_filename = r'/data/roshea/SCRATCH/Insitu/Excel_spreadsheets/CPB_WaterQualityWaterQualityStation.csv'
    CB_col_name_dictionary = {'Station':'station',
                'SampleDate':'date',
                'Latitude':'lat',
                'Longitude':'lon',
                # 'TSS':'tss',
                # 'CDOM Absorb\na[400] (m-1)':'cdom',
                # 'Extracted PC\n(µg/L)':'pc',
                # 'CHLA':'chl',
                'SampleTime':'time',
                'Depth':'Depth',
                'MeasureValue' : 'concentration',
                'Parameter':'WQP',}
    WQP_names = {
        'tss' :'TSS',
        'chl': 'CHLA',}
        
    CB_sites_products,CB_sites_latlon = load_insitu(CB_csv_filename,CB_col_name_dictionary,header=0,drop_rows = ['Depth',1.5,'>='],WQP_names=WQP_names,products= ['datetime','chl','tss'])
    gathered_path = '/data/roshea/SCRATCH/Gathered/'
    base_file_names = ['Chesapeake_Bay_2016_2023','Erie_2016_2023' ]
    # base_file_name = '/data/roshea/SCRATCH/Gathered/Chesapeake_Bay_2016_2023' 
    base_file_names =[gathered_path + base_file_name for base_file_name in base_file_names]
    #'/data/roshea/SCRATCH/Gathered/SaltonSea_1999_2022'    
    #'/home/ryanoshea/Downloads/MODIS_VIIRS_Imagery/MODIS_VIIRS_Imagery'
    sensors = ['OLCI']
    atmospheric_correction = ['acolite','l2gen']
    # overwrite = False
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
        
        'Chesapeake_Bay_2016_2023' :  CB_sites_latlon,
        # #{
        #     'CB1.1' : [39.54794,-76.08481],
        #     'CB2.1' : [39.44149,-76.02599],
        #     'CB2.2' : [39.34873,-76.17579],
        #     'CB3.3C' : [38.99596,-76.35967],
        #     'CB4.3C' : [38.55505,-76.42794],
        #     'CB5.2' : [38.13705,-76.22787],
        #     'CB6.1' : [37.58847,-76.16216],
        #     'CB6.4' : [37.23653,-76.20799],
        #     'CB7.3E' : [37.22875,-76.05383],
        #     'CB7.4' : [36.9957,-76.02048],
        #     },
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

    
    ##
    # matchup_dictionary = {}
    # matchups_CyAN      = {}
    matchups_CyAN= {name.split('/')[-1]: {daily: {} for daily in ['daily', 'daily_DT']} for name in base_file_names}
    matchups_NOAA= {name.split('/')[-1]: {NOAA_product: {daily: {} for daily in ['daily', 'daily_DT']} for NOAA_product in ['chl','tss']} for name in base_file_names}
    # matchup_dictionary['monthly_average'][name][sensor][atm_cor][key]
    # matchup_dictionary = {name.split('/')[-1]: {key: {sensor: {atm_cor: {}  for atm_cor in atmospheric_correction} for sensor in sensors} for key,latlons in matchup_locations[name.split('/')[-1]].items()} for name in base_file_names }
    # matchup_dictionary['daily'] =  {name.split('/')[-1]: {key: {sensor: {atm_cor: {}  for atm_cor in atmospheric_correction} for sensor in sensors} for key,latlons in matchup_locations[name.split('/')[-1]].items()} for name in base_file_names }
    # matchup_dictionary['daily_DT'] = {n1ame.split('/')[-1]: {key: {sensor: {atm_cor: {}  for atm_cor in atmospheric_correction} for sensor in sensors} for key,latlons in matchup_locations[name.split('/')[-1]].items()} for name in base_file_names }
    atmospheric_correction_NOAA_CyAN = atmospheric_correction.copy()
    atmospheric_correction_NOAA_CyAN.extend(['NOAA','CyAN'])
    matchup_dictionary = {name.split('/')[-1]: {key: {sensor: {atm_cor: {daily: {} for daily in ['daily','daily_DT','monthly_average']}  for atm_cor in atmospheric_correction_NOAA_CyAN} for sensor in sensors} for key,latlons in matchup_locations[name.split('/')[-1]].items()} for name in base_file_names }

    for base_file_name in base_file_names:
        name = base_file_name.split('/')[-1]
        
        #CyAN
        base_CyAN                = gathered_path + 'CyAN'
        pickle_filename_CyAN     = base_CyAN + f'/CyAN_{name}.pkl'

        available_filenames_CyAN     = find_filenames('', base_CyAN+'/' + name,'',subfile='cyan')
        datetimes_CyAN               = extract_datetime(available_filenames_CyAN,sensor='',subfile='cyan')
        matchups_CyAN[name]['daily'] = pull_timeseries(available_filenames_CyAN,pickle_filename_CyAN,matchup_locations[name],overwrite=overwrite)
        matchups_CyAN[name]['daily_DT'] = datetimes_CyAN
        
        base_NOAA                = gathered_path + 'NOAA'
        if name == 'Chesapeake_Bay_2016_2023':
            for NOAA_product in ['chl','tss']:
                pickle_filename_NOAA = base_NOAA + f'/NOAA_{NOAA_product}_{name}.pkl'
                
                available_filenames_NOAA                      = find_filenames('', base_NOAA+'/' + name,'',subfile='NOAA',NOAA_product=NOAA_product)
                datetimes_NOAA                                = extract_datetime(available_filenames_NOAA,sensor='',subfile='NOAA')
                matchups_NOAA[name][NOAA_product]['daily']    = pull_timeseries(available_filenames_NOAA,pickle_filename_NOAA,matchup_locations[name],overwrite=overwrite)
                matchups_NOAA[name][NOAA_product]['daily_DT'] = datetimes_NOAA
        
        
        for sensor in sensors:
            for atm_cor in atmospheric_correction:
                print(name,sensor,atm_cor)
                # lat, lon = lat_lon
                available_filenames = find_filenames(sensor, base_file_name,atm_cor)
                DT = extract_datetime(available_filenames,sensor=sensor)
                
                pickle_filename = base_file_name + f'/matchups_{name}_{sensor}_{atm_cor}.pkl'
                sites_dictionary = pull_timeseries(available_filenames,pickle_filename,matchup_locations[name],overwrite=overwrite)
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

    limits = {
        'Chesapeake_Bay_2016_2023' : {'chl' : [.5,100],
                                      'tss' : [1, 100],
                                      'cdom': [0.05, 5],
                                      'pc'  : [0.1, 20]},
        
        'Erie_2016_2023' : {'chl' : [.9,300],
                            'tss' : [1, 200],
                            'cdom': [0.1, 5],
                            'pc'  : [0.1, 300]},
            }
    
    products = {0 : 'chl',
                1 : 'tss',
                2 : 'cdom',
                3 : 'pc',}    
    
    for location in matchup_dictionary.keys():
        for site in matchup_dictionary[location].keys():
            if plotting_logic in ['timeseries','all']: plot_timeseries(matchup_dictionary,location,site,products,erie_sites_products,CB_sites_products,limits,matchups_CyAN,matchups_NOAA)

    insitu          = {'Erie_2016_2023' : erie_sites_products,
                       'Chesapeake_Bay_2016_2023' : CB_sites_products,}
    
    pickle_filename = base_file_name + f'/matchups_aligned.pkl'
    
    appended_matchup_dictionary = matchup_dictionary
    for location in matchup_dictionary.keys():
        for site in  matchup_dictionary[location].keys():
            for sensor in  matchup_dictionary[location][site].keys():
                # for additional_product in ['NOAA','CYAN']:
                if location in ['Chesapeake_Bay_2016_2023']:
                    matchup_dictionary[location][site][sensor]['NOAA']['daily']['chl'] = matchups_NOAA[location]['chl']['daily'][site]
                    matchup_dictionary[location][site][sensor]['NOAA']['daily_DT']['chl'] = matchups_NOAA[location]['chl']['daily_DT']
                    matchup_dictionary[location][site][sensor]['NOAA']['daily']['tss'] = matchups_NOAA[location]['tss']['daily'][site]
                    matchup_dictionary[location][site][sensor]['NOAA']['daily_DT']['tss'] = matchups_NOAA[location]['tss']['daily_DT']

                matchup_dictionary[location][site][sensor]['CyAN']['daily']['chl'] = matchups_CyAN[location]['daily'][site]
                matchup_dictionary[location][site][sensor]['CyAN']['daily_DT']     = matchups_CyAN[location]['daily_DT']
    # matchups_CyAN,matchups_NOAA
    
    if os.path.exists(pickle_filename) and not overwrite and False:
        with open(pickle_filename,'rb') as handle:
            aligned_matchups_dictionary =  pickle.load(handle)
            aligned_matchups_dictionary = aligned_matchups_dictionary[0]
    else:
        aligned_matchups_dictionary     = align_matchups(insitu,matchup_dictionary)

        with open(pickle_filename,'wb') as handle:
            pickle.dump([aligned_matchups_dictionary],handle)
        
    aligned_matchups_dictionary_combined = {name.split('/')[-1]: 
                                            {sensor: 
                                             {atm_cor: 
                                              {insitu_remote:
                                               {product: [] for product in ['chl','tss','cdom','pc','datetime'] }
                                               for insitu_remote in ['insitu','remote']}
                                              for atm_cor in atmospheric_correction} 
                                             for sensor in sensors} 
                                           for name in base_file_names }
        
    sites_dict =     {'Erie_2016_2023':[],
                      'Chesapeake_Bay_2016_2023': []}#['CB7.4','CB7.4N','CB5.5','CB7.1','CB7.1N','CB7.1S','CB7.2','CB7.2E','CB7.3','CB7.3E','CB8.1','CB8.1E']}        
    
    for name in base_file_names:
        location = name.split('/')[-1]
        for sensor in sensors:
            for atm_cor in atmospheric_correction:
                for insitu_remote in ['insitu','remote']:
                    for site in aligned_matchups_dictionary[location].keys() :
                        if site not in sites_dict[location] and len(sites_dict[location]): continue
                        for product in aligned_matchups_dictionary[location][site][sensor][atm_cor][insitu_remote].keys():
                            aligned_matchups_dictionary_combined[location][sensor][atm_cor][insitu_remote][product].extend(aligned_matchups_dictionary[location][site][sensor][atm_cor][insitu_remote][product])  

    #Plot matchups
    if plotting_logic in ['matchups_combined','all']: 
        plot_matchups(aligned_matchups_dictionary,limits,sites_dict = sites_dict,
                  aligned_matchups_dictionary_combined=aligned_matchups_dictionary_combined)


    if plotting_logic in [ 'matchup_sites','all']: 
        plot_matchups(aligned_matchups_dictionary,limits,sites_dict = sites_dict)

