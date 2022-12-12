#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 11:08:27 2018

@author: dshea
"""

import sys
import argparse
import os
import shutil
import subprocess
import urllib.parse
import json

#sys.path.insert(0, os.path.dirname(__file__))
import manifest as mf

# global variables
MANIFEST_BASENAME = "manifest.json"
BUNDLELIST_BASENAME = "bundleList.json"
versionString = "5.2"
baseUrl = "https://oceandata.sci.gsfc.nasa.gov/manifest/tags"
manifestCommand = os.path.dirname(__file__) + "/manifest.py"
currentThing = 1
totalNumThings = 0

##########################################################################
#  WARNING - The initialBundleList should match the latest bundleList.json
##########################################################################
# mapping of bundle names to directories and extra options
bundleList = []
initialBundleList = [
    {"name":"root", "dir":".", "help":"random files in the root dir", "extra":"--exclude . --include bundleList.json --include OCSSW_bash.env --include OCSSW.env", "commandLine":True},
    {"name":"bin_linux_64", "dir":"bin_linux_64", "help":"executables for Linux", "commandLine":False}, 
    {"name":"bin_macosx_intel", "dir":"bin_macosx_intel", "help":"executables for Mac", "commandLine":False},
    {"name":"bin_odps", "dir":"bin_odps", "help":"executables for ODPS", "commandLine":False},
    {"name":"lib_linux_64", "dir":"lib_linux_64", "help":"shared libraries for Linux", "commandLine":False}, 
    {"name":"lib_macosx_intel", "dir":"lib_macosx_intel", "help":"shared libraries for Mac", "commandLine":False},
    {"name":"lib_odps", "dir":"lib_odps", "help":"shared libraries for ODPS", "commandLine":False},
    {"name":"opt_linux_64", "dir":"opt_linux_64", "help":"3rd party library for Linux", "extra": "--exclude src", "commandLine":False},
    {"name":"opt_macosx_intel", "dir":"opt_macosx_intel", "help":"3rd party library for Mac", "extra": "--exclude src", "commandLine":False},
    {"name":"opt_odps", "dir":"opt_odps", "help":"3rd party library for ODPS", "extra": "--exclude src", "commandLine":False},

    {"name":"ocssw_src", "dir":"ocssw_src", "help":"OCSSW source code", "commandLine":False},
    {"name":"opt_src", "dir":"opt/src", "help":"3rd party library sources", "extra":"--exclude .buildit.db", "commandLine":True},
    
    {"name":"afrt", "dir":"share/afrt", "help":"Ahmad-Fraser RT data", "commandLine":True},
    {"name":"aquarius", "dir":"share/aquarius", "help":"Aquarius", "commandLine":True},
    {"name":"avhrr", "dir":"share/avhrr", "help":"AVHRR", "commandLine":True},
    {"name":"aviris", "dir":"share/aviris", "help":"AVIRIS", "commandLine":True},
    {"name":"common", "dir":"share/common", "help":"common", "commandLine":True},
    {"name":"czcs", "dir":"share/czcs", "help":"CZCS", "commandLine":True},
    {"name":"eval", "dir":"share/eval", "help":"evaluation", "commandLine":True},
    {"name":"goci", "dir":"share/goci", "help":"GOCI", "commandLine":True},
    {"name":"hawkeye", "dir":"share/hawkeye", "help":"Hawkeye", "commandLine":True},
    {"name":"hico", "dir":"share/hico", "help":"HICO", "commandLine":True},
    {"name":"l5tm", "dir":"share/l5tm", "help":"l5tm", "commandLine":True},
    {"name":"l7etmp", "dir":"share/l7etmp", "help":"l7etmp", "commandLine":True},
    {"name":"meris", "dir":"share/meris", "help":"MERIS", "commandLine":True},
    {"name":"misr", "dir":"share/misr", "help":"MISR", "commandLine":True},
    {"name":"modis", "dir":"share/modis", "help":"MODIS common", "extra":"--exclude aqua --exclude terra", "commandLine":False},
    {"name":"modisa", "dir":"share/modis/aqua", "help":"MODIS AQUA", "commandLine":True},
    {"name":"modist", "dir":"share/modis/terra", "help":"MODIS TERRA", "commandLine":True},
    {"name":"mos", "dir":"share/mos", "help":"MOS", "commandLine":True},
    {"name":"msi", "dir":"share/msi", "help":"MSI Sentinel 2 common", "extra":"--exclude s2a --exclude s2b", "commandLine":False},
    {"name":"msis2a", "dir":"share/msi/s2a", "help":"MSI Sentinel 2A", "commandLine":True},
    {"name":"msis2b", "dir":"share/msi/s2b", "help":"MSI Sentinel 2B", "commandLine":True},
    {"name":"oci", "dir":"share/oci", "help":"PACE OCI", "commandLine":True},
    {"name":"ocia", "dir":"share/ocia", "help":"PACE OCI AVIRIS", "commandLine":True},
    {"name":"ocip", "dir":"share/ocip", "help":"PACE OCI PRISM", "commandLine":True},
    {"name":"ocis", "dir":"share/ocis", "help":"PACE OCI Simulated data", "commandLine":True},
    {"name":"ocm1", "dir":"share/ocm1", "help":"OCM1", "commandLine":True},
    {"name":"ocm2", "dir":"share/ocm2", "help":"OCM2", "commandLine":True},
    {"name":"ocrvc", "dir":"share/ocrvc", "help":"OC Virtual Constellation", "commandLine":True},
    {"name":"octs", "dir":"share/octs", "help":"OCTS", "commandLine":True},
    {"name":"olci", "dir":"share/olci", "help":"OLCI Sentinel 3 common", "extra":"--exclude s3a --exclude s3b", "commandLine":False},
    {"name":"olcis3a", "dir":"share/olci/s3a", "help":"OLCI Sentinel 3A", "commandLine":True},
    {"name":"olcia3b", "dir":"share/olci/s3b", "help":"OLCI Sentinel 3B", "commandLine":True},
    {"name":"oli", "dir":"share/oli", "help":"Landsat OLI", "commandLine":True},
    {"name":"osmi", "dir":"share/osmi", "help":"OSMI", "commandLine":True},
    {"name":"prism", "dir":"share/prism", "help":"PRISM", "commandLine":True},
    {"name":"sabiamar", "dir":"share/sabiamar", "help":"Sabiamar", "commandLine":True},
    {"name":"seawifs", "dir":"share/seawifs", "help":"SeaWiFS", "commandLine":True},
    {"name":"sgli", "dir":"share/sgli", "help":"SGLI", "commandLine":True},
    {"name":"viirs", "dir":"share/viirs", "extra":"--exclude dem --exclude j1 --exclude j2 --exclude npp", "help":"VIIRS common", "commandLine":False},
    {"name":"viirsdem", "dir":"share/viirs/dem", "help":"VIIRS Digital Elevation", "commandLine":True},
    {"name":"viirsj1", "dir":"share/viirs/j1", "help":"VIIRS JPSS1", "commandLine":True},
    {"name":"viirsj2", "dir":"share/viirs/j2", "help":"VIIRS JPSS2", "commandLine":True},
    {"name":"viirsn", "dir":"share/viirs/npp", "help":"VIIRS NPP", "commandLine":True},
    {"name":"wv3", "dir":"share/wv3", "help":"WV3", "commandLine":True},
    {"name":"aerosol", "dir":"share/aerosol", "help":"aerosol processing with dtdb", "commandLine":True},
    {"name":"cloud", "dir":"share/cloud", "help":"cloud properties processing", "commandLine":True},
    {"name":"benchmark", "dir":"benchmark", "help":"benchmark MOSIS Aqua, level0 -> level3 Mapped", "commandLine":True},
    {"name":"viirs_l1_benchmark", "dir":"viirs_l1_benchmark", "help":"VIIRS benchmark data", "commandLine":True},
    {"name":"viirs_l1_bin_macosx_intel", "dir":"viirs_l1_bin_macosx_intel", "help":"Subset of binary files for VIIRS", "commandLine":False},
    {"name":"viirs_l1_bin_linux_64", "dir":"viirs_l1_bin_linux_64", "help":"Subset of binary files for VIIRS", "commandLine":False},
    {"name":"viirs_l1_bin_odps", "dir":"viirs_l1_bin_odps", "help":"Subset of binary files for VIIRS", "commandLine":False}
]

# list of bundles that have luts
lutBundles = ["seawifs", "aquarius", "modisa", "modist", "viirsn", "viirsj1"]


def findBundleInfo(bundleName):
    for bundleInfo in bundleList:
        if bundleInfo["name"] == bundleName:
            return bundleInfo
    return None

def getArch():
    """
    Return the system arch string.
    """
    (sysname, _, _, _, machine) = os.uname()
    if sysname == 'Darwin':
        if machine == 'x86_64' or machine == 'i386':
            return 'macosx_intel'
        print("unsupported Mac machine =", machine)
        exit(1)
    if sysname == 'Linux':
        if machine == 'x86_64':
            return 'linux_64'
        print("Error: can only install OCSSW software on 64bit Linux")
        exit(1)
    if sysname == 'Windows':
        print("Error: can not install OCSSW software on Windows")
        exit(1)
    print('***** unrecognized system =', sysname, ', machine =', machine)
    print('***** defaulting to linux_64')
    return 'linux_64'

def runCommand(command):
    proc = subprocess.run(command, shell=True)
    if proc.returncode != 0:
        print("Error: return =", proc.returncode, ": trying to run command =", command)
        sys.exit(1)

def listTags(options):
    manifest_options = mf.create_default_options_list_tags()
    manifest_options.wget = options.wget
    mf.list_tags(manifest_options, None)

def installBundle(options, bundleInfo):
    global currentThing
    if options.verbose:
        print()
    print("Installing (" + str(currentThing), "of", str(totalNumThings) + ") -", bundleInfo["name"], flush=True)
    currentThing += 1

    manifest_options = mf.create_default_options_download()
    manifest_options.verbose = options.verbose
    manifest_options.name = bundleInfo["name"]
    manifest_options.tag = options.tag
    manifest_options.dest_dir = "%s/%s" % (options.install_dir, bundleInfo["dir"])
    manifest_options.save_dir = options.save_dir
    manifest_options.local_dir = options.local_dir
    manifest_options.wget = options.wget

    mf.download(manifest_options, None)

    if options.clean:
        command = "%s clean %s/%s" % (manifestCommand, options.install_dir, bundleInfo["dir"])
        if "extra" in bundleInfo:
            command += " " + bundleInfo["extra"]
        runCommand(command)

def updateLuts(options, lut):
    runner = options.install_dir + "/bin/ocssw_runner"
    if not os.path.isfile(runner):
        print("Error - bin directory needs to be installed.")
        exit(1)
    if options.verbose:
        print()
    print("Installing lut -", lut)
    command = "%s --ocsswroot %s update_luts %s" % (runner, options.install_dir, lut)
    runCommand(command)

def getBundleListTag(manifestFilename):
    try:
        with open(manifestFilename, 'rb') as manifestFile:
            manifest = json.load(manifestFile)
            return manifest['files'][BUNDLELIST_BASENAME]['tag']
    except json.JSONDecodeError:
        print(manifestFilename, "is not a manifest file")
        sys.exit(1)
    except FileNotFoundError:
        print(manifestFilename, "Not found")
        sys.exit(1)
    except KeyError:
        print(manifestFilename, "is corrupt")
        sys.exit(1)
    print("could not find bundeList tag in", manifestFilename)
    sys.exit(1)

def downloadBundleList(options):
    global bundleList

    if not options.tag:
        print("\nWARNING: --tag is required to get the proper bundle list.\n")
        bundleList = initialBundleList
        return
    if options.local_dir:
        manifestFilename = "%s/%s/root/%s" % (options.local_dir, options.tag, MANIFEST_BASENAME)
        bundleFilename = "%s/%s/root/%s" % (options.local_dir, getBundleListTag(manifestFilename),BUNDLELIST_BASENAME)
        if not os.path.isfile(bundleFilename):
            print(bundleFilename, "file does not exist")
            sys.exit(1)
        dest = "/tmp/%s" % (BUNDLELIST_BASENAME)
        shutil.copy(bundleFilename, dest)
    elif options.wget:
        command = "cd /tmp; wget %s/%s/root/%s" % (options.base_url, options.tag, MANIFEST_BASENAME)
        runCommand(command)
        manifestFilename = "/tmp/%s" % (MANIFEST_BASENAME)
        bundleListUrl = "%s/%s/root/%s" % (options.base_url, getBundleListTag(manifestFilename), BUNDLELIST_BASENAME)
        os.remove("/tmp/%s" % (MANIFEST_BASENAME))
        command = "cd /tmp; wget %s" % (bundleListUrl)
        runCommand(command)
    else:
        manifestUrl = "%s/%s/root/%s" % (options.base_url, options.tag, MANIFEST_BASENAME)
        parts = urllib.parse.urlparse(manifestUrl)
        host = parts.netloc
        request = parts.path
        status = mf.httpdl(host, request, localpath="/tmp", outputfilename=MANIFEST_BASENAME, force_download=True)
        if status != 0:
            print("Error downloading", manifestUrl, ": return code =", status)
            sys.exit(1)
        manifestFilename = "/tmp/%s" % (MANIFEST_BASENAME)
        bundleListUrl = "%s/%s/root/%s" % (options.base_url, getBundleListTag(manifestFilename), BUNDLELIST_BASENAME)
        os.remove("/tmp/%s" % (MANIFEST_BASENAME))
        parts = urllib.parse.urlparse(bundleListUrl)
        host = parts.netloc
        request = parts.path
        status = mf.httpdl(host, request, localpath="/tmp", outputfilename=BUNDLELIST_BASENAME, force_download=True)
        if status != 0:
            print("Error downloading", bundleListUrl, ": return code =", status)
            sys.exit(1)
    with open("/tmp/%s" % (BUNDLELIST_BASENAME), 'rb') as bundleListFile:
        bundleList = json.load(bundleListFile)
    os.remove("/tmp/%s" % (BUNDLELIST_BASENAME))

def run():
    global totalNumThings
    global bundleList

    # first make a parser to download the bundleInfo file
    parser = argparse.ArgumentParser(description="Install OCSSW bundles", add_help=False)
    parser.add_argument("-t", "--tag", default=None,
                        help="tag that you want to install")
    parser.add_argument("-b", "--base_url", default=baseUrl, 
                        help="remote url for the bundle server")
    parser.add_argument("-l", "--local_dir", default=None, 
                        help="local directory to use for bundle source instead of the bundle server")
    parser.add_argument("--wget", default=False, action="store_true", 
                        help="use wget for file download")
    parser.add_argument("--list_tags", default=False, action="store_true", 
                        help="list the tags that exist on the server")
    parser.add_argument("--version", default=False, action="store_true", 
                        help="print this program's version")

    options1 = parser.parse_known_args()
    if not options1[0].list_tags and not options1[0].version:
        downloadBundleList(options1[0])

    # now make the real parser
    parser = argparse.ArgumentParser(description="Install OCSSW bundles")
    parser.add_argument("--version", default=False, action="store_true", 
                        help="print this program's version")
    parser.add_argument("--list_tags", default=False, action="store_true", 
                        help="list the tags that exist on the server")
    parser.add_argument("-t", "--tag", default=None,
                        help="tag that you want to install")
    parser.add_argument("-i", "--install_dir", default=os.environ.get("OCSSWROOT", None), 
                        help="root directory for bundle installation (default=$OCSSWROOT)")
    parser.add_argument("-b", "--base_url", default=baseUrl, 
                        help="remote url for the bundle server")
    parser.add_argument("-l", "--local_dir", default=None, 
                        help="local directory to use for bundle source instead of the bundle server")
    parser.add_argument("-s", "--save_dir", default=None, 
                        help="local directory to save a copy of the downloaded bundles")
    parser.add_argument("-c", "--clean", default=False, action="store_true", 
                        help="delete extra files in the destination directory")
    parser.add_argument("--wget", default=False, action="store_true", 
                        help="use wget for file download")
    parser.add_argument("-a", "--arch", default=None, 
                        help="use this architecture instead of guessing the local machine (linux_64 macosx_intel odps)")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="increase output verbosity")

    # add weird bundle switches
    parser.add_argument("--bin", default=False, action="store_true", 
                        help="install binary executables")
    parser.add_argument("--opt", default=False, action="store_true", 
                        help="install 3rd party programs and libs")
    parser.add_argument("--src", default=False, action="store_true", 
                        help="install source files")
    parser.add_argument("--luts", default=False, action="store_true", 
                        help="install LUT files")
    parser.add_argument("--viirs_l1_bin", default=False, action="store_true", 
                        help="install VIIRS binary executables subset")

    # add bundles from the bundle list
    for bundleInfo in bundleList:
        if bundleInfo["commandLine"]:
            parser.add_argument("--" + bundleInfo["name"], default=False, action="store_true", 
                                help="install " + bundleInfo["help"] + " files")

    # add argument
    parser.add_argument("--direct_broadcast", default=False, action="store_true", 
                        help="toggle on bundles needed for MODIS direct broadcast")
    parser.add_argument("--seadas", default=False, action="store_true", 
                        help="toggle on the base set of bundles for SeaDAS")
    parser.add_argument("--odps", default=False, action="store_true", 
                        help="toggle on the base set of bundles for ODPS systems")
    parser.add_argument("--viirs_l1", default=False, action="store_true", 
                        help="install everything to run and test the VIIRS executables")
    parser.add_argument("--all", default=False, action="store_true", 
                        help="toggle on all satellite bundles")

    options = parser.parse_args()

    # print version
    if options.version:
        print(os.path.basename(sys.argv[0]), versionString)
        sys.exit(0)
    
    if options.list_tags:
        listTags(options)
        sys.exit(0)

    if not options.tag:
        print("--tag is required")
        sys.exit(1)

    if not options.install_dir:
        print("--install_dir is required if OCSSWROOT enviroment variable is not set")
        sys.exit(1)

    # add convience arguments
    if options.benchmark:
        options.seadas = True
        options.modisa = True

    if options.viirs_l1:
        options.root = True
        options.viirs_l1_bin = True
        options.viirs_l1_benchmark = True
        options.opt = True
        options.luts = True
        options.common = True
        options.ocrvc = True
        options.viirsn = True
        options.viirsj1 = True
        options.viirsdem = True

    if options.direct_broadcast:
        options.seadas = True
        options.modisa = True
        options.modist = True
        
    if options.seadas:
        options.root = True
        options.bin =True
        options.opt = True
        options.luts = True
        options.common = True
        options.ocrvc = True
        
    if options.odps:
        options.root = True
        options.bin =True
        options.opt = True
        options.common = True
        options.ocrvc = True
        options.all = True
        
    if options.all:
        for bundleInfo in bundleList:
            if bundleInfo["commandLine"]:
                if bundleInfo["name"] not in ["root"]:
                    setattr(options, bundleInfo["name"], True)

    # unset silly sensors for ODPS
    if options.odps:
        options.aquarius = False
        options.avhrr = False
        options.l5tm = False
        options.l7etmp = False
        options.misr = False
        options.mos = False
        options.msi = False
        options.msis2a = False
        options.msis2b = False
        options.ocm1 = False
        options.ocm2 = False
        options.prism = False
        options.sabiamar = False
        options.sgli = False
        options.wv3 = False

    # take care of the sub-sensors
    if options.modisa or options.modist:
        options.modis = True
    if options.msis2a or options.msis2b:
        options.msi = True
    if options.viirsn or options.viirsj1 or options.viirsj2:
        options.viirs = True
    if hasattr(options, "olcis3a"):
        if options.olcis3a or options.olcis3b:
            options.olci = True

    # make sure arch is set
    if not options.arch:
        if options.odps:
            options.arch = "odps"
        else:
            options.arch = getArch()

    # make sure bin and viirs_l1_bin are not both set
    if options.bin and options.viirs_l1_bin:
        print("Error: Can not install --bin and --viirs_l1_bin")
        sys.exit(1)

    # count the things we are going to install
    totalNumThings = 0
    for bundleInfo in bundleList:
        if hasattr(options, bundleInfo["name"]) and getattr(options, bundleInfo["name"]):
            totalNumThings += 1
        
    # count bin and lib bundles
    if options.bin:
        totalNumThings += 2

    # count viirs_l1_bin and lib bundles
    if options.viirs_l1_bin:
        totalNumThings += 2

    # count the opt bundle
    if options.opt:
        totalNumThings += 1

    # count source bundles (ocssw-src and opt/src)
    if options.src:
        totalNumThings += 2

    # now install the bundles

    # do the weird bundles
    if options.bin:
        bundleName = "bin_" + options.arch
        bundleInfo = findBundleInfo(bundleName)
        bundleInfo["dir"] = "bin"                 # fix the bin dest directory
        installBundle(options, bundleInfo)

    if options.viirs_l1_bin:
        bundleName = "viirs_l1_bin_" + options.arch
        bundleInfo = findBundleInfo(bundleName)
        if not bundleInfo:
            print("Error: tag does not contain the viirs_l1_bin bundles")
            sys.exit(1)
        bundleInfo["dir"] = "bin"                 # fix the bin dest directory
        installBundle(options, bundleInfo)

    if options.bin or options.viirs_l1_bin:
        bundleName = "lib_" + options.arch
        bundleInfo = findBundleInfo(bundleName)
        bundleInfo["dir"] = "lib"                 # fix the lib dest directory
        installBundle(options, bundleInfo)

    if options.opt:
        bundleName = "opt_" + options.arch
        bundleInfo = findBundleInfo(bundleName)
        bundleInfo["dir"] = "opt"                 # fix the opt dest directory
        installBundle(options, bundleInfo)

    if options.src:
        bundleInfo = findBundleInfo("opt_src")
        installBundle(options, bundleInfo)
        bundleInfo = findBundleInfo("ocssw_src")
        installBundle(options, bundleInfo)
        
    # do the normal bundles
    for bundleInfo in bundleList:
        if hasattr(options, bundleInfo["name"]) and getattr(options, bundleInfo["name"]):
            installBundle(options, bundleInfo)
    
    # update luts
    if options.luts:
        for bundleInfo in bundleList:
            if hasattr(options, bundleInfo["name"]) and getattr(options, bundleInfo["name"]):
                if bundleInfo["name"] in lutBundles:
                    updateLuts(options, bundleInfo["name"])
                else:
                    updateLuts(options, "common")

    print("Done\n")

if __name__ == "__main__":
    sys.exit(run())
