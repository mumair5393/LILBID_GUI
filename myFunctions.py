#
# define the functions used for the peak detection and plotting
#

import os
import numpy as np
import scipy.stats as sstats



def error( ):
# give out error message
    print("error!")
    raw_input( "press any key to quit!" )
    quit( )



def strip_ending( fname, ending ):
# strip ending of fname
    if not fname.endswith( ending ):
        return fname
    return fname[:-len( ending )]



def check_file_existence( filename ):
# check if a file with filename exists
    if not os.path.isfile( filename ):
        print('\n' + 'the file \"' + filename + '\"' + ' does not exist')
        error(  )



def check_peakfile_existence( datafile ):
# check if a peak file for datafile exists
    trunk = strip_ending( datafile, ".txt")
    peakfile_candidate = trunk + ".peaks.txt"
    return os.path.isfile( peakfile_candidate )



def check_folder_existence( foldername ):
# check if a folder with foldername exists
    if not os.path.isdir( foldername ):
        print('\n' + 'the folder \"' + foldername + '\"' + ' does not exist')
        error(  )



def lines_in_file( file ):
# count number of lines in file
    f = open( file, 'r')
    lines = sum( 1 for line in f)
    return lines



def m(t):
# mass calibration, not used generally, but included for testing purposes
	m = 0.448*t**2 + 0.253*t + 0.351
	return m



def get_local_percentile( data_array, indices, percentile_range, percentile ):
# retrieve the local percentile in data_array at indices
    local_percentile = np.array([])
    for i in range(indices.size):
        lower_end = np.max( [indices[i]-percentile_range, 0] )
        upper_end = np.min( [indices[i]+percentile_range, data_array.shape[0]] )
        loc_per = sstats.scoreatpercentile(data_array[ lower_end : upper_end ,1], percentile )
        local_percentile = np.append(local_percentile, loc_per)
    return local_percentile.reshape([local_percentile.size,1])



def automatic_threshhold( data_array, percentile, std_range_bot, std_range_top, std_factor ):
# calculate an automatic threshhold for peak validation
    std = np.std( data_array[std_range_bot:std_range_top,1] )
    # if the formula for autothr is changed, beware to change the header of the peakfile
    autothr = percentile + std_factor*std
    return autothr



def check_peak_validation( peak_posi, max_massdiff_from_fullmass ):
# throw possible peak away with "half masses"
    if abs( round(peak_posi, 0) - round(peak_posi, 2) ) > max_massdiff_from_fullmass:
        return False
    return True



def delete_false_peaks( detections_to_delete, peaks, peak_indices, local_percentile ):
    for i in range(detections_to_delete.size):
        peaks = np.delete(peaks,detections_to_delete[i]-i,0)
        peak_indices = np.delete(peak_indices,detections_to_delete[i]-i,0)
        local_percentile = np.delete(local_percentile,detections_to_delete[i]-i,0)
    return [ np.array([], dtype=int),peaks, peak_indices, local_percentile ]



def calculate_relative_intensities( peak_array, baseline ):
# calculate relative intensities
    if peak_array.shape[0] != baseline.shape[0]:
        print("wrong length of peak or baseline array ")
        error(  )
    relative_intensities = np.array([])
    for i in range(peak_array.shape[0]):
        rel_int = peak_array[i,1] - baseline[i]
        relative_intensities = np.append(relative_intensities, rel_int)
    relative_intensities = relative_intensities / abs( np.sum(relative_intensities) )
    return relative_intensities
     


def write_peakfile_header( pfile, std_factor, baseline ):
# write header for peakfile
# !change if threshhold is changed!
    pfile.write("# threshhold used: local percentile + " +str(std_factor) + " *std_deviation \n")
    if baseline == "local_percentile":
        pfile.write( "# baseline used: local percentile around peaks \n" )
    if type( baseline ) is float:
        pfile.write( "# baseline used: global baseline = " + str( baseline ) +" \n" )
    pfile.write("# 1st col: mass [amu]; 2nd col: measured intensity [V]; 3rd col: relative intensity - baseline corrected  \n")
    return pfile    



def write_peakfile( filename, peaks, peakfile_datatype, std_factor, baseline ):
# save peak positions and intensities in file
# !may need to be changed if the header is changed!
    if filename.endswith( ".txt" ) and not "peak" in filename:
    # expects filename to be either datafilename or already peakfilename
        peakfilename = strip_ending( filename, ".txt" ) + ".peaks.txt"
    else:
        peakfilename = filename
    pfile = open(peakfilename, 'w')
    pfile = write_peakfile_header( pfile, std_factor, baseline )
    np.savetxt ( pfile, peaks, fmt=peakfile_datatype )
    pfile.close()
    #print 'saved: ' + peakfilename


