from myFunctions import *
from detectPeaks import detectPeaks
import pandas as pd
import ions_dict
timestep = 2*10**( -3 ) # in mikrosekunden

def m( t, params ):
    return params[0]*t**2 + params[1]*t + params[2]

def lower_mass_region_peaks(detected_peaks, ion_mode):
    correct_peaks = eval('ions_dict.'+ion_mode)
    correct_peaks = pd.DataFrame.from_dict(correct_peaks)

    peaks_with_exact_masses = []
    # detect peaks for mass less than 60
    for i in detected_peaks[(detected_peaks[:,0]<60)]:
        for j in correct_peaks['integer mass']:
            if j == np.round(i[0]):
                i[3] = list(correct_peaks['exact mass'])[list(correct_peaks['integer mass']).index(np.round(i[0]))]
                peaks_with_exact_masses.append(i)
                
    if not peaks_with_exact_masses:
        for i in detected_peaks[(detected_peaks[:,0]<60)]:
            i[3] = np.round(i[0])
    
    return np.array(peaks_with_exact_masses)
    
def higher_mass_region_peaks(detected_peaks, peaks_in_previous_region, ion_mode, region_range):
    region = detected_peaks[(detected_peaks[:, 0] > region_range[0]) & (detected_peaks[:, 0] < region_range[1])]
    if region.size==0:
        pass
    else:
        correct_peaks = eval('ions_dict.'+ion_mode)
        correct_peaks = pd.DataFrame.from_dict(correct_peaks)
        corrected_peaks_in_region = []
        if peaks_in_previous_region.size==0:
            peak_diff = 0
        else:
            peak_diff = peaks_in_previous_region[-1, 3] - peaks_in_previous_region[-1, 0]
        for i in range(len(region)):
            for j in correct_peaks['integer mass']:
                if j==np.round(region[i, 0] + peak_diff):
                    region[i, 3] = list(correct_peaks['exact mass'])[list(correct_peaks['integer mass']).index(j)]
                    corrected_peaks_in_region.append(region[i])
            if region[i, 3] == 0:
                if region[i, 0] + peak_diff - np.int(region[i, 0]) < 0.5:
                    region[i, 3] = np.floor(region[i, 0])
                else:
                    region[i, 3] = np.ceil(region[i, 0])
               
            peak_diff = region[i, 3] - region[i, 0]
        if not corrected_peaks_in_region:
            corrected_peaks_in_region.append(region[region[:,1].argmax()])
        
        if peaks_in_previous_region.size==0:
            peaks_in_previous_region = np.array(corrected_peaks_in_region)
        else:
            peaks_in_previous_region = np.vstack((peaks_in_previous_region,np.array(corrected_peaks_in_region)))
    return peaks_in_previous_region

def automated_recal(file_name, data):
    if '_pos_' in file_name:
        ion_mode = 'pos'
    elif'_neg_' in file_name:
        ion_mode = 'neg'
    else:
        ion_mode = 'pos'
    check_recal_manually = False
    peaks, peak_indices, local_percentile=detectPeaks(data)
    detected_peaks = np.hstack([np.hstack([peaks,local_percentile]),np.zeros((len(peaks),1))])
    #print(detected_peaks)
    peaks_to_recal=lower_mass_region_peaks(detected_peaks, ion_mode)
    peaks_to_recal=higher_mass_region_peaks(detected_peaks, peaks_to_recal, ion_mode, (60,120))
    peaks_to_recal=higher_mass_region_peaks(detected_peaks, peaks_to_recal, ion_mode, (120,190))
    peaks_to_recal=higher_mass_region_peaks(detected_peaks, peaks_to_recal, ion_mode, (190,237))
    recalibrated_peaks = peaks_to_recal
    peak_condition = 1.5*abs(recalibrated_peaks[-1,0]-recalibrated_peaks[-1,3]) < abs(recalibrated_peaks[-2,0]-recalibrated_peaks[-2,3])
    if (len(recalibrated_peaks)<3) or peak_condition:
        check_recal_manually = True
    print("check manually: ", check_recal_manually)
    print(pd.DataFrame(np.stack([recalibrated_peaks[:,0],recalibrated_peaks[:,3]], axis=1),columns=['original', 'corrected to']).to_string(index=False))
    
    for j in range(recalibrated_peaks.shape[0]):
        for t in range(data.shape[0]):
            if data[t, 0] > recalibrated_peaks[j, 0]:
                recalibrated_peaks[j, 0] = (t-1) * timestep
                break
    fitparameter = np.polyfit( recalibrated_peaks[:, 0], recalibrated_peaks[:, 3], 2)
    ### apply new fit function to data[0,:]
    recalibrated_data=np.copy(data)
    for j in range(recalibrated_data.shape[0]):
        recalibrated_data[j, 0] = m(j*timestep, fitparameter)
    return recalibrated_data, check_recal_manually

def manual_recalibration(data, detected_peaks, corrected_peaks):
    recalibrated_peaks = np.hstack([detected_peaks.reshape(-1, 1), corrected_peaks.reshape(-1, 1)])
    for j in range(recalibrated_peaks.shape[0]):
        for t in range(data.shape[0]):
            if data[t, 0] > recalibrated_peaks[j, 0]:
                recalibrated_peaks[j, 0] = (t-1) * timestep
                break
    fitparameter = np.polyfit( recalibrated_peaks[:, 0], recalibrated_peaks[:, 1], 2)
    ### apply new fit function to data[0,:]
    recalibrated_data=np.copy(data)
    for j in range(recalibrated_data.shape[0]):
        recalibrated_data[j, 0] = m(j*timestep, fitparameter)
    return recalibrated_data