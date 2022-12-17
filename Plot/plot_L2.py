#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 16:29:32 2022

@author: ryanoshea
"""

from pipeline.MDNs.MDN_MODIS_VIIRS_OLCI import image_estimates, get_tile_data, get_sensor_bands
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import numpy as np

from netCDF4 import Dataset
from pathlib import Path 

from pipeline.MDNs.MDN_MODIS_VIIRS_OLCI.parameters import get_args
from pipeline.MDNs.MDN_MODIS_VIIRS_OLCI.utils import get_sensor_bands, closest_wavelength, get_tile_data
from pipeline.MDNs.MDN_MODIS_VIIRS_OLCI.plot_utils import add_identity, add_stats_box
from pipeline.MDNs.MDN_MODIS_VIIRS_OLCI.metrics import mdsa,slope,sspb,r_squared

import pandas as pd
import matplotlib.colors as colors
import matplotlib.pyplot as plt 
import numpy as np
import time 
import os

def gamma_stretch(data, gamma=2): 
    ''' Apply gamma stretching to brighten imagery '''
    return (255. * data ** 0.5).astype(np.uint8) 



def extract_data(image, avail_bands, req_bands, allow_neg=False, key='Rrs'):
    ''' Extract the requested bands from a given NetCDF object '''

    if key == 'rhos':
        key = 'rhos' if any('rhos' in word for  word in image['geophysical_data'].variables.keys()) else 'Rrs' 
        
    def extract(requested):
        bands = [closest_wavelength(band, avail_bands,tol=40 if key == 'rhos' else 5) for band in requested]
        # avail_bands = list(image['sensor_band_parameters'].variables['wavelength'][:])
        # bands = [closest_wavelength(band, avail_bands) for band in requested]
        div   = np.pi if key == 'Rw' else 1
        return np.ma.stack([image['geophysical_data'][f'{key}_{band}'][:]/ div  for band in bands], axis=-1) if 'Rrs' not in image['geophysical_data'].variables.keys() else np.ma.stack([image['geophysical_data'][key][:,:,avail_bands.index(b) ] / div for b in bands], axis=-1)
    
    # Extract the requested bands from the image object     
    extracted = extract(req_bands)

    # Set any values <= 0 to nan if we disallow negatives
    if not allow_neg: 
        extracted[extracted <= 0] = np.nan

    # Return the data, filling any masked values with nan
    return extracted.filled(fill_value=np.nan)



def plot_product(ax, title, product, rgb, vmin, vmax):
    ''' Plot a given product on the axis using vmin/vmax as the 
        colorbar min/max, and rgb as the visible background '''
    ax.imshow( gamma_stretch(rgb) )
    ax.axis('off')
    ax.set_title(title.upper())

    norm = colors.LogNorm(vmin=vmin, vmax=vmax)
    img  = ax.imshow(np.squeeze(product), norm=norm, cmap='turbo',interpolation='nearest')
    plt.colorbar(img, ax=ax,fraction=0.046, pad=0.04)

def plot_products(sensor,inp_file, out_path, product = 'chl,tss,cdom',overwrite=True):
    kwargs = {
        'sensor'        : sensor,
        'product'       : product,
        'sat_bands'     : True,
    }
    if sensor in ['OLCI']: kwargs['product'] = 'chl,tss,cdom,pc'
    req_bands = get_sensor_bands(sensor, get_args(**kwargs))
    rgb_bands = [640, 550, 440]

    location = Path(inp_file)
    date = str(location).split('/')[-4]
    loc = str(location).split('/')[-2] 
    Aqua_or_Terra  = str(location).split('/')[-4][0] 
    
    out_path = Path(out_path).joinpath('Imagery')
    out_path.mkdir(exist_ok=True, parents=True)
    filename = f'{out_path}/{loc}_{location.stem}_{date}_{sensor}.png'
    
    if os.path.exists(filename) and not overwrite:
        print(filename,f'exists, moving to next location')
        return
    time_start = time.time()

    # Load data, using rhos as the visible background
    image = Dataset(location)
    bands = sorted([int(k.replace('Rrs_', '')) for k in image['geophysical_data'].variables.keys() if 'Rrs_' in k and 'unc' not in k])
    bands = list(image['sensor_band_parameters'].variables['wavelength'][:]) if not bands else bands

    Rrs   = extract_data(image, bands, req_bands,allow_neg=False)
    if sensor in ['PACE']: Rrs = Rrs[::-1, :, :] #if sensor == 'PACE': 
    if sensor in ['VI'] or (Aqua_or_Terra =='A' and 'MOD' in sensor): Rrs = Rrs[::-1, ::-1, :] 

    rgb   = extract_data(image, bands, rgb_bands,key='rhos')
    if sensor in ['PACE']: rgb = rgb[::-1, :, :] 
    if sensor in ['VI'] or (Aqua_or_Terra =='A' and 'MOD' in sensor): rgb = rgb[::-1, ::-1, :] 
    try:
        products, slices = image_estimates(Rrs, **kwargs)
    except:
        print('Failed to produce products for ', filename)

    # Create plot for each product, bounding the colorbar per product
    f, axes = plt.subplots(1, len(slices), figsize=(4*len(slices), 8))
    bounds  = {
        'chl' : (1,  100),
        'tss' : (1,  100),
        'pc'  : (1,  100),
        'cdom': (0.1, 10),
    }
    for i, (key, idx) in enumerate(slices.items()):
        plot_product(np.atleast_1d(axes)[i], key, products[..., idx], rgb, *bounds[key])
    f.suptitle(f'{loc} {location.stem} {date} {sensor}')
    f.subplots_adjust(top=0.88)
    plt.tight_layout()
    plt.savefig(filename)
    print(f'Generated',filename,'in {time.time()-time_start:.1f} seconds')

    
