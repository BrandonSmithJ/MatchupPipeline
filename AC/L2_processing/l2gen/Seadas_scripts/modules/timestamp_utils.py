from modules.MetaUtils import readMetadata
import modules.ProcUtils as ProcUtils
import datetime

def hico_timestamp(arg):
    """
        Determine the start time, stop time, and platform of a VIIRS hdf5 file.
    """

    meta = readMetadata(arg)
    if 'instrument' in meta:
        sat_name = meta['instrument'].lower()
        sdate = meta['Beginning_Date']
        edate = meta['Ending_Date']
        stime = meta['Beginning_Time']
        etime = meta['Ending_Time']
        start_time = '-'.join([sdate[0:4],sdate[4:6],sdate[6:8]]) + 'T' + ':'.join([stime[0:2],stime[2:4],stime[4:len(stime)]])
        end_time = '-'.join([edate[0:4],edate[4:6],edate[6:8]]) + 'T' + ':'.join([etime[0:2],etime[2:4],etime[4:len(etime)]])
        # sdt_obj = datetime.datetime(int(sdate[0:4]), int(sdate[4:6]), int(sdate[6:8]), int(stime[0:2]), int(stime[2:4]), int(stime[4:6]))
        # edt_obj = datetime.datetime(int(edate[0:4]), int(edate[4:6]), int(edate[6:8]), int(etime[0:2]), int(etime[2:4]), int(etime[4:6]))
    return start_time, end_time, sat_name