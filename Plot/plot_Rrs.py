#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 15:02:06 2023

@author: roshea
"""

import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import numpy
from matplotlib.colors import LogNorm
import rasterio
import glob
import tarfile
from scipy.ndimage import zoom
from pathlib import Path
 
def rgb_enhance(rgb:'numpy.ndarray') -> 'numpy.ndaray':
    """ Rescale a rgb image to enhance the visual quality, adapted from:
    https://gis.stackexchange.com/questions/350663/automated-image-enhancement-in-python
    
    Parameters:
    rgb : numpy.ndarray of type float - size row*col*3
    
    Returns:
    rgb_enhanced: numpy.ndarray of type float - size row*col*3
    
    """
    
    import skimage.exposure as exposure
    import numpy as np
    
    rgb_vector = rgb.reshape([rgb.shape[0] * rgb.shape[1], rgb.shape[2]])
    rgb_vector = rgb_vector[~np.isnan(rgb_vector).any(axis=1)]
    
    # Get cutoff values based on standard deviations. Ideally these would be 
    # on either side of each histogram peak and cutoff the tail. 
    lims = []
    for i in range(3):
        x = np.mean(rgb_vector[:, i])
        sd = np.std(rgb_vector[:, i])
        low = x-(1.75*sd)  # Adjust the coefficient here if the image doesn't look right
        high = x + (1.75 * sd)  # Adjust the coefficient here if the image doesn't look right
        if low < 0:
            low = 0
        if high > 1:
            high = 1
        lims.append((low, high))
    
    r = exposure.rescale_intensity(rgb[:, :, 0], in_range=lims[0])
    g = exposure.rescale_intensity(rgb[:, :, 1], in_range=lims[1])
    b = exposure.rescale_intensity(rgb[:, :, 2], in_range=lims[2])
    rgb_enhanced = np.dstack((r, g, b))
    
    return rgb_enhanced

def nir_mask_gen(base_dir):
    l8_sr = glob.glob(base_dir +'/*_L2R.nc')[0]
    sr_l8 = netCDF4.Dataset(l8_sr, 'r')
    # read nir rhot
    l8_rhot_865 = np.array(sr_l8.variables['rhot_865'])
    toa_ref_nir =  np.where(l8_rhot_865 < 0.1, l8_rhot_865, 0)
    nir_mask = toa_ref_nir !=0
    if 'MSI' in base_dir: nir_mask  = zoom(nir_mask, 1/3, order=0)
    return nir_mask

#finds bounds based on provided lat lon box
def load_Rrs_aquaverse(base_dir,scene_id, nir_mask,pixel_bounds, wavelengths = [443,482,561,655],zoom_dict={'OLI':1/3,'MSI':1/3}):
    rrs = {}
    rrs_mask = {}
    for wavelength in wavelengths:
        rrs_file = base_dir + '/'+ scene_id + f'_RRS_{wavelength}nm.TIF'
        rrs[wavelength] = np.squeeze(rasterio.open(rrs_file).read()).astype(float)*nir_mask
        rrs[wavelength][rrs[wavelength] <= 0] = np.nan
        if 'OLI' in base_dir: 
            rrs[wavelength] = rrs[wavelength][pixel_bounds['row']:pixel_bounds['row_u'], pixel_bounds['col']:pixel_bounds['col_u']]
            rrs[wavelength] = zoom(rrs[wavelength],zoom_dict['OLI'],order=0)
        rrs_mask[wavelength] = rrs[wavelength].copy()
        rrs_mask[wavelength][rrs_mask[wavelength]>0] = 1.0
    return rrs,rrs_mask
    
def gen_pixel_bounds(image_shape):
    pixel_bounds={}
    #pixel_bounds['row']   = 1000
    #pixel_bounds['row_u'] = 4500
    #pixel_bounds['col']   = 2000
    #pixel_bounds['col_u'] = 4800
    pixel_bounds['row']   = 0
    pixel_bounds['row_u'] = image_shape[0]
    pixel_bounds['col']   = 0
    pixel_bounds['col_u'] = image_shape[1]


    return pixel_bounds

def gen_RGB(base_dir,pixel_bounds,sensor,zoom_dict={'OLI':1/3,'MSI':1/3}):
    l8_sr = glob.glob(base_dir +'/*_L2R.nc')[0]
    sr_l8 = netCDF4.Dataset(l8_sr, 'r')
    rhos_483 = 'rhos_483' if 'LC08' in base_dir else 'rhos_482'
    rhos_561 = 'rhos_561' if 'LC08' in base_dir else 'rhos_561'
    rhos_655 = 'rhos_655' if 'LC08' in base_dir else 'rhos_654'

    l8_rhos_483 = zoom(np.array(sr_l8.variables[rhos_483]),zoom_dict['OLI'],order=0) if sensor == 'OLI' else zoom(np.array(sr_l8.variables['rhos_492']), zoom_dict['MSI'], order=0)
    l8_rhos_561 = zoom(np.array(sr_l8.variables[rhos_561]),zoom_dict['OLI'],order=0) if sensor == 'OLI' else zoom(np.array(sr_l8.variables['rhos_560']), zoom_dict['MSI'], order=0)
    l8_rhos_655 = zoom(np.array(sr_l8.variables[rhos_655]),zoom_dict['OLI'],order=0) if sensor == 'OLI' else zoom(np.array(sr_l8.variables['rhos_665']), zoom_dict['MSI'], order=0)

    l8_rhos_483[l8_rhos_483<=0]= np.nan
    l8_rhos_561[l8_rhos_561<=0]= np.nan
    l8_rhos_655[l8_rhos_655<=0]= np.nan

    plt.figure()
    if sensor == 'OLI':
        plt.imshow(l8_rhos_483)
        plt.savefig(base_dir +'483.png')

        l8_rhos_483 = l8_rhos_483[pixel_bounds['row']:pixel_bounds['row_u'], pixel_bounds['col']:pixel_bounds['col_u']]
        l8_rhos_561 = l8_rhos_561[pixel_bounds['row']:pixel_bounds['row_u'], pixel_bounds['col']:pixel_bounds['col_u']]
        l8_rhos_655 = l8_rhos_655[pixel_bounds['row']:pixel_bounds['row_u'], pixel_bounds['col']:pixel_bounds['col_u']]

    l8_rgb = np.dstack((l8_rhos_655, l8_rhos_561,  l8_rhos_483)); del l8_rhos_483, l8_rhos_561, l8_rhos_655
    l8_rgb = rgb_enhance(l8_rgb)

    plt.figure()
    plt.imshow(l8_rgb)
    plt.savefig(base_dir +'rgb.png')
    plt.close()
    return l8_rgb

def find_Rrs_key(file2read_ar,prefix_Rrs,wavelength):
    offset=len(prefix_Rrs)
    keys_list = [i for i in file2read_ar.variables.keys() if prefix_Rrs in i]
    #print(keys_list,wavelength)
    int_keys_list_bool = [np.abs(int(key[offset:])-wavelength) <5 for key in keys_list]
    Rrs_key = keys_list[np.where(int_keys_list_bool)[0][0]] #np.where(int_keys_list_bool)[0][0]
    return Rrs_key

def load_Rrs(base_dir, AQV_rrs_mask,pixel_bounds, wavelengths = [443,483,561,655],atm_corr='acolite',sensor='MSI',zoom_dict={'OLI':1/3,'MSI':1/3}):
    l8_ac = glob.glob(base_dir +f'/{atm_corr}.nc')[0]
    prefix_Rrs = 'Rw' if atm_corr == 'polymer' else 'Rrs_'
    wavelength_swap = {'OLI2': {'acolite': {483: 482, 492:490},'polymer': {440: 443, 480:482, 560:561},'l2gen': {},},
                       'OLI' : {'acolite': {483: 482, 492:490},'polymer': {440: 443, 480:482, 560:561},'l2gen': {},},
                       'MSI' : {'acolite': {492:490},'polymer': {},'l2gen': {492:490},},}
    file2read_ar = netCDF4.Dataset(l8_ac,'r')
    AC_Rrs = {}
    if sensor == 'OLI' and 'LC09' in base_dir: sensor = 'OLI2'
    for wavelength in wavelengths:
        if atm_corr in ['acolite','polymer']: 
            #keys_list = [int(i[4:]) for i in file2read_ar.variables.keys() if 'Rrs_' in i]
            #int_keys_list_bool = [np.abs(int(key[4:])-483) <5 for key in keys_list]
            #Rrs_key = keys_list[np.where(int_keys_list_bool)[0][0]] #np.where(int_keys_list_bool)[0][0]

            AC_Rrs[wavelength] = np.asarray(file2read_ar.variables[find_Rrs_key(file2read_ar,prefix_Rrs,wavelength)])
        if atm_corr in ['l2gen']: 
            AC_Rrs[wavelength] = np.asarray(file2read_ar['geophysical_data'].variables[find_Rrs_key(file2read_ar['geophysical_data'],prefix_Rrs,wavelength)])
        if atm_corr == 'polymer': 
            AC_Rrs[wavelength][AC_Rrs[wavelength]==9.96921e+36] = np.float('nan')
            AC_Rrs[wavelength] = AC_Rrs[wavelength]/np.pi
        if wavelength in wavelength_swap[sensor][atm_corr].keys():
            AC_Rrs[wavelength_swap[sensor][atm_corr][wavelength]]=AC_Rrs[wavelength]
            wavelength = wavelength_swap[sensor][atm_corr][wavelength]
        
        if 'MSI'  == sensor:
            zoom_amount = 1/3 if atm_corr == 'acolite' else 2/3 if atm_corr == 'l2gen' else 2
            AC_Rrs[wavelength]  = zoom(AC_Rrs[wavelength], zoom_amount, order=0)
        if 'OLI' == sensor or 'OLI2' == sensor:
            zoom_amount = zoom_dict['OLI']
            AC_Rrs[wavelength] = AC_Rrs[wavelength][pixel_bounds['row']:pixel_bounds['row_u'], pixel_bounds['col']:pixel_bounds['col_u']]
            AC_Rrs[wavelength] = zoom(AC_Rrs[wavelength],zoom_amount,order=0)
            #print(np.shape(AC_Rrs[wavelength]),np.shape(AQV_rrs_mask[wavelength]))
            #AQV_rrs_mask[wavelength] = zoom(AQV_rrs_mask[wavelength],zoom_amount,order=0)
        local_AQV_rrs_mask = AQV_rrs_mask[wavelength] #zoom(AQV_rrs_mask[wavelength],zoom_amount,order=0) if sensor =='OLI' else AQV_rrs_mask[wavelength]
        AC_Rrs[wavelength] = local_AQV_rrs_mask*AC_Rrs[wavelength]

    return AC_Rrs
       

def set_vbounds(logic='',log_bool=True):
    vbounds={}
    vbounds['min']={}
    vbounds['max']={}
    min_max_prc = 100
    vbounds['min'][443] = -1 if logic=='diff'   else -min_max_prc if logic=='diff_prc' else 0.001 if log_bool else 0 
    vbounds['min'][482] = -0.5 if logic=='diff' else -min_max_prc if logic=='diff_prc' else 0.001 if log_bool else 0
    vbounds['min'][490] = -0.5 if logic=='diff' else -min_max_prc if logic=='diff_prc' else 0.001 if log_bool else 0
    vbounds['min'][560] = -0.5 if logic=='diff' else -min_max_prc if logic=='diff_prc' else 0.001 if log_bool else 0
    vbounds['min'][561] = -0.5 if logic=='diff' else -min_max_prc if logic=='diff_prc' else 0.001 if log_bool else 0
    vbounds['min'][655] = -0.5 if logic=='diff' else -min_max_prc if logic=='diff_prc' else 0.001 if log_bool else 0
    vbounds['min'][665] = -0.5 if logic=='diff' else -min_max_prc if logic=='diff_prc' else 0.001 if log_bool else 0

    vbounds['max'][443] = 1 if logic=='diff' else min_max_prc if logic=='diff_prc' else .03#0.006
    vbounds['max'][482] = 0.5 if logic=='diff' else min_max_prc if logic=='diff_prc' else .03#0.008
    vbounds['max'][490] = 0.5 if logic=='diff' else min_max_prc if logic=='diff_prc' else .03#0.008
    vbounds['max'][560] = 0.5 if logic=='diff' else min_max_prc if logic=='diff_prc' else .03#0.016
    vbounds['max'][561] = 0.5 if logic=='diff' else min_max_prc if logic=='diff_prc' else .03#0.016
    vbounds['max'][655] = 0.5 if logic=='diff' else min_max_prc if logic=='diff_prc' else .03#0.015
    vbounds['max'][665] = 0.5 if logic=='diff' else min_max_prc if logic=='diff_prc' else .03#0.015

    return vbounds

def plot_Rrs(base_dir,AC_Rrs,AQV_Rrs,l8_rgb,vbounds,wavelengths = [443,482,561,655],atm_corr_label = 'ACOLITE',rgb = True,scene_id=""):
    fig, axs = plt.subplots(2, 4, figsize=(18,8))
    box = dict(boxstyle="square",
         ec= 'black',
         fc='white')    
    txt_x, txt_y = 120, 300
    fsize = 16

    for i,wavelength in enumerate(wavelengths):
        if rgb:
            axs[0,0+i].imshow(l8_rgb)
        z1_plot = axs[0,0+i].imshow(AQV_Rrs[wavelength], vmin=vbounds['min'][wavelength], vmax=vbounds['max'][wavelength], cmap = 'jet' )
        clb = plt.colorbar(z1_plot, ax=axs[0,0+i],fraction=0.046, pad=0.04)
        clb.ax.set_title(r'$R_{rs} [sr^{-1}]$')
        if i == 0: axs[0,0+i].text(txt_x, txt_y, 'Aquaverse', color='black', fontsize=fsize, bbox=box)
        axs[0,0+i].xaxis.set_ticklabels([])
        axs[0,0+i].yaxis.set_ticklabels([])
        axs[0,0+i].set_title(f'{wavelength} nm', fontsize=24)

        if rgb:
            axs[1,0+i].imshow(l8_rgb)
        z1_plot = axs[1,0+i].imshow(AC_Rrs[wavelength], vmin=vbounds['min'][wavelength], vmax=vbounds['max'][wavelength], cmap = 'jet')
        plt.colorbar(z1_plot, ax=axs[1,0+i],fraction=0.046, pad=0.04)
        if i == 0: axs[1,0+i].text(txt_x, txt_y, atm_corr_label, color='black', fontsize=fsize, bbox=box)
        axs[1,0+i].xaxis.set_ticklabels([])
        axs[1,0+i].yaxis.set_ticklabels([])

    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["font.size"] = 18
    plt.tight_layout()
    plt.savefig(base_dir + f'/{scene_id}_{atm_corr_label}_Rrs.png')
    plt.close()

def plot_Rrs_composite(base_dir,AC_Rrs,AQV_Rrs,l8_rgb,vbounds,wavelengths = [443,482,561,655],atm_corrs = 'ACOLITE',rgb = True,scene_id=""):
    from matplotlib.colors import LogNorm
    fig, axs = plt.subplots(4, 4, figsize=(18,16))
    box = dict(boxstyle="square",
         ec= 'black',
         fc='white')    
    txt_x, txt_y = 120, 300
    fsize = 16

    for i,wavelength in enumerate(wavelengths):
        if rgb:
            axs[0,0+i].imshow(l8_rgb)
        # z1_plot = axs[0,0+i].imshow(AQV_Rrs[wavelength], vmin=vbounds['min'][wavelength], vmax=vbounds['max'][wavelength], cmap = 'jet' )
        z1_plot = axs[0,0+i].imshow(AQV_Rrs[wavelength], norm=LogNorm(vmin=vbounds['min'][wavelength], vmax=vbounds['max'][wavelength]), cmap = 'jet' )
        
        clb = plt.colorbar(z1_plot, ax=axs[0,0+i],fraction=0.046, pad=0.04)
        clb.ax.set_title(r'$R_{rs} [sr^{-1}]$')
        if i == 0: axs[0,0+i].text(txt_x, txt_y, 'Aquaverse', color='black', fontsize=fsize, bbox=box)
        axs[0,0+i].xaxis.set_ticklabels([])
        axs[0,0+i].yaxis.set_ticklabels([])
        axs[0,0+i].set_title(f'{wavelength} nm', fontsize=24)

        for j,atm_corr in enumerate(atm_corrs):
            if rgb:
                axs[1+j,0+i].imshow(l8_rgb)
            # z1_plot = axs[1+j,0+i].imshow(AC_Rrs[atm_corr][wavelength], vmin=vbounds['min'][wavelength], vmax=vbounds['max'][wavelength], cmap = 'jet')
            
            z1_plot = axs[1+j,0+i].imshow(AC_Rrs[atm_corr][wavelength], norm=LogNorm(vmin=vbounds['min'][wavelength], vmax=vbounds['max'][wavelength]), cmap = 'jet')
            
            plt.colorbar(z1_plot, ax=axs[1+j,0+i],fraction=0.046, pad=0.04)
            if i == 0: axs[1+j,0+i].text(txt_x, txt_y, atm_corr, color='black', fontsize=fsize, bbox=box)
            axs[1+j,0+i].xaxis.set_ticklabels([])
            axs[1+j,0+i].yaxis.set_ticklabels([])

    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["font.size"] = 18
    plt.tight_layout()
    plt.savefig(base_dir + f'/{scene_id}_Rrs.png')
    plt.close()

def plot_Rrs_diff(base_dir,AC_Rrs,AQV_Rrs,l8_rgb,wavelengths = [443,482,561,655],atm_corr_label = 'ACOLITE',rgb = True,scene_id=""):
    box = dict(boxstyle="square",
         ec= 'black',
         fc='white')    
    txt_x, txt_y = 120, 300
    fsize = 16
    
    fig, axs = plt.subplots(2, 4, figsize=(18,8))
    Rrs_diff = {}
    Rrs_diff_prc = {}
    vbounds_diff     = set_vbounds(logic='diff')
    vbounds_diff_prc = set_vbounds(logic='diff_prc')

    for i,wavelength in enumerate(wavelengths):
        Rrs_diff[wavelength] = 100*(AQV_Rrs[wavelength] - AC_Rrs[wavelength])
        Rrs_diff_prc[wavelength] = Rrs_diff[wavelength]/AC_Rrs[wavelength]

        if rgb:
            axs[0,0+i].imshow(l8_rgb)
            
        z1_plot = axs[0,0+i].imshow(Rrs_diff[wavelength], vmin = vbounds_diff['min'][wavelength], vmax = vbounds_diff['max'][wavelength], cmap = 'jet' )
        clb = plt.colorbar(z1_plot, ax=axs[0,0+i],fraction=0.046, pad=0.04)
        clb.ax.set_title(r'%')

        if i == 3: clb.set_label(f'100*(Rrs(AQV) - Rrs({atm_corr_label}))', fontsize= 16, rotation=90)

        axs[0,0+i].xaxis.set_ticklabels([])
        axs[0,0+i].yaxis.set_ticklabels([])
        axs[0,0+i].set_title(f'{wavelength} nm', fontsize=24)
        if i == 0: axs[0,0].text(txt_x, txt_y, atm_corr_label, color='black', fontsize=fsize, bbox=box)

        if rgb:
            axs[1,0+i].imshow(l8_rgb)

        z1_plot = axs[1,0+i].imshow(Rrs_diff_prc[wavelength], vmin = vbounds_diff_prc['min'][wavelength], vmax = vbounds_diff_prc['max'][wavelength], cmap = 'jet')
        clb = plt.colorbar(z1_plot, ax=axs[1,0+i],fraction=0.046, pad=0.04)

        if i == 3:  clb.set_label(f'100*(AQV - {atm_corr_label})/{atm_corr_label}', fontsize= 14, rotation=90)
        axs[1,0+i].xaxis.set_ticklabels([])
        axs[1,0+i].yaxis.set_ticklabels([])


    #plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["font.size"] = 18
    plt.tight_layout()
    plt.savefig(base_dir + f'/{scene_id}_{atm_corr_label}_Rrs_diff.png')
    plt.close()

def plot_Rrs_diff_composite(base_dir,AC_Rrs,AQV_Rrs,l8_rgb,wavelengths = [443,482,561,655],atm_corrs = 'ACOLITE',rgb = True,scene_id=""):
    box = dict(boxstyle="square",
         ec= 'black',
         fc='white')    
    txt_x, txt_y = 120, 300
    fsize = 16
    
    fig, axs = plt.subplots(3, 4, figsize=(18,12))
    fig_diff, axs_diff = plt.subplots(3, 4, figsize=(18,12))
    Rrs_diff = {}
    Rrs_diff_prc = {}
    vbounds_diff     = set_vbounds(logic='diff')
    vbounds_diff_prc = set_vbounds(logic='diff_prc')

    for i,wavelength in enumerate(wavelengths):
        for j,atm_corr in enumerate(atm_corrs):
            Rrs_diff[wavelength]     = 100*(AQV_Rrs[wavelength] - AC_Rrs[atm_corr][wavelength])
            Rrs_diff_prc[wavelength] = Rrs_diff[wavelength]/AC_Rrs[atm_corr][wavelength]
    
            if rgb:
                axs[0+j,0+i].imshow(l8_rgb)
                
            z1_plot = axs[0+j,0+i].imshow(Rrs_diff[wavelength], vmin = vbounds_diff['min'][wavelength], vmax = vbounds_diff['max'][wavelength], cmap = 'jet' )
            clb = plt.colorbar(z1_plot, ax=axs[0+j,0+i],fraction=0.046, pad=0.04)
            clb.ax.set_title(r'%')
    
            if i == 3: clb.set_label(f'100*(Rrs(AQV) - Rrs({atm_corr}))', fontsize= 16, rotation=90)
    
            axs[0+j,0+i].xaxis.set_ticklabels([])
            axs[0+j,0+i].yaxis.set_ticklabels([])
            if j == 0: axs[0,0+i].set_title(f'{wavelength} nm', fontsize=24)
            if i == 0: axs[0+j,0].text(txt_x, txt_y, atm_corr, color='black', fontsize=fsize, bbox=box)
            if j == 0: axs_diff[0,0+i].set_title(f'{wavelength} nm', fontsize=24)
            if i == 0: axs_diff[0+j,0].text(txt_x, txt_y, atm_corr, color='black', fontsize=fsize, bbox=box)
    
            if rgb:
                axs_diff[0+j,0+i].imshow(l8_rgb)
    
            z1_plot = axs_diff[0+j,0+i].imshow(Rrs_diff_prc[wavelength], vmin = vbounds_diff_prc['min'][wavelength], vmax = vbounds_diff_prc['max'][wavelength], cmap = 'jet')
            clb = plt.colorbar(z1_plot, ax=axs_diff[0+j,0+i],fraction=0.046, pad=0.04)
    
            if i == 3:  clb.set_label(f'100*(AQV - {atm_corr})/{atm_corr}', fontsize= 14, rotation=90)
            axs_diff[0+j,0+i].xaxis.set_ticklabels([])
            axs_diff[0+j,0+i].yaxis.set_ticklabels([])


    #plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["font.size"] = 18
    plt.tight_layout()
    #fig.savefig(base_dir + f'/{scene_id}_Rrs_diff.png')
    
    # plt.rcParams["axes.labelweight"] = "bold"
    # plt.rcParams["font.size"] = 18
    # plt.tight_layout()
    fig_diff.savefig(base_dir + f'/{scene_id}_Rrs_diff_prc.png')
    plt.close('all')

################
def plot_OLI_Rrs(base_dir, scene_id, atm_corrs,sensor,out_path):
    Path(out_path).mkdir(parents=True, exist_ok=True)
    atm_corrs_list = ['acolite','polymer','l2gen']
    zoom_dict = {'OLI':1/3 ,'MSI':1/3}
    if len(glob.glob(base_dir +'/*RRS*nm.TIF')) and all([len(glob.glob(base_dir +f'/*{atm_corr}.nc'))  for atm_corr in atm_corrs_list]):
        nir_mask = nir_mask_gen(base_dir)
        pixel_bounds = gen_pixel_bounds(image_shape=np.shape(nir_mask))
        wavelengths = {
                       'OLI': {'aquaverse':[443,482,561,655],'acolite':[443,483,561,655],'polymer':[440,480,560,655],'l2gen':[443,482,561,655],'output':[443,482,561,655]},
                       'MSI': {'aquaverse':[443,490,560,665],'acolite':[443,492,560,665],'polymer':[443,490,560,665],'l2gen':[443,492,560,665],'output':[443,490,560,665]},
                       }
        AQV_Rrs, AQV_Rrs_mask = load_Rrs_aquaverse(base_dir,scene_id, nir_mask,pixel_bounds, wavelengths = wavelengths[sensor]['aquaverse'],zoom_dict=zoom_dict)
        l8_rgb = gen_RGB(base_dir,pixel_bounds,sensor,zoom_dict=zoom_dict)
        vbounds = set_vbounds()
        #atm_corrs_list = ['acolite','polymer','l2gen']
        # for atm_corr in atm_corrs_list:
            
        #     if len(glob.glob(base_dir +f'/*{atm_corr}.nc')) :
        #            AC_Rrs = load_Rrs(base_dir, AQV_Rrs_mask, pixel_bounds, wavelengths = wavelengths[sensor][atm_corr],atm_corr=atm_corr,sensor=sensor)
        #            plot_Rrs(out_path,     AC_Rrs, AQV_Rrs, l8_rgb, vbounds, wavelengths = wavelengths[sensor]['output'], atm_corr_label = atm_corr,scene_id=scene_id)
        #            plot_Rrs_diff(out_path,AC_Rrs, AQV_Rrs, l8_rgb,          wavelengths = wavelengths[sensor]['output'], atm_corr_label = atm_corr,scene_id=scene_id)
        #if all([len(glob.glob(base_dir +f'/*{atm_corr}.nc'))  for atm_corr in atm_corrs_list]):
        AC_Rrs_dict = {atm_corr: load_Rrs(base_dir, AQV_Rrs_mask, pixel_bounds, wavelengths = wavelengths[sensor][atm_corr],atm_corr=atm_corr,sensor=sensor,zoom_dict=zoom_dict) for atm_corr in atm_corrs_list}
    
        plot_Rrs_composite(out_path,     AC_Rrs_dict, AQV_Rrs, l8_rgb, vbounds, wavelengths = wavelengths[sensor]['output'], atm_corrs = atm_corrs_list,scene_id=scene_id)
        plot_Rrs_diff_composite(out_path,AC_Rrs_dict, AQV_Rrs, l8_rgb,          wavelengths = wavelengths[sensor]['output'], atm_corrs = atm_corrs_list,scene_id=scene_id)
        plt.close('all') 
        return True
    # if 'acolite' in atm_corrs : 
    #     AC_Rrs = load_Rrs(base_dir, AQV_Rrs_mask, pixel_bounds, wavelengths = wavelengths[sensor]['acolite'],atm_corr='acolite',sensor=sensor)
    #     plot_Rrs(out_path,     AC_Rrs, AQV_Rrs, l8_rgb, vbounds, wavelengths = wavelengths[sensor]['output'], atm_corr_label = 'acolite')
    #     plot_Rrs_diff(out_path,AC_Rrs, AQV_Rrs, l8_rgb,          wavelengths = wavelengths[sensor]['output'], atm_corr_label = 'acolite')
        
    # if 'polymer' in atm_corrs: 
    #     polymer_Rrs = load_Rrs(base_dir, AQV_Rrs_mask, pixel_bounds, wavelengths = wavelengths[sensor]['polymer'],atm_corr='polymer',sensor=sensor)
    #     plot_Rrs(out_path,     polymer_Rrs, AQV_Rrs, l8_rgb, vbounds, wavelengths = wavelengths[sensor]['output'], atm_corr_label = 'polymer')
    #     plot_Rrs_diff(out_path,polymer_Rrs, AQV_Rrs, l8_rgb,          wavelengths = wavelengths[sensor]['output'], atm_corr_label = 'polymer')

    # if 'l2gen' in atm_corrs: 
    #     l2gen_Rrs = load_Rrs(base_dir, AQV_Rrs_mask, pixel_bounds, wavelengths = wavelengths[sensor]['l2gen'],atm_corr='l2gen',sensor=sensor)
    #     plot_Rrs(out_path,     l2gen_Rrs, AQV_Rrs, l8_rgb, vbounds, wavelengths = wavelengths[sensor]['output'], atm_corr_label = ' l2gen') 
    #     plot_Rrs_diff(out_path,l2gen_Rrs, AQV_Rrs, l8_rgb,          wavelengths = wavelengths[sensor]['output'], atm_corr_label = 'l2gen')

    # for atm_corr in atm_corrs:
        

# def plot_Rrs(sensor, inp_file, out_path, date, dataset, ac_method, product = 'chl,tss,cdom',overwrite=True, fix_projection_Rrs = False):

#         return True
