# purpose: recalibrate the time to mass conversion of the time of flight
# data files. the quality of standard calibration usually is dependent on
# the delaytime of the mass spectrometer.
#
# expected input:
# in the peaks.txt files a fourth column has to be added with the supposed
# mass.
#
# what does it do:
# scan a given folder for peaks.txt files with a fourth column. if there is
# one, it fits a parabolic function and recalibrates the according data
# file



from myFunctions import *



##############################
### variables
timestep = 2*10**( -3 ) # in mikrosekunden
datafile_datatype = '%.6f'
##############################



### fit function for quadratic fit
# normaly "m=((t-b)/a)**2" is used as fit function. but numpy.polyfit can only fit standard polynomial form
def m( t, params ):
    return params[0]*t**2 + params[1]*t + params[2]
mass_cal_string = "a*t**2+b*t+c"



### search for datafiles to renew calibration
DATAFOLDER = raw_input (  'please give the folder: \n' )
check_folder_existence(  DATAFOLDER )
DFILES = np.array( [])
for files in os.listdir(  DATAFOLDER ):
    if files.endswith(  '.txt' ) and not 'peaks' in files:
        DATAFILE = DATAFOLDER + '/' + files
        check_file_existence(  DATAFILE )
        DFILES = np.append(  DFILES, DATAFILE  )
print ""



for i in range(  len(  DFILES ) ):
### load data ( currently assigned mass ; proposed correct mass )
    DATAFILE = DFILES[i]
    PEAKFILE = strip_ending( DATAFILE, ".txt" ) + ".peaks.txt"
    peaks = np.array( np.loadtxt( PEAKFILE ) ) # should be in a format of: 1st column currently assigned mass; 4th column: proposed mass
    if len( peaks.shape ) ==  1:
        peaks = peaks.reshape( [1,peaks.shape[0]] )
    if len( peaks.shape ) ==  0:
        print DFILES[i] + " has no peaks in file"
        continue
    if peaks.shape[1] != 4: # if peaks.txt has an unexpected format, try next file
        continue
    data = np.array( np.loadtxt( DATAFILE ) )
    for j in range( peaks.shape[0] ):
        for t in range( data.shape[0] ):
            if data[t,0] > peaks[j,0]:
                peaks[j,0] = (t-1) * timestep
                break
### find new fit function m( t )
    fitparameter = np.polyfit( peaks[:,0], peaks[:,3], 2 )
### apply new fit function to data[0,:]
    data = np.array(  np.loadtxt(  DATAFILE )  )
    measurementTime = data.shape[0] # total time in data points # wirklich?
    for j in range( data.shape[0] ):
        data[j,0] = m( j*timestep, fitparameter)
### read header of the datafile
    headerfile = open( DATAFILE )
    header = np.array( [""], dtype=np.str ).reshape( [1] )
    isHeader = True
    while isHeader == True:
        line = headerfile.readline(  )
        if line[0] == "#":
            header = np.append( header, line )
        else:
            isHeader = False
    headerfile.close()
### adapt header if needed
    for j in range( header.size ):
        if j != 0:
            if header[j][1] == "#" or header[j][1] == " ":
                header[j] = header[j][0] + header[j][2:]
            if header[j][0] == "#" or header[j][0] == " ":
                header[j] = header[j][0] + header[j][1:]
        if "masscalibrationa" in header[j]:
            header[j] = "#masscalibrationa=" + str( "%.6f" %fitparameter[0] ) + "\n" #str( a ) + "\n"
            continue
        if "masscalibrationb" in header[j]:
            header[j] = "#masscalibrationb=" + str( "%.6f" %fitparameter[1] ) + "\n" #str( b ) + "\n"
            continue
        if "masscalibrationc" in header[j]:
            header[j] = "#masscalibrationc=" + str( "%.6f" %fitparameter[2] ) + "\n" #notUsed" + "\n"
            continue
        if "mcal_form" in header[j]:
            header[j] = "#mcal_form:" + mass_cal_string + "\n"
            continue
### save new data - old file will be overwritten
    header_str = ""
    for j in range( header.size ):
        header_str = header_str + header[j][1:]
    np.savetxt( DATAFILE, data, fmt=datafile_datatype, header=header_str[:-1] )
    print "recalibrated: " + DATAFILE



raw_input( "press any key to close" )


