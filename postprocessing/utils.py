#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 14:46:39 2023

@author: roshea
"""
import numpy as np
from collections import defaultdict as dd 
from pathlib import Path
import datetime, pickle ,os, time
from datetime import timedelta
import xarray as xr
import pandas as pd
from pyproj import Transformer
import matplotlib.pyplot as plt
 

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

#Correct acdom 400 --> 440
def adjust_cdom(value,desired_wavelength=440,reference_wavelength=400,S=0.018):
    return value* np.exp(-S*(desired_wavelength-reference_wavelength))
   
    
def convert_CyAN(DN):
    if DN >=253: return np.nan
    CI_cyano = 10**((3/250)*DN-4.2)
    chla = 4000 * CI_cyano + 10
    return chla

def is_float(element: any) -> bool:
    #If you expect None to be passed:
    if element is None: 
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False

def find_filenames(sensor, basefile,atmospheric_correction,subfile='',NOAA_product=''):
    os.chdir(basefile if subfile in [ 'cyan','NOAA'] else basefile+'/'+sensor)
    file_list = sorted(Path().resolve().rglob(  "L*.tif" if subfile == 'cyan' else f"*{NOAA_product}/*.nc4" if subfile == 'NOAA' else "*"+atmospheric_correction+"*.tif"))
    os.chdir(basefile)
    return file_list

# Function to calculate datetime from input filename
def extract_datetime(fname,sensor,subfile = ''):
    if subfile == 'cyan': 
        datetime_convertor = '%Y%j'
        return [datetime.datetime.strptime(file.stem.split('.')[0].replace('L',''),datetime_convertor) + timedelta(hours=12) for file in fname]
    if subfile == 'NOAA': 
        datetime_convertor = '%Y%j'
        return [datetime.datetime.strptime(file.stem.split('.')[0].replace('L','').replace('A','').replace('B',''),datetime_convertor) + timedelta(hours=12) for file in fname]
    
    if          sensor == 'MOD': datetime_convertor = '%Y%j%H%M%S'
    if sensor in [ 'VI','OLCI']: datetime_convertor = '%Y%m%dT%H%M%S'
    
    return [datetime.datetime.strptime(file.stem.split('_')[1],datetime_convertor) for file in fname]


def load_insitu(csv_filename,col_name_dictionary,header = 0,min_datetime='2016/01/01',drop_rows=[],products= ['datetime','chl','tss','cdom','pc'],WQP_names={}):
    erie_df = pd.read_csv(csv_filename,
                     header=header,usecols=col_name_dictionary.keys())
    
    erie_df = erie_df.rename(columns=col_name_dictionary)
    
    if len(drop_rows): 
        if drop_rows[2] == '==': erie_df.drop(erie_df[erie_df[drop_rows[0]] == drop_rows[1]].index, inplace = True)
        if drop_rows[2] == '>=': erie_df.drop(erie_df[erie_df[drop_rows[0]] >= drop_rows[1]].index, inplace = True)

    erie_df             = erie_df[erie_df['time'].notna()]
    erie_df['datetime'] = pd.to_datetime(erie_df.date.astype(str) + ' ' +erie_df.time.astype(str))
    erie_df.drop(erie_df[erie_df['datetime'] <= pd.to_datetime(min_datetime)].index, inplace = True)
    
    erie_sites          = erie_df['station'].value_counts().keys()[erie_df['station'].value_counts().values>10]
    erie_sites_latlon   = {}
    erie_sites_products = {site: {} for site in erie_sites}
    for erie_site in erie_sites:
        out                          = erie_df.groupby('station').get_group(erie_site).mean()
        erie_sites_latlon[erie_site] = [out['lat'],out['lon']]
        for product in products:
            if 'Parameter' in col_name_dictionary.keys():
                if product == 'datetime':
                    erie_sites_products[erie_site][product] = erie_df.groupby('station').get_group(erie_site)[product]
                    continue
                
                station_vals  = erie_df.groupby('station').get_group(erie_site)
                concentration = station_vals['concentration'].copy()
                concentration[station_vals[station_vals[col_name_dictionary['Parameter']] != WQP_names[product]].index] = np.nan
                erie_sites_products[erie_site][product] = concentration

            else:
                erie_sites_products[erie_site][product] = erie_df.groupby('station').get_group(erie_site)[product]
        
    print(erie_df)
    return erie_sites_products,erie_sites_latlon

def align_matchups(insitu,matchup_dictionary,hours={"Erie_2016_2023":4,"Chesapeake_Bay_2016_2023":4}):
    for location in insitu.keys():
        insitu_location = insitu[location]
        
        for site in insitu_location.keys():
            for sensor in matchup_dictionary[location][site].keys():
                for atm_cor in matchup_dictionary[location][site][sensor].keys():
                    # if atm_cor not in ['NOAA','CyAN']: continue
                    print(location, site, sensor, atm_cor)
                    daily_vals         = matchup_dictionary[location][site][sensor][atm_cor]['daily']
                    daily_DT           = matchup_dictionary[location][site][sensor][atm_cor]['daily_DT']
                    for product in daily_vals.keys():
                        if type(daily_vals[product][0]) == list:
                            daily_vals[product] = [val[0] for val in daily_vals[product]]
                    if daily_vals == {} or daily_DT == {}: continue
                    insitu_remote_dict = {'insitu': {product: []  for product in insitu_location[site].keys()},
                                          'remote': {product: []  for product in insitu_location[site].keys()},}
                    timedelta_array = {}
                    argmin_timedelta_array = {}
                    for i,insitu_date in enumerate(insitu_location[site]['datetime']):
                        if type(daily_DT) == dict:
                            products = daily_DT.keys()
                        else:
                            products = ['chl','tss','cdom','pc']
                        for product in products:
                            daily_DT = daily_DT[product] if type(daily_DT) == dict else daily_DT
                            timedelta_array[product]        = [abs(pd.Timestamp(remote_date) - pd.Timestamp(insitu_date)) for remote_date in  daily_DT]
                            argmin_timedelta_array[product] = np.argmin(timedelta_array[product])
                        
                        for product in insitu_location[site].keys():
                            if  product != 'datetime' :
                                if timedelta_array[product][argmin_timedelta_array[product]] < pd.Timedelta(hours=hours[location]) and product in daily_vals.keys():
                                    insitu_remote_dict['insitu'][product].append(float( insitu_location[site][product].values[i]) if is_float(insitu_location[site][product].values[i]) else np.nan)
                                    insitu_remote_dict['remote'][product].append(float(daily_vals[product][argmin_timedelta_array[product]]) if is_float(daily_vals[product][argmin_timedelta_array[product]]) else np.nan)
                          
                    matchup_dictionary[location][site][sensor][atm_cor]['insitu'] = insitu_remote_dict['insitu']
                    matchup_dictionary[location][site][sensor][atm_cor]['remote'] = insitu_remote_dict['remote']
    return matchup_dictionary

def search_lat_lon(xarr,desired_lat,desired_lon,search_region=0.003,tss_or_chl='chl'):
    distance = (np.abs(xarr.lat-desired_lat)**2 + np.abs(xarr.lon-desired_lon)**2)**0.5
    valid_estimate_locations = xr.where(distance < search_region,True,False)
    
    valid_estimates = xarr.tsm_nn.values[0][0][valid_estimate_locations] if tss_or_chl=='tss' else xarr.chlor_a.values[0][0][valid_estimate_locations]
    if np.all(np.isnan(valid_estimates)):
        return np.nan
    return np.nanmedian(valid_estimates)

def pull_timeseries(available_filenames,pickle_filename,latlon_keys,overwrite=True):
    if os.path.exists(pickle_filename) and not overwrite : #and 'Chesapeake' not in str(pickle_filename) or  'NOAA' not in str(pickle_filename)
        with open(pickle_filename,'rb') as handle:
            sites_dictionary =  pickle.load(handle)
            sites_dictionary=sites_dictionary[0]
    else:
        sites_dictionary = {key: [] for  key, lat_lon in latlon_keys.items()}
        for i,filename in enumerate(available_filenames): 
            t = time.time()
            xarr = xr.open_rasterio(filename) if 'NOAA' not in str(filename) else xr.open_dataset(filename,engine='netcdf4')

            for key, lat_lon in latlon_keys.items():
                lat,lon = lat_lon
                if 'NOAA' in str(filename):
                    val  = [search_lat_lon(xarr,lat,lon,tss_or_chl =  'tss' if 'tss' in str(filename) else  'chl')]
                    if False and not np.isnan(val[0]):
                        print("time to plot",val[0])
                        plt.imshow(xarr.chlor_a.values[0][0],extent = (np.amin(xarr.lon[0,:].values), np.amax(xarr.lon[0,:].values), np.amin(xarr.lat[:,0].values), np.amax(xarr.lat[:,0].values) ) , interpolation = 'nearest')
                        plt.scatter(lon,lat,1,'r')
                        print("Waiting for next")
                        plt.close()
                    sites_dictionary[key].append(val) 
                    continue
                
                if xarr.x.values[0]>180: #xarr.transform[2]
                    # transformer = Transformer.from_crs(xarr.crs,"epsg:4326",)
                    # tuple_coordinates = [transformer.transform(x,y) for x,y in zip(xarr.x.values,xarr.y.values)]
                    # y,x = list(map(list,zip(*tuple_coordinates)))
                    # xarr = xarr.assign_coords(coords={'x':x,'y':y})
                    transformer_flipped = Transformer.from_crs("epsg:4326",xarr.crs,)
                    lat_lon = transformer_flipped.transform(lat,lon)
                    lon = lat_lon[0]
                    lat = lat_lon[1]
                val = xarr.sel(x=lon, y=lat, method="nearest")
                
                if 'Chesapeake' in str(filename) and val.values[0] not in [255,254,0] and False : #key =='CB2.2': #val.values[0] not in [255,0] 
                    print("time to plot",val.values[0])
                    xarr[0].plot()
                    plt.scatter(lon,lat,1,'r')
                    print("Waiting for next")
                    plt.close()
                sites_dictionary[key].append(list(val.values)) 
            if not i%10: print(i,time.time()-t)
        
        if overwrite:
            with open(pickle_filename,'wb') as handle:
                pickle.dump([sites_dictionary],handle)  
    return sites_dictionary