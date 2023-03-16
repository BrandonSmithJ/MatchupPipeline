# Default parameters used for l2gen
# Other l2gen defaults can be found in:
#     {SeaDAS install folder}/share/{sensor}/msl12_defaults.par
DEFAULT_CONFIG = {
  'l2prod' : [ # Output products - more products requires more time to run l2gen
    'Rrs_nnn', 'Rrs_unc_vvv', 'aot_nnn', 
    'rhos_nnn', 'rhot_nnn', 'polcor_nnn',
    'latitude', 'longitude', 'l2_flags', 

    # Ancillary parameter
    'solz', 'senz', 'sola', 'sena', 'relaz', 'scattang', 'ozone', 'no2_frac', 'mwind', 
    'zwind', 'windangle', 'windspeed', 'height', 'humidity', 'ice_frac', 'water_vapor',
    'pressure', 'no2_strat', 'no2_tropo', 'sstref', 'sssref',

    # Atmospheric correction intermediate products
    'aer_model_min', 'aer_model_max', 'brdf', 'cloud_albedo', 'glint_coef',

    # Derived geophysical parameters
    'angstrom', 'Kd_490', 'smoke', 

    # Unable to be used by some sensors
    'pic', 'poc', 'calcite', 'chlor_a', 'depth',

    # Miscellaneous
    'elev', 'pixnum',

    # Uncertainties
    #'aot_unc_nnn', 'ozone_unc', 'mwind_unc', 'zwind_unc', 'windangle_unc', 'windspeed_unc', 
    #'humidity_unc', 'water_vapor_unc', 'pressure_unc', 
  ]

}


# Sensor-specific parameters used for l2gen
SENSOR_CONFIG = {
  'TM': {
    'aer_opt'        : '-1',
    'aer_wave_short' : '840',
    'aer_wave_long'  : '1676',
    'cloud_wave'     : '2223',
    'cloud_thresh'   : '0.0256',
    'nlwmin'         : '0.15',
    'rhoamin'        : '0.0005',
    'l2prod_exclude' : ['pic', 'poc', 'chlor_a', 'depth', 'calcite'],
  },

  'ETM' : {
    'aer_opt'        : '-1',
    'aer_wave_short' : '835',
    'aer_wave_long'  : '1648',
    'cloud_wave'     : '2205',
    'cloud_thresh'   : '0.0256',
    'nlwmin'         : '0.15',
    'rhoamin'        : '0.0005',
    'l2prod_exclude' : ['pic', 'poc', 'chlor_a', 'depth', 'calcite'],
  },

  'OLI' : {
    'l2prod_exclude' : [ 
        'Rrs_unc_vvv', 'aot_nnn', 
        'rhos_nnn', 'rhot_nnn', 'polcor_nnn',
         

        # Ancillary parameter
        'solz', 'senz', 'sola', 'sena', 'relaz', 'scattang', 'ozone', 'no2_frac', 'mwind', 
        'zwind', 'windangle', 'windspeed', 'height', 'humidity', 'ice_frac', 'water_vapor',
        'pressure', 'no2_strat', 'no2_tropo', 'sstref', 'sssref',

        # Atmospheric correction intermediate products
        'aer_model_min', 'aer_model_max', 'brdf', 'cloud_albedo', 'glint_coef',

        # Derived geophysical parameters
        'angstrom', 'Kd_490', 'smoke', 

        # Unable to be used by some sensors
        'pic', 'poc', 'calcite', 'chlor_a', 'depth',

        # Miscellaneous
        'elev', 'pixnum',],
  },

  'OLI2' : {
    'l2prod_exclude' : [ 
        'Rrs_unc_vvv', 'aot_nnn', 
        'rhos_nnn', 'rhot_nnn', 'polcor_nnn',
         

        # Ancillary parameter
        'solz', 'senz', 'sola', 'sena', 'relaz', 'scattang', 'ozone', 'no2_frac', 'mwind', 
        'zwind', 'windangle', 'windspeed', 'height', 'humidity', 'ice_frac', 'water_vapor',
        'pressure', 'no2_strat', 'no2_tropo', 'sstref', 'sssref',

        # Atmospheric correction intermediate products
        'aer_model_min', 'aer_model_max', 'brdf', 'cloud_albedo', 'glint_coef',

        # Derived geophysical parameters
        'angstrom', 'Kd_490', 'smoke', 

        # Unable to be used by some sensors
        'pic', 'poc', 'calcite', 'chlor_a', 'depth',

        # Miscellaneous
        'elev', 'pixnum',],
  },
  
  'MOD' : {
    'aer_opt'        : '-2',
    'aer_wave_short' : '869',
    'aer_wave_long'  : '2130',
    'cloud_wave'     : '2130',
    'cloud_thresh'   : '0.018',
    'l2prod_exclude' : ['depth'],

  },

  'VI' : {
    #'aer_opt'        : '-3',      
    'aer_wave_short' : '868',
    'aer_wave_long'  : '2258',
    'l2prod_exclude' : ['depth'],
  },

  'HICO' : {
    'aer_opt'        : '-2',
    'aer_wave_short' : '776',
    'aer_wave_long'  : '868',
    'cloud_thresh'   : '0.027',
    'atrem_opt'      : '32',
    'gas_opt'        : '15',
  },
  
  'OLCI': {
    #'aer_opt'        : '-2',
    'l2prod_exclude' : [ 'depth'],
  },
}



"""
l2gen parameters reference, found here:
   https://seadas.gsfc.nasa.gov/help/seadas-processing/ProcessL2gen.html
and replicated below.

Also useful: https://oceancolor.gsfc.nasa.gov/docs/format/Ocean_Level-2_Data_Products.pdf 

l2gen 9.3.0-seadas-v7.5.2.1 (Dec  3 2018 15:37:26)
Usage: l2gen argument-list

  The argument-list is a set of keyword=value pairs. The arguments can
  be specified on the commandline, or put into a parameter file, or the
  two methods can be used together, with commandline over-riding.

  return value: 0=OK, 1=error, 110=north,south,east,west does not intersect
  file data.

The list of valid keywords follows:

   help (boolean) (alias=h) (default=false) = print usage information
   version (boolean) (default=false) = print the version
        information
   dump_options (boolean) (default=false) = print
        information about each option
   dump_options_paramfile (ofile) = print
        information about each option to paramfile
   dump_options_xmlfile (ofile) = print
        information about each option to XML file
   par (ifile) = input parameter file
   pversion (string) (default=Unspecified) = processing version string
   suite (string) (default=OC) = product suite string for loading
        suite-specific defaults
   eval (int) (default=0) = evaluation bitmask
          0: standard processing
          1: init to old aerosol models
          2: enables MODIS and MERIS cloud Mask for HABS
         16: enables MODIS cirrus mask
         32: use test sensor info file
         64: use test rayleigh tables
        128: use test aerosol tables
        256: use test polarization tables
       1024: mask modis mirror-side 1 (navfail)
       2048: mask modis mirror-side 2 (navfail)
       4096: don't apply 'cold-only' or equatorial aerosol tests for SST
       8192: use alt sensor info file in eval
      32768: enables spherical path geom for dtran
   ifile (ifile) (alias=ifile1) = input L1 file name
   ilist (ifile) = file containing list of input files, one per line
   geofile (ifile) = input L1 geolocation file name (MODIS/VIIRS only)
   ofile (ofile) (alias=ofile1) (default=output) = output file #1 name,
        output vicarious L1B for inverse mode
   ofile[#] = additional output L2 file name
   oformat (string) (default=netCDF4) = output file format
        netcdf4: output a netCDF version 4 file
        hdf4:    output a HDF version 4 file
   il2file (ifile) (alias=il2file1) = input L2 file names for sensor to be
        used as a calibrator.  Alternatively, a data point can be used as a
        calibrator (e.g. MOBY)
   il2file[#] = additional L2 calibration file names
   tgtfile (ifile) = vicarious calibration target file
   aerfile (ifile) = aerosol model specification file
   metafile (ifile) = output meta-data file
   l2prod (string) (alias=l2prod1) = L2 products to be included in ofile #1
   l2prod[#] = L2 products to be included in ofile[#]
   spixl (int) (default=1) = start pixel number
   epixl (int) (default=-1) = end pixel number (-1=the last pixel)
   dpixl (int) (default=1) = pixel sub-sampling interval
   sline (int) (default=1) = start line number
   eline (int) (default=-1) = end line number (-1=the last line)
   dline (int) (default=1) = line sub-sampling interval
   ctl_pt_incr (int) (default=8) =  control-point pixel increment for lon/lat
        arrays
   proc_ocean (int) (default=1) = toggle ocean processing
        1: On
        0: Off
        2: force all pixels to be processed as ocean
   proc_land (boolean) (default=off) = toggle land processing
   proc_sst (boolean) (default=false) = toggle SST processing
        (default=1 for MODIS, 0 otherwise)
   proc_cloud (boolean) (default=off) = toggle cloud processing
   atmocor (boolean) (default=on) = toggle atmospheric correction
   mode (int) (default=0) = processing mode
        0: forward processing
        1: inverse (calibration) mode, targeting to nLw=0
        2: inverse (calibration) mode, given nLw target
        3: inverse (calibration) mode, given Lw target (internally normalized)
   aer_opt (int) (default=99) = aerosol mode option
      -99: No aerosol subtraction
      >0: Multi-scattering with fixed model (provide model number, 1-N,
           relative to aermodels list)
        0: White aerosol extrapolation.
       -1: Multi-scattering with 2-band model selection
       -2: Multi-scattering with 2-band, RH-based model selection and
           iterative NIR correction
       -3: Multi-scattering with 2-band model selection
           and iterative NIR correction
       -4: Multi-scattering with fixed model pair
           (requires aermodmin, aermodmax, aermodrat specification)
       -5: Multi-scattering with fixed model pair
           and iterative NIR correction
           (requires aermodmin, aermodmax, aermodrat specification)
       -6: Multi-scattering with fixed angstrom
           (requires aer_angstrom specification)
       -7: Multi-scattering with fixed angstrom
           and iterative NIR correction
           (requires aer_angstrom specification)
       -8: Multi-scattering with fixed aerosol optical thickness
           (requires taua specification)
       -9: Multi-scattering with 2-band model selection using Wang et al. 2009
           to switch between SWIR and NIR. (MODIS only, requires aer_swir_short,
           aer_swir_long, aer_wave_short, aer_wave_long)
      -10: Multi-scattering with MUMM correction
           and MUMM NIR calculation
      -11: Spectral optimization via Kuchinke (SeaWiFS-only)
      -12: Spectral matching via Gordon (SeaWiFS-only)
   aer_wave_short (int) (default=765) = shortest sensor wavelength for aerosol
        model selection
   aer_wave_long (int) (default=865) = longest sensor wavelength for aerosol
        model selection
   aer_swir_short (int) (default=-1) = shortest sensor wavelength for
        SWIR-based NIR Lw correction
   aer_swir_long (int) (default=-1) = longest sensor wavelength for SWIR-based
        NIR Lw correction
   aer_rrs_short (float) (default=-1.0) = Rrs at shortest sensor wavelength for
        aerosol model selection
   aer_rrs_long (float) (default=-1.0) = Rrs at longest sensor wavelength for
        aerosol model selection
   aermodmin (int) (default=-1) = lower-bounding model to use for fixed model
        pair aerosol option
   aermodmax (int) (default=-1) = upper-bounding model to use for fixed model
        pair aerosol option
   aermodrat (float) (default=0.0) = ratio to use for fixed model pair aerosol
        option
   aer_angstrom (float) (default=-999.0) = aerosol angstrom exponent for model
        selection
   aer_iter_max (int) (default=10) = maximum number of iterations for NIR
        water-leaving radiance estimation.
   mumm_alpha (float) (default=1.72) = water-leaving reflectance ratio for MUMM
       turbid water atmospheric correction
   mumm_gamma (float) (default=1.0) = two-way Rayleigh-aerosol transmittance
       ratio for MUMM turbid water atmospheric correction
   mumm_epsilon (float) (default=1.0) = aerosol reflectance ratio for MUMM
        turbid water atmospheric correction
   absaer_opt (int) (default=-1) = absorbing aerosol flagging option
       -1: disable
        0: use rhow constant
        1: apply chlorophyll climatology to calculate rhow
        2: 1+validate against nLw_412 climatology
   glint_opt (int) (default=1) = glint correction:
        0: glint correction off
        1: standard glint correction
        2: simple glint correction
   outband_opt (int) (default=99) = out-of-band correction for water-leaving
        radiances
        2: On (default for MODIS, SeaWiFS, OCTS)
        0: Off (default for MOS, OSMI)
   oxaband_opt (boolean) (default=false) = oxygen a-band correction option
        (default On for SeaWiFS, OSMI, and OCTS, Off otherwise)
   cirrus_opt (boolean) (default=false) = cirrus cloud reflectance correction option
   filter_opt (boolean) (default=false) = filtering input data option
        (default On for OCTS, Off otherwise)
   filter_file (ifile) (default=$OCDATAROOT/sensor/sensor_filter.dat) =
        data file for input filtering
   brdf_opt (int) (default=-1) = Bidirectional reflectance correction
        0: no correction
        1: Fresnel reflection/refraction correction for sensor path
        3: Fresnel reflection/refraction correction for sensor + solar path
        7: Morel f/Q + Fresnel solar + Fresnel sensor
       15: Gordon DT + Morel f/Q + Fresnel solar + Fresnel sensor
       19: Morel Q + Fresnel solar + Fresnel sensor
   fqfile (ifile) (default=$OCDATAROOT/common/morel_fq.nc) = f/Q correction file
   parfile (ifile) = par climatology file for NPP calculation
   gas_opt (int) (default=1) = gaseous transmittance bitmask selector
        0: no correction
        1: Ozone
        2: CO2
        4: NO2
        8: H2O
       16: Use ATREM (H2O)
   atrem_opt (int) (default=0) = ATREM gaseous transmittance bitmask selector
        0: H2O only
        1: Ozone
        2: CO2
        4: NO2
        8: CO
       16: CH4
       32: O2
       64: N2O
   atrem_full (int) (default=0) = ATREM gaseous transmittance calculation option
        0: Calculate transmittance using k-distribution method (fast)
        1: Calculate transmittance using full method (slow)
   atrem_geom (int) (default=0) = ATREM gaseous transmittance geometry option
        0: Only recalculate geometry when error threshold reached (fast)
        1: Recalculate geometry every pixel (slow)
   atrem_model (int) (default=0) = ATREM gaseous transmittance Atm. model selection
        0: Use pixel's latitude and date to determine model
        1: tropical
        2: mid latitude summer
        3: mid latitude winter
        4: subarctic summer
        5: subarctic winter
        6: US standard 1962
   atrem_splitpaths (int) (default=0) = ATREM gaseous transmittance split paths between solar and sensor (turns atrem_full on)
        0: Calculates transmittance over total path length (default)
        1: Calculates transmittance over separate solar and sensor paths (slow)
   iop_opt (int) (default=0) = IOP model for use in downstream products
        0: None (products requiring a or bb will fail)
        1: Carder
        2: GSM
        3: QAA
        4: PML
        5: NIWA
        6: LAS
        7: GIOP
   seawater_opt (int) (default=0) = seawater IOP options
        0: static values
        1: temperature & salinity-dependent seawater nw, aw, bbw

   polfile (ifile) = polarization sensitivities filename leader
   pol_opt (int) (default=-1) = polarization correction (sensor-specific)
        0: no correction
        1: only Rayleigh component is polarized
        2: all radiance polarized like Rayleigh
        3: only Rayleigh and Glint are polarized (MODIS default)
        4: all radiance polarized like Rayleigh + Glint
   rad_opt (int) (default=0) = radiation correction option (sensor-specific)
        0: no correction
        1: apply MERIS Smile correction
   xcalfile (ifile) = cross-calibration file
   xcal_opt (int) = cross-calibration option (sensor-specific) comma separated
        list of option values, 1 per band, with bands listed in xcal_wave.
        3: apply cross-calibration corrections (polarization and rvs)
        2: apply cross-calibration polarization corrections
        1: apply cross-calibration rvs corrections
        0: no correction
   xcal_wave (float) = wavelengths at which to apply cross-calibration.  Comma
        separated list of sensor wavelength values associated with xcal_opt.
   band_shift_opt (int) (default=0) = bandshifting option
        1: apply bio-optical bandshift
        0: linear interpolation
   add_ws_noise (float) (default=-1.0) = wind speed uncertainty simulation option
       <0.0: no noise added
       =0.0: use ws_unc to inform noise model
       >0.0: use input to inform noise model
   add_wd_noise (float) (default=-1.0) = wind direction uncertainty simulation option
       <0.0: no noise added
       =0.0: use wd_unc to inform noise model
       >0.0: use input to inform noise model
   add_mw_noise (float) (default=-1.0) = meridional wind  uncertainty simulation option
       <0.0: no noise added
       =0.0: use mw_unc to inform noise model
       >0.0: use input to inform noise model
   add_zw_noise (float) (default=-1.0) = zonal wind uncertainty simulation option
       <0.0: no noise added
       =0.0: use zw_unc to inform noise model
       >0.0: use input to inform noise model
   add_rh_noise (float) (default=-1.0) = relative humidity uncertainty simulation option
       <0.0: no noise added
       =0.0: use rh_unc to inform noise model
       >0.0: use input to inform noise model
   add_pr_noise (float) (default=-1.0) = pressure uncertainty simulation option
       <0.0: no noise added
       =0.0: use pr_unc to inform noise model
       >0.0: use input to inform noise model
   add_wv_noise (float) (default=-1.0) = water vapor uncertainty simulation option
       <0.0: no noise added
       =0.0: use wv_unc to inform noise model
       >0.0: use input to inform noise model
   add_oz_noise (float) (default=-1.0) = ozone uncertainty simulation option
       <0.0: no noise added
       =0.0: use oz_unc to inform noise model
       >0.0: use input to inform noise model
   add_lt_noise (float) (default=0.0) = Lt uncertainty simulation option
       >0.0: add random normal noise to gain
        0.0: no random noise added
   add_no2_tropo_noise (float) (default=-1.0) = tropospheric no2 uncertainty simulation option
       <0.0: no noise added
       =0.0: use no2_tropo_unc to inform noise model
       >0.0: use input to inform noise model
   add_no2_strat_noise (float) (default=-1.0) = stratospheric no2 uncertainty simulation option
       <0.0: no noise added
       =0.0: use no2_strat_unc to inform noise model
       >0.0: use input to inform noise model
   lt_noise_scale (float) = Lt noise scale factor option
       !=1.0: scales noise by factoring SNR
       =1.0: noise not scaled
   bias_frac (float) = bias fraction factor option
       !=0.0: adds bias as a fraction of Lt
       =0.0: no bias added
   resolution (int) (default=-1) = processing resolution (MODIS only)
       -1: standard ocean 1km processing
     1000: 1km resolution including aggregated 250 and 500m land bands
      500: 500m resolution including aggregated 250 land bands and
           replication for lower resolution bands
      250: 250m resolution with replication for lower resolution bands
   giop_aph_opt (int) (default=2) = GIOP model aph function type
        0: tabulated (supplied via giop_aph_file)
        2: Bricaud et al. 1995 (chlorophyll supplied via default empirical algorithm)
        3: Ciotti and Bricaud 2006 (size fraction supplied via giop_aph_s)
   giop_aph_file (ifile) (default=$OCDATAROOT/common/aph_default.txt) =
        GIOP model, tabulated aph spectra
   giop_aph_s (float) (default=-1000.0) = GIOP model, spectral parameter
        for aph
   giop_adg_opt (int) (default=1) = GIOP model adg function type
        0: tabulated (supplied via giop_adg_file)
        1: exponential with exponent supplied via giop_adg_s)
        2: exponential with exponent derived via Lee et al. (2002)
        3: exponential with exponent derived via OBPG method
   giop_adg_file (string) (default=$OCDATAROOT/common/adg_default.txt) =
        GIOP model, tabulated adg spectra
   giop_adg_s (float) (default=0.018) = GIOP model, spectral parameter
        for adg
   giop_bbp_opt (int) (default=3) = GIOP model bbp function type
        0: tabulated (supplied via giop_bbp_file)
        1: power-law with exponent supplied via giop_bbp_s)
        2: power-law with exponent derived via Hoge & Lyon (1996)
        3: power-law with exponent derived via Lee et al. (2002)
        5: power-law with exponent derived via Ciotti et al. (1999)
        6: power-law with exponent derived via Morel & Maritorena (2001)
        7: power-law with exponent derived via Loisel & Stramski (2000)
        8: spectrally independent vector derived via Loisel & Stramski (2000)
        9: fixed vector derived via Loisel & Stramski (2000)
       10: fixed vector derived via lee et al. (2002)
   giop_bbp_file (ifile) (default=$OCDATAROOT/common/bbp_default.txt) =
        GIOP model, tabulated bbp spectra
   giop_bbp_s (float) (default=-1000.0) = GIOP model, spectral parameter
        for bbp
   giop_acdom_opt (int) (default=1) = GIOP model acdom function type
        0: tabulated (supplied via giop_acdom_file)
        1: no data
   giop_acdom_file (ifile) =
        file of specific CDOM absorption coefficients for aLMI
   giop_anap_opt (int) (default=1) = GIOP model anap function type
        0: tabulated (supplied via giop_anap_file)
        1: no data
   giop_anap_file (ifile) =
        file of specific NAP absorption coefficients for aLMI
   giop_bbph_opt (int) (default=1) = GIOP model bbph function type
        0: tabulated (supplied via giop_bbph_file)
        1: no data
   giop_bbph_file (ifile) =
        file of specific phytoplankton backscattering coefficients for aLMI
   giop_bbnap_opt (int) (default=1) = GIOP model bbnap function type
        0: tabulated (supplied via giop_bbnap_file)
        1: no data
   giop_bbnap_file (ifile) =
        file of specific nap backscattering coefficients for aLMI
   giop_rrs_opt (int) (default=0) = GIOP model Rrs to bb/(a+bb) method
        0: Gordon quadratic (specified with giop_grd)
        1: Morel f/Q
   giop_rrs_diff (float) (default=0.33) = GIOP model, maximum difference between input and modeled Rrs
   giop_grd (float) (default=[0.0949,0.0794]) = GIOP model, Gordon
        Rrs to bb/(a+bb) quadratic coefficients
   giop_wave (float) (default=-1) = GIOP model list of sensor wavelengths for
        optimization comma-separated list, default is all visible bands (400-700nm)
   giop_maxiter (int) (default=50) = GIOP Model iteration limit
   giop_fit_opt (int) (default=1) = GIOP model optimization method
        0: Amoeba optimization
        1: Levenberg-Marquardt optimization
        3: SVD matrix inversion
        4: SIOP adaptive matrix inversion
   gsm_opt (int) (default=0) = GSM model options
        0: default coefficients
        1: Chesapeake regional coefficients
   gsm_fit (int) (default=0) = SM fit algorithm
        0: Amoeba
        1: Levenberg-Marquardt
   gsm_adg_s (float) (default=0.02061) = GSM IOP model, spectral slope for adg
   gsm_bbp_s (float) (default=1.03373) = GSM IOP model, spectral slope for bbp
   gsm_aphw (float) (default=[412.0, 443.0, 490.0, 510.0, 555.0, 670.0]) =
        GSM IOP model, wavelengths of ap* table
   gsm_aphs (float) (default=[0.00665, 0.05582, 0.02055, 0.01910, 0.01015, 0.01424]) = GSM IOP model, coefficients of ap* table
   qaa_adg_s (float) (alias=qaa_S) (default=0.015) = QAA IOP model, spectral
        slope for adg
   qaa_wave (int) = sensor wavelengths for QAA algorithm
   chloc2_wave (int) (default=[-1,-1]) = sensor wavelengths for OC2 chlorophyll
        algorithm
   chloc2_coef (float) (default=[0.0,0.0,0.0,0.0,0.0]) = coefficients for OC2
        chlorophyll algorithm
   chloc3_wave (int) (default=[-1,-1,-1]) = sensor wavelengths for OC3
         chlorophyll algorithm
   chloc3_coef (float) (default=[0.0,0.0,0.0,0.0,0.0]) = coefficients for OC3
        chlorophyll algorithm
   chloc4_wave (int) (default=[-1,-1,-1,-1]) = sensor wavelengths for OC4
        chlorophyll algorithm
   chloc4_coef (float) (default=[0.0,0.0,0.0,0.0,0.0]) = coefficients for OC4
        chlorophyll algorithm
   kd2_wave (int) (default=[-1,-1]) = sensor wavelengths for polynomial Kd(490)
        algorithm
   kd2_coef (float) (default=[0.0,0.0,0.0,0.0,0.0,0.0]) = sensor wavelengths
        for polynomial Kd(490) algorithm
   flh_offset (float) (default=0.0) = bias to subtract
        from retrieved fluorescence line height
   vcnnfile (ifile) = virtual constellation neural net file
   picfile (ifile) = pic table for Balch 2-band algorithm
   owtfile (ifile) = optical water type file
   owtchlerrfile (ifile) = chl error file associate with optical water type
   aermodfile (ifile) = aerosol model filename leader
   aermodels (string) (default=[r30f95v01,r30f80v01,r30f50v01,r30f30v01,r30f20v01,r30f10v01,r30f05v01,r30f02v01,r30f01v01,r30f00v01,r50f95v01,r50f80v01,r50f50v01,r50f30v01,r50f20v01,r50f10v01,r50f05v01,r50f02v01,r50f01v01,r50f00v01,r70f95v01,r70f80v01,r70f50v01,r70f30v01,r70f20v01,r70f10v01,r70f05v01,r70f02v01,r70f01v01,r70f00v01,r75f95v01,r75f80v01,r75f50v01,r75f30v01,r75f20v01,r75f10v01,r75f05v01,r75f02v01,r75f01v01,r75f00v01,r80f95v01,r80f80v01,r80f50v01,r80f30v01,r80f20v01,r80f10v01,r80f05v01,r80f02v01,r80f01v01,r80f00v01,r85f95v01,r85f80v01,r85f50v01,r85f30v01,r85f20v01,r85f10v01,r85f05v01,r85f02v01,r85f01v01,r85f00v01,r90f95v01,r90f80v01,r90f50v01,r90f30v01,r90f20v01,r90f10v01,r90f05v01,r90f02v01,r90f01v01,r90f00v01,r95f95v01,r95f80v01,r95f50v01,r95f30v01,r95f20v01,r95f10v01,r95f05v01,r95f02v01,r95f01v01,r95f00v01]) = aerosol models
   met1 (ifile) (default=$OCDATAROOT/common/met_climatology.hdf) =
        1st meteorological ancillary data file
   met2 (ifile) = 2nd meteorological ancillary data file
   met3 (ifile) = 3rd meteorological ancillary data file
   ozone1 (ifile) (default=$OCDATAROOT/common/ozone_climatology.hdf) =
        1st ozone ancillary data file
   ozone2 (ifile) = 2nd ozone ancillary data file
   ozone3 (ifile) = 3rd ozone ancillary data file
   anc_profile1 (ifile) =
        1st ancillary profile data file
   anc_profile2 (ifile) =
        2nd ancillary profile data file
   anc_profile3 (ifile) =
        3rd ancillary profile data file
   anc_cor_file (ifile) = ozone correction file
   land (ifile) (default=$OCDATAROOT/common/landmask_GMT15ARC.nc) = land mask file
   water (ifile) (default=$OCDATAROOT/common/watermask.dat) =
        shallow water mask file
   demfile (ifile) (default=$OCDATAROOT/common/ETOPO1_ocssw.nc) =
        digital elevation map file
   elevfile (ifile) (default=$OCDATAROOT/common/ETOPO1_ocssw.nc) = global elevation netCDF file
   elev_auxfile (ifile) = auxiliary elevation netCDF file
   icefile (ifile) (default=$OCDATAROOT/common/ice_mask.hdf) = sea ice file
   ice_threshold (float) (default=0.1) = sea ice fraction above which will be
        flagged as sea ice
   sstcoeffile (ifile) = IR sst algorithm coefficients file
   sstssesfile (ifile) = IR sst algorithm error statistics file
   sst4coeffile (ifile) = SWIR sst algorithm coefficients file
   sst4ssesfile (ifile) = SWIR sst algorithm error statistics file
   sst3coeffile (ifile) = Triple window sst algorithm coefficients file
   sst3ssesfile (ifile) = Triple window sst algorithm error statistics file
   sstfile (ifile) (default=$OCDATAROOT/common/sst_climatology.hdf) = input
        SST reference file
   sstreftype (int) (default=0) = Reference SST field source
        0: Reynolds OI SST reference file
        1: AMSR-E daily SST reference file
        2: AMSR-E 3-day SST reference file
        3: ATSR monthly SST reference file
        4: NTEV2 monthly SST reference file
        5: AMSR-E 3-day or night SST reference file
        6: WindSat daily SST reference file
        7: WindSat 3-day SST reference file
        8: WindSat 3-day or night SST reference file

   sstrefdif (float) (default=100.0) = stricter sst-ref difference threshold
   viirsnv7 (int) (default=-1) = =1 to use the VIIRSN V7 high senz latband sst and sst3 equations
   viirsnosisaf (int) (default=0) = =1 to use the VIIRSN OSI-SAF sst and sst3 equations
   newavhrrcal (int) (default=0) = =1 for new noaa-16 calibration
   ch22detcor (float) (default=[1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]) =
        Channel 22 detector corrections (MODIS only)
   ch23detcor (float) (default=[1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]) =
        Channel 23 detector corrections (MODIS only)
   no2file (ifile) (default=$OCDATAROOT/common/no2_climatology.hdf) = no2
        ancillary file
   alphafile (ifile) (default=$OCDATAROOT/common/alpha510_climatology.hdf) =
        alpha510 climatology file
   tauafile (ifile) (default=$OCDATAROOT/common/taua865_climatology.hdf) =
        taua865 climatology file
   cldfile (ifile) = cloud mask file (MODIS only)
   calfile (ifile) = system calibration file
   offset (float) = calibration offset adjustment
   gain (float) = calibration gain multiplier
   flaguse (string) (default=) = Flags to use
   xcalbox (int) (default=0) = pixel size of the central box in the L1 scene
        (e.g. 5 pixels around MOBY) to be extracted into xcalfile for the
        cross-calibration, 0=whole L1
   xcalboxcenter (int) (default=[0,0]) = Central [ipix, iscan] of the box in
        the L1 scene, [0,0] = center of the L1 scene
   xcalpervalid (int) (default=0) = min percent of valid cross-calibration
        pixels within the box or the L1 scene, 0 = at least 1 pixel
   xcalsubsmpl (int) (default=1) = Sub-sampling rate for the data to be used
        for the cross-calibration
   chlthreshold (float) (default=100.000000) = threshold on L2 data chlorophyll
        (100.000000=CHL_MAX)
   aotthreshold (float) (default=1.000000) = threshold on L2 data AOTs
        (1.000000=AOT_MAX)
   coccolith (float) (default=[1.1,0.9,0.75,1.85,1.0,1.65,0.6,1.15]) =
        coccolithophore algorithm coefs
   cirrus_thresh (float) (default=[-1.0,-1.0]) = cirrus reflectance thresholds
   taua (float) = [taua_band1,...,taua_bandn] aerosol optical thickness of the
        calibration data point
   cloud_thresh (float) (alias=albedo) (default=0.027) = cloud reflectance
        threshold
   cloud_wave (float) (default=865.0) = wavelength of cloud reflectance test
   cloud_eps (float) (default=-1.0) = cloud reflectance ratio threshold
        (-1.0=disabled)
   glint_thresh (float) (alias=glint) (default=0.005) = high sun glint threshold
   absaer (float) (default=0.0) = absorbing aerosol threshold on aerosol index
   rhoamin (float) (default=0.0001) = min NIR aerosol reflectance to attempt
        model lookup
   sunzen (float) (default=75.0) = sun zenith angle threshold in deg.
   satzen (float) (default=60.0) = satellite zenith angle threshold
   epsmin (float) (default=0.85) = minimum epsilon to trigger atmospheric
        correction failure flag
   epsmax (float) (default=1.35) = maximum epsilon to trigger atmospheric
         correction failure flag
   tauamax (float) (default=0.3) = maximum 865 aerosol optical depth to trigger
        hitau flag
   nLwmin (float) (default=0.15) = minimum nLw(555) to trigger low Lw flag
   hipol (float) (default=0.5) = threshold on degree-of-polarization to set
        HIPOL flag
   wsmax (float) (default=8.0) = windspeed limit on white-cap correction in m/s
   windspeed (float) (default=-1000.0) = user over-ride of windspeed in m/s
        (-1000=use ancillary files)
   windangle (float) (default=-1000.0) = user over-ride of wind angle in deg
        (-1000=use ancillary files)
   pressure (float) (default=-1000.0) = user over-ride of atmospheric pressure
        in mb (-1000=use ancillary files)
   ozone (float) (default=-1000.0) = user over-ride of ozone concentration in
        cm (-1000=use ancillary files)
   relhumid (float) (default=-1000.0) = user over-ride of relative humidity in
        percent (-1000=use ancillary files)
   watervapor (float) (default=-1000.0) = user over-ride of water vapor in
        g/cm^2 (-1000=use ancillary files)
   maskland (boolean) (default=on) = land mask option
   maskbath (boolean) (default=off) = shallow water mask option
   maskcloud (boolean) (default=on) = cloud mask option
   maskglint (boolean) (default=off) = glint mask option
   masksunzen (boolean) (default=off) = large sun zenith angle mask option
   masksatzen (boolean) (default=off) = large satellite zenith angle mask option
   maskhilt (boolean) (default=on) = high Lt masking
   maskstlight (boolean) (default=on) = stray light masking
   sl_frac (float) (default=0.25) = SeaWiFS only, straylight fractional
        threshold on Ltypical
   sl_pixl (int) (default=-1) = SeaWiFS only, number of LAC pixels for
        straylight flagging
   vcal_opt (int) (default=-1) = Vicarious calibration option
   vcal_chl (float) (default=-1.0) = Vicarious calibration chl
   vcal_solz (float) (default=-1.0) = Vicarious calibration solz
   vcal_nLw (float) = Vicarious calibration normalized water leaving radiances
   vcal_Lw (float) = Vicarious calibration water leaving radiances
   vcal_depth (float) (default=-1000.0) = depth to use to exclude data from target file
   e.g. -1000 excludes depths less than 1000m

   vcal_min_nbin (int) (default=4) = minimum # of samples in a bin for acceptance
   vcal_min_nscene (int) (default=3) = minimum # of scenes in a bin for acceptance
   owmcfile (ifile) (default=$OCDATAROOT/common/owmc_lut.hdf) = lut for OWMC
        classification
   north (float) (default=-999) = north boundary
   south (float) (default=-999) = south boundary
   east (float) (default=-999) = east boundary
   west (float) (default=-999) = west boundary
   xbox (int) (default=-1) = number of pixels on either side of the SW point
   ybox (int) (default=-1) = number of scan lines on either side of the SW point
   subsamp (int) (default=1) = sub-sampling interval
   prodxmlfile (ofile) = output XML file describing all possible products
   breflectfile (ifile) = input NetCDF file for bottom reflectances and bottom types
   deflate (int) (default=0) = deflation level
   raman_opt (int) (default=0) = Raman scattering Rrs correction options
        0: no correction
        1: Lee et al. (2013) empirical correction
        2: Westberry et al. (2013) analytical correction
        3: Lee et al. (1994) analytical correction

   viirscalparfile (ifile) = VIIRS L1A calibration parameter file name (VIIRS only)
   geom_per_band (boolean) (default=0) = geometry per band option:
        0: use nominal viewing geometry - same for all bands
        1: use band-specific viewing geometry (if available)

   gmpfile (ifile) = GMP geometric parameter file (MISR only)
"""
