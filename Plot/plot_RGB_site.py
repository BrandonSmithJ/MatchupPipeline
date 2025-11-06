from pipeline.utils.find_nearest_lat_lon import find_nearest_lat_lon
from pipeline.utils.add_scale import add_scale
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import numpy as np
title_dictionary = {'KR': 'Klein River Lagoon', 'RV': 'Rietvlei Dam (Urban)','TW': 'Theewaterskloof Dam', 'ZK': 'Zeekoevlei Wetland (Urban)'}


def overlay_sites(im_lat,im_lon,rgb,extent,site_name,sites_filename='/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Gathered/PC_1_CyanoSCape/MSI/acolite/Imagery/pngs/AQV_20231017_S2A_MSIL1C_20231017T081931_N0509_R121_T34HBH_20231017T101938_acolite_rgb_sites.png'):
    plt.figure()
    plt.imshow(rgb ,extent=extent)

    #target_lat = -34.41316891397631  #-34.056111
    #target_lon =  19.361395499742944 #18.513611

    cyano_sites = '/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/Insitu/CyanoscapeSites_reformatted.csv'
    cyano_sites = pd.read_csv(cyano_sites)
    #site_name   = 'KR'
    sites       = [ site_key for site_key in cyano_sites['station'].values if site_name in site_key]
    cyano_sites = cyano_sites[cyano_sites['station'].isin(sites)]
    target_lat  = list(cyano_sites['lat'])
    target_lon  = list(cyano_sites['lon'])
    target_stations = list(cyano_sites['station'])
    colors_dict = {'1': 'xkcd:electric blue', '2':'xkcd:fuchsia' ,'3': 'xkcd:bright orange','4': 'xkcd:light olive',}
    shapes_dict = {'A': '$A$', 'B': '$B$' , 'C': '$C$', 'D': '$D$' , 'E': '$E$' ,'F': '$F$'}
    lat_lon_colors = [colors_dict[station[2]] for station in target_stations]
    lat_lon_shapes = [shapes_dict[station[3]] for station in target_stations]

    plt.grid(True)
    plt.grid(color='xkcd:grey', linestyle='--', linewidth=0.5)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=45, ha='right')
    title_text=''
    if site_name in title_dictionary.keys(): title_text = title_dictionary[site_name] 
    dt = sites_filename.split('/')[-1].split('_')[3]
    dt = datetime.strptime(dt.split('T')[0], '%Y%m%d')
    dt_str = dt.strftime("%B %d, %Y")
    title_text = title_text+f' on {dt_str}'
    plt.title(title_text) 
    #x_lat,y_lon,z = find_nearest_lat_lon(im_lat, im_lon, target_lat, target_lon)

    #plt.scatter([z[1]], [z[0]], c='r', s=20, edgecolors='k',linewidth=0.5,zorder=99)
    for i,j in enumerate(target_stations):
        plt.scatter(target_lon[i], target_lat[i], c=lat_lon_colors[i],marker=lat_lon_shapes[i], s=40, edgecolors='w',linewidth=0.15,zorder=99)
    #degree_diff = np.abs(np.max(im_lon) - np.min(im_lon))
    #degree_diff*100

    add_scale(plt.gca(),im_lon,im_lat,multiple_of=1)
    plt.tight_layout()
    plt.savefig(sites_filename,dpi=600)
    plt.close()
