import sys
import scipy.signal as ss
from myFunctions import *
from automated_recalibration_v3 import automated_recal
import copy
import glob
import numpy as np
from baseline_correction import baseline_correction
from detectPeaks import detectPeaks
import scipy.interpolate as interpolate
#import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
##################################################


i='/home/umair/PycharmProjects/mass_spectro/Recalibration test May2021/original/2021-04-15-122531_T4Phages_NA_1.8e10PFUpermL_1H2O2IPA_0.29mlpmin_93.1%_FL5.35J_neg_des_I1152_dt083.txt'
data = np.loadtxt(i)
file_name = os.path.basename(i)
recalibrated_data = automated_recal(file_name,data)[:10000]
print(recalibrated_data.shape)
baseline_corrected_data = baseline_correction(recalibrated_data)[:10000]
print(baseline_corrected_data.shape)
print(detectPeaks(i))
