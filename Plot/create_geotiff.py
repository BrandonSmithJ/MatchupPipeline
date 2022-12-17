#!/usr/bin/env python
from osgeo import gdal
from osgeo import osr
import numpy as np
import os, sys


#takes a lat/lon grid and image as input
#Assuming it is a north facing image... take min/max values of the grid, divide by the widle
def create_geotiff(products, im_lat,im_lon,filename = 'exampleGeo_08_13.tif'):
    # print(np.shape(products),np.shape(products)[2])
    products_len = np.shape(products)[2]
    lat_count=np.shape(products)[0]
    lon_count=np.shape(products)[1]
    lon_min, lat_min, lon_max, lat_max = [np.min(im_lon),np.min(im_lat),np.max(im_lon),np.max(im_lat)]
    lat_resolution = (lat_max - lat_min)/float(lat_count)
    lon_resolution = (lon_max - lon_min)/float(lon_count)
    geotransform_tuple = (lon_min,lon_resolution,0,lat_max,0,-lat_resolution)
    # print(lon_min,lat_min,lon_max,lat_max,lat_resolution,lon_resolution)
    geotiff_object = gdal.GetDriverByName('GTiff').Create(filename, lon_count,lat_count, products_len, gdal.GDT_Float64)
    geotiff_object.SetGeoTransform(geotransform_tuple)
    spatial_reference_system =osr.SpatialReference()
    spatial_reference_system.ImportFromEPSG(4326)
    geotiff_object.SetProjection(spatial_reference_system.ExportToWkt())
    for i in range(products_len):
        geotiff_object.GetRasterBand(i+1).WriteArray(products[:,:,i])
    geotiff_object.FlushCache()
    geotiff_object = None



