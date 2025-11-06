from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import rasterio, os, pickle
from datetime import datetime,timedelta
from PIL import Image
from pathlib import Path
import numpy as np
import pandas as pd
def datetime_from_SID(SID,sensor):
    SID_dt = SID.split('_')[1]
    if sensor == 'MOD':    date_format = "%Y%j%H%M%S"
    if sensor == 'VI' :    date_format = "%Y%m%dT%H%M%S"
    SID_dt = datetime.strptime(SID_dt,date_format)
    return SID_dt


def create_gif(image_paths,gif_location, output_gif_path,percent_limit):
    images = [Image.open(gif_location+image_path) for image_path in image_paths if float(image_path.split('_')[-1].split('.')[0])>percent_limit ]
    images[0].save(
        output_gif_path,
        save_all=True,
        append_images=images[1:],
        optimize=False,
        duration=100,
        loop=0 
    )

def plot_basemap(pickled_figure_name,bounds,products):
    ll_lon,ur_lon,ur_lat,ll_lat = bounds
    map_base_list = []
    if not os.path.exists(pickled_figure_name) :
        #fig = plt.figure()
        fig, axes = plt.subplots(1, len(products), figsize=(4*len(products), 4))
        for ax in axes:
            map_base = Basemap(llcrnrlon=ll_lon,llcrnrlat=ll_lat,urcrnrlon=ur_lon,urcrnrlat=ur_lat, epsg=4326,ax=ax)
            map_base.arcgisimage(service='World_Imagery', xpixels = 1500, verbose= True)
            map_base_list.append(map_base)
        with open(pickled_figure_name, "wb") as f:
            pickle.dump([fig,axes,map_base_list], f, protocol=-1)

    else:
        with open(pickled_figure_name, 'rb') as f:
            [fig,axes,map_base_list] = pickle.load(f)
    return fig,axes,map_base_list

def overlay_sampling_stations(fig,axes,map_base,site):
    lats = [-33.836111]
    lons = [18.489167]
    labels = ['RV1']
    # Convert coordinates to map projection
    x, y = map_base[0](lons, lats)

    # Plot points
    map_base[0].plot(x, y, 'ro', markersize=8)  # 'ro' for red circles

    # Add labels to points
    for label, xpt, ypt in zip(labels, x, y):
        plt.text(xpt + 100000, ypt + 100000, label, fontsize=9) # Adjust offset as needed


    plt.savefig(f'/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Plots/lat_lons/{site}.png',dpi=600)

def plot_lat_lon_points(site,regional_bounds):
    products=['lat','lon']
    ll_lon,ur_lon,ur_lat,ll_lat = regional_bounds[site]
    pickled_figure_name = f"fig_{ll_lon}_{ur_lon}_{ur_lat}_{ll_lat}.pkl"
    fig,axes,map_base = plot_basemap(pickled_figure_name,regional_bounds[site],products)
    overlay_sampling_stations(fig,axes,map_base,site)

def find_nearest_lat_lon(lat_grid, lon_grid, target_lat, target_lon):
    """Find the nearest latitude and longitude in a 2D grid.
    Args:
         lat_grid (numpy.ndarray): 2D array of latitudes.
         lon_grid (numpy.ndarray): 2D array of longitudes.
         target_lat (float): Target latitude.
         target_lon (float): Target longitude.
   
    Returns:
    tuple: The nearest latitude and longitude values.
    """
   
    # Calculate the absolute difference between target and grid points
    lat_diff = np.abs(lat_grid - target_lat)
    lon_diff = np.abs(lon_grid - target_lon)
  
    # Calculate the combined distance using Euclidean distance
    distance = np.sqrt(lat_diff**2 + lon_diff**2)
   
    # Find the index of the minimum distance
    min_index = np.unravel_index(np.argmin(distance), distance.shape)
   
    # Return the nearest latitude and longitude
    return lat_grid[min_index], lon_grid[min_index], min_index

def load_in_situ(in_situ_source,parsed_loc):
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
    return msi_df

def convert_sid_datetime(sid,sensor):
    start_stop_format = {'OLCI': [16,30,'%Y%m%dT%H%M%S'],
                         'MSI' : [11,25,'%Y%m%dT%H%M%S'],
                         'MOD' : [4,17,'%Y%j%H%M%S'],
                         'VI'  : [4,19,'%Y%m%dT%H%M%S'],}
    start,stop,format_ = start_stop_format[sensor]
    sid_datetime       = pd.to_datetime(str(sid)[start:stop], format=format_)
    sid_dt             = pd.Series(sid_datetime).dt.date#sid.datetime.dt.date
    return sid_dt[0]

def plot_products(current_image,tifs_folder,sensor,year,bounds,in_situ_data):
    
    
    gif_image_folder  = Path(tifs_folder).parent.joinpath('gif').joinpath(f'{year}')
    SID               = current_image.split('.')[0].split('/')[-1]
    out_str           = str(gif_image_folder.joinpath( SID + '.png'))
    available_imagery = os.listdir(gif_image_folder) if os.path.exists(gif_image_folder) else []
    if any(SID in available_image for available_image in available_imagery): return

    #with rasterio.open("AQV_2016240205500_A2016240205500_l2gen_chl_tss_cdom.tif") as src:
    #    data = src.read(1)
    #    transform = src.transform

    #ll_lon,ur_lon,ur_lat,ll_lat= transform[2], transform[2] + transform[0] * data.shape[1],transform[5], transform[5] + transform[4] * data.shape[0]
    ll_lon,ur_lon,ur_lat,ll_lat = bounds
    pickled_figure_name = f"fig_{ll_lon}_{ur_lon}_{ur_lat}_{ll_lat}.pkl" 
    products = ['chl','tss','cdom']
    #plt.figure()
    fig,axes,map_base = plot_basemap(pickled_figure_name,bounds,products)

    from rasterio.plot import show
    import xarray as xr
    from affine import Affine
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from matplotlib import colors
    import numpy as np
    from pylab import cm
    current_OLCI_im = tifs_folder + current_image #"AQV_2016240205500_A2016240205500_l2gen_chl_tss_cdom.tif" ##available_filenames_OLCI_MSI_sorted[current_map_number]

    xarr = xr.open_rasterio(current_OLCI_im)
    transform = Affine.from_gdal(*xarr.attrs['transform'])
    #Create meshgrid from geotiff
    nx, ny = xarr.sizes['x'], xarr.sizes['y']
    x = xarr['x']
    y = xarr['y']
    bounds  = {
        'chl' : (1,  100),
        'tss' : (1,  100),
        'pc'  : (0.1,  100),
        'cdom': (0.1, 3),
        'zsd' : (0.1,  10),
    }
    product_name_ins_dict = {'chl':'chla','tss':'tss','cdom':'cdom'}
    labels  = {'chl':'Chlorophyll $[mg/m^3]$','tss':'TSS $[mg/m^3]$','cdom':'CDOM $[m^-1]$'}
    #MODIS/VIIRS: Chl,TSS,aCDOM443,aCDOM555,aNAP443,aNAP555,aph443,aph488,aph555,aph667
    for i,product in enumerate(xarr.variable.data):
        if i>2: continue
        output_data = xarr.variable.data
        percent_finite = 100*sum(sum(np.isfinite(output_data[i])))/output_data[i].size # 100*sum(np.isfinite(output_data[i]))/output_data[i].size
        #if percent_finite <0.05:
        #    print(SID,percent_finite)
        #    return
        #output_data = np.ma.masked_where(np.logical_or(output_data>1000, output_data<0.1),output_data).filled(np.nan) #masks the input data
        product_name = products[i]
        vmin, vmax = bounds[product_name]
        im = axes[i].pcolor(x,y,output_data[i], cmap='turbo',norm=colors.LogNorm(vmin=vmin,vmax=vmax))
        #target_lat,target_lon,matchup_value = (38,-119,50)
        lon_grid = np.tile(x.values, (len(y.values), 1))
        lat_grid = np.tile(y.values, (len(x.values),1)).T
        #x_lat,y_lon,z = find_nearest_lat_lon(lat_grid, lon_grid, target_lat, target_lon)
        circle_size = 45
        circle_size_outer = circle_size*8/7
    
        if len(in_situ_data):
            for row in in_situ_data.iterrows():
                product_name_ins = product_name_ins_dict[product_name]
                if product_name_ins in row[1].keys():
                    target_lat,target_lon,matchup_value = (row[1]['lat'],row[1]['lon'],row[1][f'{product_name_ins}'])
                    x_lat,y_lon,z = find_nearest_lat_lon(lat_grid, lon_grid, target_lat, target_lon)
                    y_lon = target_lon
                    x_lat = target_lat
                    map_base[i].scatter([y_lon], [x_lat], c=[np.log10(matchup_value)], vmin=np.log10(vmin), vmax=np.log10(vmax), s=circle_size_outer, cmap=cm.turbo,edgecolors='fuchsia',linewidth=0.5,zorder=99)
                    map_base[i].scatter([y_lon], [x_lat], c=[np.log10(matchup_value)], vmin=np.log10(vmin), vmax=np.log10(vmax), s=circle_size, cmap=cm.turbo,edgecolors='black',linewidth=0.5,zorder=100)

        plt.colorbar(im, ax=axes[i],fraction=0.037, pad=0.04)
        label      = labels[product_name]
        axes[i].set_title(f'{label}',weight='bold')

    #SID = current_image.split('.')[0].split('/')[-1]
    plt.suptitle(str(datetime_from_SID(SID,sensor))+ '\n' + str(SID),weight='bold')
    plt.tight_layout()
    os.makedirs(gif_image_folder,exist_ok = True)
    percent_finite = str(np.round(percent_finite,2))
    print(SID)
    plt.savefig(str(gif_image_folder.joinpath( SID + f'_{percent_finite}' + '.png')),dpi=100)
    if len(in_situ_data):
        gif_image_folder_insitu = gif_image_folder.parent.joinpath('insitu')
        os.makedirs(gif_image_folder_insitu,exist_ok = True)
        plt.savefig(str(gif_image_folder_insitu.joinpath( SID + f'_{percent_finite}' + '.png')),dpi=100)
    plt.close()
    

regional_bounds = {
        'SaltonSea_1999_2025': [-116.39180755615234, -115.39802551269531, 33.69487762451172, 32.87944793701172], #ll_lon,ur_lon,ur_lat,ll_lat
        'MonoLake_1999_2025' : [-119.20478131601323, -118.87079318456,    38.12611342024058, 37.89818034436002],
        'GSL_1999_2025'      : [-113.17365348430634, -112.09150019062751, 41.76025894471491, 40.58184618240213],
        'RV'           : [18.47598622238378,    18.509111692429665, -33.831524024147896,-33.8488059136944,],
        'TW'           : [19.091221546640977,   19.3089150409756,   -33.96208212029914, -34.09677305533565,],
        'ZK'           : [18.4975026019921,     18.525725379014702, -34.04827259596211, -34.07327335242889,],
        'KR'           : [19.276121761276944,   19.423882659634433, -34.39354947944188, -34.4340556316619,],
        }

#for site in ['RV','TW','ZK','KR']:
#    plot_lat_lon_points(site,regional_bounds)

#assert(0)
#Define directory
base_location = '/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Gathered/' 
region        =  'GSL_1999_2025' #'MonoLake_1999_2025' #'SaltonSea_1999_2022'
plot_products_bool = True
#sensor        = 'MOD'
#ac            = 'l2gen'
#tif_location  = f'/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Gathered/{region}/{sensor}/{ac}/Imagery/tifs/'
region_dir    = f'/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Gathered/{region}/'
valid_sensors = ['MOD','VI','OLCI','MSI','OLI','PACE','EMIT']
valid_acs     = ['l2gen','polymer','acolite','aquaverse']

sensors = os.listdir(region_dir)
sensors = sorted([sensor for sensor in sensors if sensor in valid_sensors])

#Mono Lake
#in_situ_source = '/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/Insitu/terminalLakes_25.csv'

#GSL
if region == 'MonoLake_1999_2025' : in_situ_loc  = "/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/Insitu/terminalLakes_25.csv"

if region == 'SaltonSea_1999_2025': in_situ_loc  = "/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/Insitu/combined_Salton_Sea_BOR_Spaulding_2.csv"

if region == 'GSL_1999_2025'      : in_situ_loc  = "/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/Insitu/gsl_usgs_utahdeq00_22_formatted.csv"


parsed_loc  = f"/run/cephfs/m2cross_scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Insitu/{region}/parsed.csv"
 

in_situ_df = load_in_situ(in_situ_loc,parsed_loc)

days_difference = 1

print(sensors)
for sensor in sensors:
    sensor_dir = region_dir + f'{sensor}/'
    acs        = os.listdir(sensor_dir)
    acs        = [ac for ac in acs if ac in valid_acs]
    print(acs)
    for ac in acs:
        tif_location  = f'/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Gathered/{region}/{sensor}/{ac}/Imagery/tifs/'
        tifs = os.listdir(tif_location)
        for year in range(2000,2026):
            tifs_year = sorted([tif for tif in tifs if '_RGB' not in tif and f'AQV_{year}' in tif])
            if not len(tifs_year): continue
            for tif in tifs_year:
                #identify matching in situ data
                satellite_date  = convert_sid_datetime(tif,sensor) 
                matching_ins    = in_situ_df[abs(in_situ_df['ins_date'] - satellite_date) < timedelta(days=days_difference)]
                
                if plot_products_bool: plot_products(tif,tif_location,sensor,year,regional_bounds[region],matching_ins) 
            gif_year_dir             = f'/tis/m2cross/scratch/f003/roshea/matchup_pipeline_dev_test/roshea/SCRATCH/Gathered/{region}/{sensor}/{ac}/Imagery/gif/{year}/'
            gif_tifs                 = sorted(os.listdir(gif_year_dir))
            gif_tif_percent_coverage = sorted([float(percent.split('_')[-1].split('.png')[0]) for percent in gif_tifs])#sorted([float(percent.split('_')[-1]) for percent in gif_tifs])
            percent_limit            = np.percentile(gif_tif_percent_coverage, 50)
            create_gif(gif_tifs, gif_year_dir, str(Path(gif_year_dir).parent.joinpath( f'{region}_{sensor}_{ac}_{year}_gif.gif')),percent_limit)


