# -*- coding: utf-8 -*-
"""
File Name:      create_matchup_datasets_from_sources.py
Description:    This code file will be used to combine matchup Rrs from FWS groups matchup pipeline and in situ Chla
                measurements


Date Created:   October 29th, 2024
"""
__author__ = "arunsaranath"

import numpy as np
import pandas as pd
import re
from tqdm import tqdm
from pathlib import Path
import warnings, datetime
warnings.filterwarnings("ignore")


# Define a function to calculate Haversine distance
def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c
    return distance

def create_matchup_datasets_from_sources(in_situ_source,satellite_retrievals_source,sensor, output_name=None,distance_lim_km=1,days_difference=1,dataset='',parsed_loc=''):
    """
    This function will be used to matchup the satellite rrs with the in situ measurements to create a satellite matchup
    datasets which can be used for analysis.

    :param in_situ_source: [string]
    A file location where the in situ measurements are available. This function assumes that the file is delimited and contains
    columns corresponding to the insitu latitude and longitude.


    :param satellite_retrievals_source: [string]
    A file location where the satellite Rrs are available. This function assumes that the file is delimited and contains
    columns corresponding to the insitu latitude and longitude.

    :param sensor: string (Default: OLCI)
    The sensor which we are using at this point

    :param output_name: string (Default: parsed_matchups_{sensor}.csv)
    :return:
    """

    '------------------------------------------------------------------------------------------------------------------'
    'PREVIOUS MSI MATCHUPS'
    '------------------------------------------------------------------------------------------------------------------'
    "The available in situ measurement locations are"
    msi_ins_loc = in_situ_source 
    "Read the existing insitu measurements into a pandas dateframe"
    msi_df = pd.read_csv(msi_ins_loc)
    "The available in situ measurement locations are"
    'Include a column with only the date, rather than datetime'
    msi_df['ins_date'] = pd.to_datetime(msi_df['date']).dt.date
    
    stations_dict = { 'lat' : {'SS0003' :   33.258889, 'SS0002' :   33.342028,'SS0001' :   33.342028},
                      'lon' : {'SS0003' : -115.737389, 'SS0002' : -115.837278,'SS0001' : -115.837278},
                    }
    #load in situ CSV lat/lons and assign them
    in_situ_lat_lon = pd.read_csv(parsed_loc)

    for row in in_situ_lat_lon.iterrows():
        print(stations_dict)
        stations_dict['lat'].update( {row[1]['uid']:float(row[1]['lat'])})
        stations_dict['lon'].update( {row[1]['uid']:float(row[1]['lon'])})

    if 'lat' not in msi_df.keys():
        msi_df['lat']=[np.nan] * len(msi_df)
    if 'lon' not in msi_df.keys():
        msi_df['lon']=[np.nan] * len(msi_df)
    if 'station' in msi_df.keys():
        msi_df.loc[msi_df['lat'].isnull(), 'lat'] = msi_df['station'].map(stations_dict['lat'])[msi_df['lat'].isnull()] #stations_dict[df['station']][0]
        msi_df.loc[msi_df['lon'].isnull(), 'lon'] = msi_df['station'].map(stations_dict['lon'])[msi_df['lon'].isnull()] 

    'Sort by latitude for better visualization'
    msi_df = msi_df.sort_values(by='lat')


    '------------------------------------------------------------------------------------------------------------------'
    'RRS spectra for this specific location'
    '------------------------------------------------------------------------------------------------------------------'
    rrs_df = pd.read_csv(satellite_retrievals_source)
    "Find columns containing 'Rrs'"
    cols_with_rrs = [col for col in rrs_df.columns if 'Rrs(' in col]
    AQV_prods     = [key for key in rrs_df.columns  if 'AQV' in key and 'valid' not in key]
    if not cols_with_rrs:
        cols_with_rw= [col for col in rrs_df.columns if re.match(r'^Rw\d+$', col)]
        rrs_df = rrs_df[rrs_df[cols_with_rw].isna().mean(axis=1) <= 0.5]

        cols_with_rrs = []
        for item in cols_with_rw:
            key = item.replace('Rw', 'Rrs(') + ')'
            rrs_df[key] = rrs_df[item] / np.pi
            cols_with_rrs += [key]
    else:
        'Drop the rows where the Rrs values are mostly Nan'
        rrs_df = rrs_df[rrs_df[cols_with_rrs].isna().mean(axis=1) <= 0.5]


    'Include a column with only the date, rather than datetime'
    #rrs_df['insitu_datetime'] = pd.to_datetime(rrs_df['scene_id'].str[16:30])
    #from .utils import extract_datetime
    #extract_datetime(available_filenames,sensor=sensor)
    start_stop_format = {'OLCI': [16,30,'%Y%m%dT%H%M%S'],
                         'MSI' : [11,25,'%Y%m%dT%H%M%S'],
                         'MOD' : [1,14,'%Y%j%H%M%S'],
                         'VI'  : [0,14,'%Y%m%dT%H%M%S'],
                         'OCI' : [9,23,'%Y%m%dT%H%M%S'],

                         }
    start,stop,format_ = start_stop_format[sensor] 
    if sensor == 'VI':
        rrs_df['scene_id'] = rrs_df['scene_id'].str.split('.', expand=True)[1]

    rrs_df['scene_datetime'] = pd.to_datetime(rrs_df['scene_id'].str[start:stop], format=format_)
    rrs_df['insitu_date'] = rrs_df['scene_datetime'].dt.date

    if 'window_lat' not in rrs_df.columns:
        k1 = 'lat' #'latitude'
        k2 = 'lon' #'longitude'
    else:
        k1 = 'window_lat'
        k2 = 'window_lon'


    'Create a dataframe to hold the final matchups'
    col_names  = ['Samp ID', 'rrs_lat', 'rrs_lon', 'Distance'] + cols_with_rrs + ['ins_chl', 'ins_tss']
    match_df = pd.DataFrame(columns=col_names)
    samp_id = 1
    miss_ctr = 0

    'Iterate over available rows'
    for index, row in tqdm(rrs_df.iterrows()):
        'Find the in situ measurements on this date'
        #formula = abs(msi_df['ins_date'] - row['insitu_date']) < datetime.timedelta(days=days_difference)
        msi_loc_date_df = msi_df[abs(msi_df['ins_date'] - row['insitu_date']) < datetime.timedelta(days=days_difference)]

        'Set a variable to hold the distance between the in situ measurement and the matchup measurement from the two' \
        'sources'
        distance = np.inf
        if msi_loc_date_df.size != 0:
            'Find the distance between in situ measurements and the rrs locations'
            msi_loc_date_df['distance'] = msi_loc_date_df.apply(
                lambda ch_row: haversine(row[k1], row[k2], ch_row['lat'], ch_row['lon']), axis=1)
            'Reset indicies to enable search'
            msi_loc_date_df = msi_loc_date_df.reset_index(drop=True)
            'Track lowest distance from this set'
            distance = msi_loc_date_df['distance'].min()

            'Select the closest measurement from either source'
            if not np.isnan(msi_loc_date_df['distance'].idxmin(skipna=True)):
                chosen_insitu_row = msi_loc_date_df.loc[msi_loc_date_df['distance'].idxmin()]
            else:
                continue



        'Add this to the matchup data'
        if distance<= distance_lim_km:
            'Get the Chla and TSS values from that location'
            samp_chla = chosen_insitu_row['chla']
            samp_tss = chosen_insitu_row['tss'] if 'tss' in chosen_insitu_row.keys() else np.nan

            'Get the Rrs from rrs_df'
            samp_rrs = row[cols_with_rrs]
            samp_AQV = row[AQV_prods]
            'Create the new row'
            new_row = {
                'Samp ID': row['uid'],
                'rrs_lat': row[k1],
                'rrs_lon': row[k2],
                'insitu_lat': chosen_insitu_row['lat'],
                'insitu_lon': chosen_insitu_row['lon'],
                'Ins Date': pd.to_datetime(chosen_insitu_row['ins_date']),
                'Rrs Date': row['scene_datetime'],
                'ins_chl': samp_chla,
                'ins_tss': samp_tss,
                'Distance': distance,
            }

            'Add rrs to dictionary'
            for item in cols_with_rrs:
                new_row[item] = samp_rrs[item]
            for product in AQV_prods:
                new_row[product] = samp_AQV[product]

            match_df = pd.concat([match_df, pd.DataFrame([new_row])], ignore_index=True)

        else:
            miss_ctr += 1


        samp_id += 1


    'If an output name is provided save the file'
    if output_name != None:
        match_df.to_csv(output_name, index=False)
    print("input in situ has: ", len(msi_df), 'measurements')
    print("output df has: ", len(rrs_df),'retrievals')
    print("matchup df has: ", len(match_df), 'samples')
    return match_df

#def main():
if __name__ == "__main__":
    "Create the matchup dataset"
    dataset      = "PC_1_Chintan_matchups" # "SaltonSea_1999_2025" #"SaltonSea_1999_2022" #'PC_1_MS_SouthAfricanDams'
    sensor       = "OCI" #"MOD"
    ac_proc      = "l2gen"
    sat_name_dict= {'MOD':'MODIS','VI':'VIIRS','OLCI':'OLCI',"OCI":"OCI"}
    sat_name     = sat_name_dict[sensor]

    'Mono Lake'
    if dataset == 'MonoLake_1999_2025': in_situ_loc  = "/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/Insitu/terminalLakes_25.csv"

    if dataset == 'SaltonSea_1999_2025': in_situ_loc  = "/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/Insitu/combined_Salton_Sea_BOR_Spaulding_2.csv"
    
    if dataset == 'GSL_1999_2025': in_situ_loc  = "/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/Insitu/gsl_usgs_utahdeq00_22_formatted.csv"

    if dataset == 'PC_1_Chintan_matchups': in_situ_loc  = "/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/Insitu/Chintan_field_data_with_Chla_forRyan_renamed.csv"


    satellite_retrievals_loc   = f'/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Gathered/{dataset}/{sensor}/{ac_proc}/{dataset}_{sensor}_{ac_proc}_Matchups.csv'
    #src_loc  = f"D:\\Matchup_data\\Sat_sources\\{sensor}\\PC_2_DA_matchups_{sensor}_{ac_proc}.csv"
    op_loc       = f"/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/matchups/parsed_matchups_{dataset}_{sensor}_{ac_proc}.csv"
    parsed_loc  = f"/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/{dataset}/parsed.csv"
    if not Path(op_loc).exists():
        match_df = create_matchup_datasets_from_sources(in_situ_loc, satellite_retrievals_loc, sensor, output_name=op_loc,days_difference=1,dataset=dataset,parsed_loc=parsed_loc)
    else:
        match_df = pd.read_csv(op_loc)
        print('Using pre-generated matchups')
    'Plot scatterplots'


    from   MDN                        import create_scatterplots_trueVsPred,performance
    #remove 0 estimates
    #match_df    = match_df[~(match_df['AQV_chl'] == 0)]
    #insitu_data = match_df['ins_chl'].values.reshape(-1,1)
    #remote_data = match_df['AQV_chl'].values.reshape(-1,1)
    #difference  = np.abs(remote_data - insitu_data) #100*np.abs(remote_data - insitu_data)/insitu_data 
    #upper_bound = match_df['AQV_chl_uncert_upper'].values.reshape(-1,1) - match_df['AQV_chl_uncert_lower'].values.reshape(-1,1) #100*(match_df['AQV_chl_uncert_upper'].values.reshape(-1,1) - match_df['AQV_chl_uncert_lower'].values.reshape(-1,1))/remote_data 

    short_names_dict = {'chl': r'Chlorophyll-a [$mg~m^{-3}$]',
                        'tss': r'Total Suspended Solids [$g~m^{-3}$]',}
    inp_str = []
    for key in ['chl']:
        match_df    = match_df[~(match_df[f'AQV_{key}'] == 0)]
        insitu_data = match_df[f'ins_{key}'].values.reshape(-1,1)
        remote_data = match_df[f'AQV_{key}'].values.reshape(-1,1)
        difference  = np.abs(remote_data - insitu_data) #100*np.abs(remote_data - insitu_data)/insitu_data
        upper_bound = match_df[f'AQV_{key}_uncert_upper'].values.reshape(-1,1) - match_df[f'AQV_{key}_uncert_lower'].values.reshape(-1,1)
        in_unc_bounds_bool  = np.logical_and(insitu_data>match_df[f'AQV_{key}_uncert_lower'].values.reshape(-1,1), insitu_data< match_df[f'AQV_{key}_uncert_upper'].values.reshape(-1,1))
        percent_within_bounds = round(float(100*sum(in_unc_bounds_bool)/len(in_unc_bounds_bool)),1)

        str1 = (performance(f'', insitu_data, remote_data).replace('|', ''))
        inp_str += [str1.replace('   ', '\n')]
        inp_str[0] = inp_str[0] + f'\nPWUB:  {percent_within_bounds}'

        out = create_scatterplots_trueVsPred(insitu_data, remote_data, short_name=[short_names_dict[key]],
                               x_label=['In Situ Measurements'], y_label=[f'Satellite ({sat_name}) Retrievals'],  inplot_str=inp_str,
                               title="", maxv_b=[3], minv_b=[-1], ipython_mode=False) #,unc_lower = np.squeeze(match_df[f'AQV_{key}_uncert_lower'].values.reshape(-1,1)), unc_upper =  np.squeeze(match_df[f'AQV_{key}_uncert_upper'].values.reshape(-1,1)))
    
    


        out.savefig(f'/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Plots/{dataset}/{dataset}_{sensor}_{ac_proc}_matchup_scatterplot_{key}.png',dpi=600)
    
    #inp_str = []
    #for key in ['chl']:
    #    str1 = (performance(f'', upper_bound,difference).replace('|', ''))
    #    inp_str += [str1.replace('   ', '\n')]
    #out = create_scatterplots_trueVsPred(upper_bound,difference, short_name=[r'Chlorophyll-a Uncertainty [$mg~m^{-3}$]'],
    #                           x_label=['Uncertainty (Upper - lower)'], y_label=['abs(Remote - insitu)'],  inplot_str=inp_str,
    #                           title="MDN prediction performance", maxv_b=[3], minv_b=[-1], ipython_mode=False)

    #out.savefig(f'/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Plots/{dataset}/{dataset}_{sensor}_{ac_proc}_matchup_scatterplot_uncertainty.png',dpi=600)

    print('finished')
