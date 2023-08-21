#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 09:30:38 2023

@author: roshea
"""

import os 
import numpy as np
import xarray as xr
from pathlib import Path 

#from https://stackoverflow.com/questions/15141563/python-netcdf-making-a-copy-of-all-variables-and-attributes-but-one
def copy_nc(in_nc,out_nc):
    import netCDF4 as nc
    keep = ['chlor_a','l2_flags','latitude','longitude']
    
    with nc.Dataset(in_nc) as src, nc.Dataset(out_nc, "w", format="NETCDF4") as dst:
        # copy global attributes all at once via dictionary
        dst.setncatts(src.__dict__)
        # copy dimensionsls
        for name, dimension in src.dimensions.items():
            dst.createDimension(
                name, (len(dimension) if not dimension.isunlimited() else None))
        dst.createGroup('geophysical_data')
        # copy all file data except for the excluded
        for group in ['navigation_data','geophysical_data']:
            for name, variable in src[group].variables.items():
                if name not  in keep: continue
                x = dst.createVariable(name, np.float32, variable.dimensions, fill_value=-999)
                dst[name].setncatts(src[group][name].__dict__)
                dst[name][:] = src[group][name][:].astype(np.float32)
            
    ds = xr.open_dataset(out_nc)
    # print(ds)
    comp = dict(zlib=True, complevel=5)
    encoding = {var: comp for var in ds.data_vars}
    out_nc_encoded = str(out_nc.parent) +'/'+ str(out_nc).split('/')[-1].split('.L2')[0] + '_encoded.L2.OC.nc'
    # print(out_nc)
    ds.to_netcdf(out_nc_encoded, encoding=encoding)
    Path.unlink(Path(in_nc))
    Path.unlink(Path(in_nc).parent.joinpath('.complete'))
    # Path.unlink(Path(in_nc))
    if 'Test_Outputs' in str(Path(in_nc).parent):
        Path.rmdir(Path(in_nc).parent)
    Path.unlink(Path(out_nc))
    os.rename(out_nc_encoded,out_nc)