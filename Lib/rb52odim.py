'''
Copyright (C) 2017 The Crown (i.e. Her Majesty the Queen in Right of Canada)

This file is an add-on to RAVE.

RAVE is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RAVE and this software are distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with RAVE.  If not, see <http://www.gnu.org/licenses/>.

'''
## Collected functionality for decoding and merging data from Rainbow 5 
# 


## 
# @file
# @author Daniel Michelson and Peter Rodriquez, Environment and Climate Change Canada
# @date 2017-06-14

import sys, os, math, tarfile
import _rb52odim
import _rave, _raveio, _polarvolume


## Rudimentary input file validation
# @param string input file name
def validate(filename):
    if not os.path.isfile(filename):
        raise IOError, "Input file %s is not a regular file. Bailing ..." % filename
    if os.path.getsize(filename) == 0:
        raise IOError, "%s is zero-length. Bailing ..." % filename


## Reads RB5 files and merges their contents into an output ODIM_H5 file
# @param string file name of input file
# @param string file name of output file
def singleRB5(inp_fullfile, out_fullfile=None, return_rio=False):
    validate(inp_fullfile)
    if not _rb52odim.isRainbow5(inp_fullfile):
        raise IOError, "%s is not a proper RB5 raw file" % inp_fullfile
    else:
        rio=_rb52odim.readRB5(inp_fullfile)

    if out_fullfile:
        rio.save(out_fullfile)
    if return_rio:
        return rio


## Reads RB5 files and merges their contents into an output ODIM_H5 file
# @param string list of input file names
# @param string output file name
# @param Boolean if True, return the RaveIOCore object containing the decoded and merged RB5 data
# @ returns RaveIOCore if return_rio=True, otherwise nothing
def combineRB5(ifiles, out_fullfile=None, return_rio=False):
    big_obj=None

    nMEMBERs=len(ifiles)
    for iMEMBER in range(nMEMBERs):
        inp_fullfile=ifiles[iMEMBER]
        validate(inp_fullfile)
        mb=parse_tarball_member_name(inp_fullfile,ignoredir=True)

        if mb['rb5_ftype'] == "rawdata":
            isrb5=_rb52odim.isRainbow5(inp_fullfile)
            if not isrb5:
                raise IOError, "%s is not a proper RB5 raw file" % inp_fullfile
            else:
                rio=_rb52odim.readRB5(inp_fullfile) ## by FILENAME
                this_obj=rio.object
                if rio.objectType == _rave.Rave_ObjectType_PVOL:
                    big_obj=compile_big_pvol(big_obj,this_obj,mb,iMEMBER)
                else:
                    big_obj=compile_big_scan(big_obj,this_obj,mb)
    
    container=_raveio.new()
    container.object=big_obj
    if out_fullfile:
        container.save(out_fullfile)
    if return_rio:
        return container


## Reads a single RB5 tarball and merges its contents into an output ODIM_H5 file
# @param string input tarball file name
# @param string output file name
# @param string output base directory, only used when creating new output file name  
# @param Boolean if True, return the RaveIOCore object containing the decoded and merged RB5 data
# @ returns RaveIOCore if return_rio=True, otherwise nothing
def combineRB5FromTarball(ifile, ofile, out_basedir=None, return_rio=False):
    validate(ifile)
    big_obj=None

    tar=tarfile.open(ifile)
    member_arr=tar.getmembers()
    nMEMBERs=len(member_arr)
    for iMEMBER in range(nMEMBERs):
        this_member=member_arr[iMEMBER]
        inp_fullfile=this_member.name
        mb=parse_tarball_member_name(inp_fullfile)

        if mb['rb5_ftype'] == "rawdata":
            obj_mb=tar.extractfile(this_member) #EXTRACTED MEMBER OBJECT
#            import pdb; pdb.set_trace()

            rb5_buffer=obj_mb.read() #NOTE: once read(), buffer is detached from obj_mb
            isrb5=_rb52odim.isRainbow5buf(rb5_buffer)
            if not isrb5:
                raise IOError, "%s is not a proper RB5 buffer" % rb5_buffer
            else:
#                buffer_len=len(rb5_buffer)
                buffer_len=obj_mb.size
#                print '### inp_fullfile = %s (%ld)' % (inp_fullfile, buffer_len)
#                rio=_rb52odim.readRB5buf(inp_fullfile,rb5_buffer,long(buffer_len)) ## by BUFFER
                rio=_rb52odim.readRB5buf(inp_fullfile,rb5_buffer) ## by BUFFER
#                rio=_rb52odim.readRB5(inp_fullfile)              ## by FILENAME
                this_obj=rio.object

                if rio.objectType == _rave.Rave_ObjectType_PVOL:
                    big_obj=compile_big_pvol(big_obj,this_obj,mb,iMEMBER)
                else:
                    big_obj=compile_big_scan(big_obj,this_obj,mb)

    #auto output filename (as needed)
    if not ofile and not return_rio:
        tb=parse_tarball_name(ifile)
        out_basefile=".".join([\
            tb['nam_site'],\
            tb['nam_timestamp'],\
            tb['nam_sdf'],\
            'h5'\
            ])
        out_fulldir=os.path.join(\
            out_basedir,\
            tb['nam_site'],\
            tb['nam_date'],\
            tb['nam_sdf']\
            )
        if not os.path.exists(out_fulldir):
            os.makedirs(out_fulldir)
        out_fullfile=os.path.join(out_fulldir,out_basefile)
    else:
        out_fullfile=ofile

    container=_raveio.new()
    container.object=big_obj
    if out_fullfile:
        container.save(out_fullfile)
    if return_rio:
        return container


## Read multiple RB5 scan tarballs and output a single ODIM_H5 PVOL file or, alternatively, a RaveIOCore object. This is a simple wrapper for reading the input data required by \ref mergeOdimScans2Pvol
# @param list of input tarball files, each containing RB5 sweep moment files
# @param string output file name
# @param Boolean if True, return the RaveIOCore object containing the merged ODIM data
# @param string cycle time interval in minutes
# @param string combined task name
# @ returns RaveIOCore if return_rio=True, otherwise nothing
def combineRB5Tarballs2Pvol(ifiles, out_fullfile=None, return_rio=False, interval=None, taskname=None):
    rio_arr = []

    for ifile in ifiles:
        validate(ifile)
        rio = combineRB5FromTarball(ifile, None, None, True)
        if rio: rio_arr.append(rio)

    return mergeOdimScans2Pvol(rio_arr, out_fullfile, return_rio, interval, taskname)


## Merge multiple ODIM_H5 SCAN contents into an output ODIM_H5 PVOL file or, alternatively, a RaveIOCore object
# @param list of RaveIOCore objects (ODIM_H5 SCANs)
# @param string output file name
# @param Boolean if True, return the RaveIOCore object containing the merged ODIM data
# @param string cycle time interval in minutes
# @param string combined task name
# @ returns RaveIOCore if return_rio=True, otherwise nothing
def mergeOdimScans2Pvol(rio_arr, out_fullfile=None, return_rio=False, interval=None, taskname=None):
    pvol=None

    if not interval:
        interval=5
    if not taskname:
        taskname='dummy'

    nSCANs=len(rio_arr)
    for iSCAN in range(nSCANs):
        rio=rio_arr[iSCAN]

        if rio.objectType != _rave.Rave_ObjectType_SCAN:
            raise IOError, "Expecting obj_SCAN not : %s" % type(rio.object)
        else:
            scan=rio.object
            #scan.getAttributeNames()
            #print scan.getAttribute('how/task')

            if pvol is None: #clone
                pvol=_polarvolume.new()
                pvol.source=scan.source
                import datetime as dt
                scan_iso8601="-".join([scan.date[0:4],scan.date[4:6],scan.date[6:9]])+"T"+\
                             ":".join([scan.time[0:2],scan.time[2:4],scan.time[4:7]])
                scan_systime=float(dt.datetime.strptime(scan_iso8601,'%Y-%m-%dT%H:%M:%S').strftime("%s"))
                cycle_nsecs=float(interval)*60.
                cycle_systime=scan_systime - scan_systime%cycle_nsecs
                cycle_iso8601=dt.datetime.fromtimestamp(cycle_systime).isoformat()

                pvol.date=''.join(cycle_iso8601[:10].split('-'))
                pvol.time=''.join(cycle_iso8601[11:].split(':'))
                pvol.longitude=scan.longitude
                pvol.latitude=scan.latitude
                pvol.height=scan.height
                pvol.beamwidth=scan.beamwidth
                sATTRIB='how/task'; pvol.addAttribute(sATTRIB,taskname)
                sATTRIB='how/TXtype'; pvol.addAttribute(sATTRIB,scan.getAttribute(sATTRIB))
                sATTRIB='how/beamwH'; pvol.addAttribute(sATTRIB,scan.getAttribute(sATTRIB))
                sATTRIB='how/beamwV'; pvol.addAttribute(sATTRIB,scan.getAttribute(sATTRIB))
                sATTRIB='how/polmode'; pvol.addAttribute(sATTRIB,scan.getAttribute(sATTRIB))
                sATTRIB='how/poltype'; pvol.addAttribute(sATTRIB,scan.getAttribute(sATTRIB))
                sATTRIB='how/software'; pvol.addAttribute(sATTRIB,scan.getAttribute(sATTRIB))
                sATTRIB='how/sw_version'; pvol.addAttribute(sATTRIB,scan.getAttribute(sATTRIB))
                sATTRIB='how/system'; pvol.addAttribute(sATTRIB,scan.getAttribute(sATTRIB))
                sATTRIB='how/wavelength'; pvol.addAttribute(sATTRIB,scan.getAttribute(sATTRIB))
            pvol.addScan(scan)

    container=_raveio.new()
    container.object=pvol
    if out_fullfile:
        container.save(out_fullfile)
    if return_rio:
        return container


### Convenience functions follow ###


def parse_tarball_name(fullfile):
    fulldir=os.path.dirname(fullfile)
    basefile=os.path.basename(fullfile)
    elem_arr=basefile[:-len('.tar.gz')].split("_")
    nELEMs=len(elem_arr)
    nam_site=elem_arr[0]
    nam_yyyymmddhhmm=elem_arr[1]
    nam_iso8601=nam_yyyymmddhhmm[ 0: 4]+'-'+\
                nam_yyyymmddhhmm[ 4: 6]+'-'+\
                nam_yyyymmddhhmm[ 6: 8]+' '+\
                nam_yyyymmddhhmm[ 8:10]+':'+\
                nam_yyyymmddhhmm[10:12]+':00'
    nam_date=nam_iso8601[0:10]
    nam_hhmmZ=nam_yyyymmddhhmm[8:12]+'Z'
    nam_timestamp=nam_date+'_'+nam_hhmmZ
    nam_sdf="_".join(elem_arr[2:])

    return{\
        'fullfile':fullfile,\
        'fulldir': fulldir,\
        'basefile':basefile,\
        'nam_site':nam_site,\
        'nam_yyyymmddhhmm':nam_yyyymmddhhmm,\
        'nam_iso8601':nam_iso8601,\
        'nam_date':nam_date,\
        'nam_hhmmZ':nam_hhmmZ,\
        'nam_timestamp':nam_timestamp,\
        'nam_sdf':nam_sdf\
        }

def parse_tarball_member_name(fullfile,ignoredir=False):
    fulldir=os.path.dirname(fullfile)
    basefile=os.path.basename(fullfile)
    nam_yyyymmddhhmmss=basefile[0:14]
    nam_iso8601=nam_yyyymmddhhmmss[ 0: 4]+'-'+\
                nam_yyyymmddhhmmss[ 4: 6]+'-'+\
                nam_yyyymmddhhmmss[ 6: 8]+' '+\
                nam_yyyymmddhhmmss[ 8:10]+':'+\
                nam_yyyymmddhhmmss[10:12]+':'+\
                nam_yyyymmddhhmmss[12:14]
    nam_file_ver=basefile[14:16]
    dot_loc=basefile.find(".")
    nam_sparam=basefile[16:dot_loc]
    nam_scan_type=basefile[dot_loc+1:]

    if bool(ignoredir):
        rb5_date=""
        rb5_sdf=""
        rb5_ppdf=""
        rb5_site=""
        rb5_ftype="rawdata"
    else:
        elem_arr=fulldir.split("/")
        nELEMs=len(elem_arr)
        rb5_date=elem_arr[nELEMs-1]
        rb5_sdf=elem_arr[nELEMs-2]
        if not rb5_sdf.endswith(nam_scan_type): #check for ppdf
            rb5_ppdf=rb5_sdf
            rb5_sdf="" #unknown until decode
        else:
            rb5_ppdf=""
        rb5_site=elem_arr[nELEMs-3]
        rb5_ftype=elem_arr[nELEMs-4]

    return {\
        'fullfile':fullfile,\
        'fulldir':fulldir,\
        'basefile':basefile,\
        'nam_yyyymmddhhmmss':nam_yyyymmddhhmmss,\
        'nam_iso8601':nam_iso8601,\
        'nam_file_ver':nam_file_ver,\
        'nam_sparam':nam_sparam,\
        'nam_scan_type':nam_scan_type,\
        'rb5_date':rb5_date,\
        'rb5_sdf':rb5_sdf,\
        'rb5_ppdf':rb5_ppdf,\
        'rb5_site':rb5_site,\
        'rb5_ftype':rb5_ftype,\
        }

def compile_big_scan(big_scan,scan,mb):
    sparam_arr=scan.getParameterNames()
    #assume 1 param per scan of input tar_member
    if len(sparam_arr) != 1 :
        raise IOError, 'Too many sparams: %s' % sparam_arr
        return

    sparam=sparam_arr[0]
    param=scan.getParameter(sparam)

    if big_scan is None:
        big_scan=scan.clone() #clone
        big_scan.removeParameter(sparam) #remove existing param

    if mb['rb5_ppdf'] != "":
        old_sparam=sparam
        rb5_ppdf=mb['rb5_ppdf']
        new_sparam=old_sparam+rb5_ppdf[rb5_ppdf.find("."):]
        scan.removeParameter(old_sparam) #make orphan
        param.quantity=new_sparam #update orphan
        scan.addParameter(param) #add orphan
        sparam=new_sparam #update sparam

    big_scan.addParameter(param) #add
    return big_scan

def compile_big_pvol(big_pvol,pvol,mb,iMEMBER):
    #pvol=_polarvolume.new()
    #dir(pvol)

    nSCANs=pvol.getNumberOfScans()
    if big_pvol is None: #clone
        big_pvol=pvol.clone()

    for iSCAN in range(nSCANs):
        if iMEMBER == 0:
            big_scan=None #begin with empty scans (removes existing param)
        else:
            big_scan=big_pvol.getScan(iSCAN)
        this_scan=pvol.getScan(iSCAN)
        big_scan=compile_big_scan(big_scan,this_scan,mb)
        big_pvol.removeScan(iSCAN)
        big_pvol.addScan(big_scan)
        big_pvol.sortByElevations(1) # resort

    return big_pvol


if __name__=="__main__":
    pass