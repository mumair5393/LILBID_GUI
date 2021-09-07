# dialog script for the automatic peak detection
# asks for which files/folders the automatic peak detection
# defined by peakDetection.py should be done
#
# therefore this script needs peakDetection.py in the same folder
# and will hand DATAFILE and a peak threshhold over



from myFunctions import *
from detectPeaks import *
import os



### look up files to run peak detection for
sorf = raw_input( 'do you want to run peak detection and calculate relative intensities ' +
        'for a single file or for all files in a specific folder? \n' +
        '( \'s\' for single file, \'f\' for folder ) \n')
print "\n"
if sorf != "s" and sorf != "f":
    error(  )
DATAFOLDER = raw_input ( 'please give the folder: \n' )
check_folder_existence( DATAFOLDER )
if sorf == "s":
    DATAFILE = raw_input( 'please give the filename: \n' )
    print "\n"
    DATAFILE = DATAFOLDER + '/' + DATAFILE
    check_file_existence( DATAFILE )
    DFILES = np.array( [DATAFILE] )
elif sorf == "f":
    DFILES = np.array([])
    for files in os.listdir( DATAFOLDER ):
        if files.endswith( '.txt' ) and not 'peaks' in files:
            DATAFILE = DATAFOLDER + '/' + files
            check_file_existence( DATAFILE )
            DFILES = np.append( DFILES, DATAFILE )



### ask for overwrite and threshhold
print "do you want to run automatic peak detection to overwrite existing data?"
# ( note: relative intensities will always be calculated for every file )
overwriteYN = raw_input('(y or n) \n')
if overwriteYN != 'y' and overwriteYN != 'n':
    error()
print "\n"
print 'do you want a threshhold to be chosen automatically or do you want to chose one manually?'
print '( \'A\' for automatically, \'M\' for manually )'
aorm = raw_input ( 'your answer: ' )
if aorm == "A":
    threshhold = 0
elif aorm == "M":
    threshhold = "placeholder"
    while isinstance ( threshhold, float ) != True:
        try:
            threshhold = float( raw_input ( "which threshhold do you want to use? \n" ) )
        except ValueError:
            print ( "not a number, try again" )
else:
    print "not a valid answer"
    error(  )
print "\n"



### actually run peakDetection, relativeIntensities and save peak files
for i in range( len( DFILES ) ):
    DATAFILE = DFILES[i]
    if overwriteYN == "y" or check_peakfile_existence(DATAFILE) == False:
        [peaks, peak_indices, local_percentile] = detectPeaks( DATAFILE, aorm, str( threshhold ) )
    else:
        data = np.array( np.loadtxt( DATAFILE ) )
        PEAKFILE = strip_ending( DATAFILE, ".txt" ) + ".peaks.txt"
        peaks = np.array( np.genfromtxt( PEAKFILE, usecols=( 0,1 ) ) )
        peaks = peaks[ np.lexsort( ( peaks[:,1], peaks[:,0] ) ) ]
        peak_indices = np.array( [] )
        for i in range( peaks.shape[0] ):
            for j in range( data.shape[0] ):
                if float( peakfile_datatype %peaks[i,0] ) >= float( peakfile_datatype %data[j,0] ):
                    peak_indices = np.append( peak_indices, j )
                    break
        local_percentile = get_local_percentile( data, peak_indices, percentile_range, percentile )
    relative_intensities = calculate_relative_intensities( peaks, local_percentile )
    ### save peaks [mass, measured intensity, baseline, relative intensity]
    #peaks = np.append( peaks, local_percentile, axis=1 ) # append baseline
    peaks = np.append( peaks, relative_intensities.reshape( [relative_intensities.size, 1] ), axis=1 )
    write_peakfile( DATAFILE, peaks, peakfile_datatype, std_factor, "local_percentile" )



print '\n'
raw_input( 'press any key to quit' )



