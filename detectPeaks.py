# this script detects peaks in a spectrum given as a 2 column text file



import sys
import scipy.signal as ss
from myFunctions import *



##################################################
### variables
minimum_mass = 10.9 # minimum mass to allow peaks
maximum_datapoint = 50000 # maximum number of datapoints which the peak detection algorithm will analyze
max_massdiff_from_fullmass = 0.5 # maximum allowed mass deviation from unit masses, else the peak will be deleted
percentile_range = 180 # number of data points above and below the peak in which range to calculate the percentile; default = 110
percentile = 80 # percentile which will be taken as local baseline, default = 30
std_factor = 0.2 # percentile + std_factor * standard_deviation is the minimum threshhold for peaks, default = 0.08
std_range_bot = 500 # lower end of range to calculate standard deviation from
std_range_top = 2000 # upper end of range to calculate standard deviation from
                # this std is used globally to calculate the peak threshhold
mass_bin_width = 0.6 # 'bin-width' for local maximum search, default = 0.7
binning_iterations = 15 # number of iterations for local maximum search
peak_width_min = 1 # parameter of the wavelet peak detection algorithm, default = 1
peak_width_max = 28 # parameter of the wavelet peak detection algorithm, default = 28
peak_width_step = 4 # parameter of the wavelet peak detection algorithm, default = 4
relative_intensity_threshhold = 0.0006 # below this relative intensity peaks will be thrown out, default = 0.00058
relative_intensity_iterations = 3 # number of iterations to calculate relative intensity and filter with threshhold
peakfile_datatype = '%.6f'
##################################################



def detectPeaks(data):
    ### detect peaks in data
    peak_indices = np.array( ss.find_peaks_cwt(data[:maximum_datapoint,1], np.arange(peak_width_min, peak_width_max, peak_width_step)) )
    peaks = np.array([])
    for i in range(peak_indices.size):
        peak_position = data[peak_indices[i], 0]
        peak_intensity = data[peak_indices[i], 1]
        if peaks.size==0:
            peaks = np.array([ peak_position, peak_intensity ]).reshape( [1,2] )
        else:
            peaks = np.append( peaks, np.array([ peak_position, peak_intensity ]).reshape( [1,2] ), axis=0 )
    ### check for false identifications
    local_percentile = get_local_percentile( data, peak_indices, percentile_range, percentile )
    detections_to_delete = np.array([], dtype=int)
    for i in range(peak_indices.size):
        if peaks[i,0] < minimum_mass:
            detections_to_delete = np.append(detections_to_delete, i)
            continue
        if check_peak_validation(peaks[i,0], max_massdiff_from_fullmass) == False:
            detections_to_delete = np.append(detections_to_delete, i)
            continue
        for k in range( binning_iterations ): # bin peaks in local maxima
            j=0
            new_peak_index = peak_indices[i]
            while data[peak_indices[i],0] - data[peak_indices[i]-j,0] < mass_bin_width:
                if peaks[i,1] < data[peak_indices[i]-j,1]:
                    peaks[i,0] = data[peak_indices[i]-j,0]
                    peaks[i,1] = data[peak_indices[i]-j,1]
                    new_peak_index = peak_indices[i]-j
                if peak_indices[i]+j < data[:,0].size:
                    if peaks[i,1] < data[peak_indices[i]+j,1]:
                        peaks[i,0] = data[peak_indices[i]+j,0]
                        peaks[i,1] = data[peak_indices[i]+j,1]
                        new_peak_index = peak_indices[i]+j
                j +=1
            peak_indices[i]=new_peak_index
        if peak_indices[i] == peak_indices[i-1]:
            detections_to_delete = np.append(detections_to_delete, i)
            continue
        if i > 0: # to check for double peaks with same intensity
            if peaks[i,1] == peaks[i-1,1] and peaks[i,0] - peaks[i-1,0] < 0.1 :
                detections_to_delete = np.append(detections_to_delete, i)
                continue
        peak_thr = automatic_threshhold( data, local_percentile[i], std_range_bot, std_range_top, std_factor )
        if peaks[i,1] < peak_thr:
            detections_to_delete = np.append(detections_to_delete, i)
            continue
    [detections_to_delete, peaks, peak_indices, local_percentile] = delete_false_peaks( detections_to_delete, peaks, peak_indices, local_percentile )
    for k in range( relative_intensity_iterations ):
        relative_intensities = calculate_relative_intensities( peaks, local_percentile )
        for i in range( relative_intensities.size ):
            if relative_intensities[i] < relative_intensity_threshhold:
                detections_to_delete = np.append(detections_to_delete, i)
        [detections_to_delete, peaks, peak_indices, local_percentile] = delete_false_peaks( detections_to_delete, peaks, peak_indices, local_percentile )
    return [peaks, peak_indices, local_percentile]
