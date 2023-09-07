#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 12:31:08 2023

@author: roshea
"""

import xarray,rasterio,glob
import numpy as np
from osgeo import gdal
from osgeo import osr
import os, sys
from pathlib import Path
from netCDF4 import Dataset

def create_geotiff(products, lon_min, lat_min, lon_max, lat_max,filename = 'exampleGeo_08_13.tif',product_names=['443 nm','483 nm']):
    products_len = np.shape(products)[2]
    lat_count=np.shape(products)[0]
    lon_count=np.shape(products)[1]
    lat_resolution = (lat_max - lat_min)/float(lat_count)
    lon_resolution = (lon_max - lon_min)/float(lon_count)
    geotransform_tuple = (lon_min,lon_resolution,0,lat_max,0,-lat_resolution)
    geotiff_object = gdal.GetDriverByName('GTiff').Create(filename, lon_count,lat_count, products_len, gdal.GDT_Float64)
    geotiff_object.SetGeoTransform(geotransform_tuple)
    spatial_reference_system =osr.SpatialReference()
    spatial_reference_system.ImportFromEPSG(4326)
    geotiff_object.SetProjection(spatial_reference_system.ExportToWkt())
    for i in range(products_len):
        geotiff_object.GetRasterBand(i+1).WriteArray(products[:,:,i])
        geotiff_object.GetRasterBand(i+1).SetDescription(product_names[i])
    geotiff_object.FlushCache()
    geotiff_object = None
    
def mod_angle(value):
    """Returns angle in radians to be between -pi and pi"""
    return (value + np.pi) % (2 * np.pi) - np.pi

@np.vectorize
def utm_to_latlong(easting, northing, zone_number, northern=None):
    K0 = 0.999

    E = 0.00669438
    E2 = E * E
    E3 = E2 * E
    E_P2 = E / (1.0 - E)

    SQRT_E = np.sqrt(1 - E)
    _E = (1 - SQRT_E) / (1 + SQRT_E)
    _E2 = _E * _E
    _E3 = _E2 * _E
    _E4 = _E3 * _E
    _E5 = _E4 * _E

    M1 = (1 - E / 4 - 3 * E2 / 64 - 5 * E3 / 256)

    P2 = (3. / 2 * _E - 27. / 32 * _E3 + 269. / 512 * _E5)
    P3 = (21. / 16 * _E2 - 55. / 32 * _E4)
    P4 = (151. / 96 * _E3 - 417. / 128 * _E5)
    P5 = (1097. / 512 * _E4)

    R = 6378137

    x = easting - 500000
    y = northing

    if not northern:
        y -= 10000000

    m = y / K0
    mu = m / (R * M1)

    p_rad = (mu +
              P2 * np.sin(2 * mu) +
              P3 * np.sin(4 * mu) +
              P4 * np.sin(6 * mu) +
              P5 * np.sin(8 * mu))

    p_sin = np.sin(p_rad)
    p_sin2 = p_sin * p_sin

    p_cos = np.cos(p_rad)

    p_tan = p_sin / p_cos
    p_tan2 = p_tan * p_tan
    p_tan4 = p_tan2 * p_tan2

    ep_sin = 1 - E * p_sin2
    ep_sin_sqrt = np.sqrt(1 - E * p_sin2)

    n = R / ep_sin_sqrt
    r = (1 - E) / ep_sin

    c = E_P2 * p_cos**2
    c2 = c * c

    d = x / (n * K0)
    d2 = d * d
    d3 = d2 * d
    d4 = d3 * d
    d5 = d4 * d
    d6 = d5 * d

    latitude = (p_rad - (p_tan / r) *
                (d2 / 2 -
                  d4 / 24 * (5 + 3 * p_tan2 + 10 * c - 4 * c2 - 9 * E_P2)) +
                  d6 / 720 * (61 + 90 * p_tan2 + 298 * c + 45 * p_tan4 - 252 * E_P2 - 3 * c2))

    longitude = (d -
                  d3 / 6 * (1 + 2 * p_tan2 + c) +
                  d5 / 120 * (5 - 2 * c + 28 * p_tan2 - 3 * c2 + 8 * E_P2 + 24 * p_tan4)) / p_cos

    longitude = mod_angle(longitude + np.radians((zone_number - 1) * 6 - 180 + 3))

    return (np.degrees(latitude),
            np.degrees(longitude))

def GetExtent(ds,min_max = False):
    """ Return list of corner coordinates from a gdal Dataset """
    xmin, xpixel, _, ymax, _, ypixel = ds.GetGeoTransform()
    width, height = ds.RasterXSize, ds.RasterYSize
    xmax = xmin + width * xpixel
    ymin = ymax + height * ypixel
    if min_max: return [[xmin, xmin, xmax, xmax], [ymin, ymax, ymin, ymax]]
    return (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)

def save_nc(inp_file,out_path,products,slices,overwrite,prefix='AQV'):
    ''' Saves products onto the L2 tile'''

    filename = inp_file
    new_fn   = out_path

    if not Path(new_fn).exists() or overwrite:
            os.system(f'cp {filename} {new_fn}')

    with Dataset(new_fn, 'a') as dst:
        if 'geophysical_data' in dst.groups.keys():
                dst = dst['geophysical_data']

        
        for product in  slices.keys():
                varname = f'{prefix}_{product}' if product not in ['lat','lon'] else f'{product}'
                
                if varname not in dst.variables.keys():
                        dims = dst[[k for k in dst.variables.keys() if 'Rrs' in k or 'Rw' in k or '__xarray_dataarray_variable__' in k][0]].get_dims()
                        dst.createVariable(varname, np.float32, [d.name for d in dims if d.name not in 'band'], fill_value=-999)
                dst[varname][:] = np.squeeze(products[:,:,slices[product]].astype(np.float32))





def return_lat_lon_Aquaverse(path):
    gtif = gdal.Open(path)
    image = gtif.ReadAsArray()
    xoffset, px_w, rot1, yoffset, rot2, px_h  = list(gtif.GetGeoTransform())
    
    #Transform
    crs = osr.SpatialReference()
    crs.ImportFromWkt(gtif.GetProjectionRef())
    crsGeo = osr.SpatialReference()
    crsGeo.ImportFromEPSG(4326)
    image_transform = osr.CoordinateTransformation(crs, crsGeo)
    
    
    width = len(image[0])
    height = len(image)
    rows = np.arange(0,height)
    cols = np.arange(0,width)
    
    #Get a grid of lat and long values
    getarray_coords = np.vectorize(array_coords(image_transform, xoffset, px_w, rot1, yoffset, rot2, px_h),otypes=[float,float])
    lat,long = getarray_coords(rows[:,None],cols[None,:])
    return lat,long

def array_coords(image_transform, xoffset, px_w, rot1, yoffset, rot2, px_h):
    def get_array_coords(r,c):
        posX = px_w * c + rot1 * r + xoffset + px_w / 2
        posY = rot2 * c + px_h * r + yoffset + px_h / 2
        lat,long,z = image_transform.TransformPoint(posX,posY)
        
        return lat,long
    return get_array_coords

def convert_tif_nc(base_location):
    available_tifs = [name for name in glob.glob(base_location+'*RRS*nm.TIF')]
    tif            = available_tifs[0]
    lat,lon = return_lat_lon_Aquaverse(tif)  
    lon_min, lat_min, lon_max, lat_max = [min(lon[:,0]), min(lat[0,:]),max(lon[:,0]), max(lat[0,:])]
    # zone_number    = 10
    
    # extent         = GetExtent(gdal.Open(tif),min_max=True)
    # lat_lon        = utm_to_latlong(extent[0],extent[1], [zone_number], northern=True)
    
    # lon_min, lat_min, lon_max, lat_max = [min(lat_lon[1]), min(lat_lon[0]),max(lat_lon[1]), max(lat_lon[0])]
    raster = xarray.open_rasterio(tif)
    #lon,lat = np.meshgrid(raster.x,raster.y)
    # lat = utm_to_latlong(raster.x[0],raster.y, [zone_number], northern=True)[0]
    # lon = utm_to_latlong(raster.x,raster.y[0], [zone_number], northern=True)[1]
    # lon,lat = np.meshgrid(lon,lat)
    
    products       = np.squeeze(rasterio.open(tif).read()).astype(float)#[np.squeeze(rasterio.open(tif).read()).astype(float) for tif in available_tifs]
    wavelengths    = [tif.split('_')[-1].split('.')[0].split('nm')[0]] 
    
    products       =  np.expand_dims(np.squeeze(products),-1)
    out_file_tif        = base_location + 'aquaverse.tif'
    out_file_nc         = base_location + 'aquaverse_init.nc'
    out_file_nc_labels  = base_location + 'aquaverse.nc'
    create_geotiff(products, lon_min, lat_min, lon_max, lat_max,filename = out_file_tif,product_names = wavelengths)
    
    
    products       = np.dstack([np.squeeze(rasterio.open(tif).read()).astype(float) for tif in available_tifs]+[lat,lon])
    wavelengths    = [tif.split('_')[-1].split('.')[0].split('nm')[0] for tif in available_tifs]+['lat','lon']
    
    raster_final = xarray.open_rasterio(out_file_tif)
    raster_final.to_netcdf(out_file_nc)
    raster_final.close()

    slices = {wavelength: i for i,wavelength in enumerate(wavelengths)}
    save_nc(out_file_nc,out_file_nc_labels,products,slices,overwrite=True,prefix='Rrs')
    
    # print(lat_lon)
    return Path(out_file_nc_labels)

#base_location  = '/data/roshea/SCRATCH/Gathered/Scenes/OLI/LC08_L1TP_044034_20200708_20200912_02_T1/out/OLI_test_image_san_fran_XCI0001/044034/'
#base_location  = '/data/roshea/SCRATCH/Gathered/Scenes/MSI/S2A_MSIL1C_20201017T155251_N0209_R054_T18SUG_20201017T193914/out/MSI_test_image_20201017_XCI0001/'

#convert_tif_nc(base_location)

