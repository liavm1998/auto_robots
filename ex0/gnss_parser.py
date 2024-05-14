import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import sys, os, csv
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import navpy

from gnssutils import EphemerisManager
import simplekml

parent_directory = os.path.split(os.getcwd())[0]
ephemeris_data_directory = os.path.join(parent_directory, 'data')
manager = EphemerisManager(ephemeris_data_directory)

sys.path.insert(0, parent_directory)
WEEKSEC = 604800
LIGHTSPEED = 2.99792458e8


################################
# Help functions
################################

def calculate_locations_data_frame(ecef_list_with_times):
    locations_df = []
    # Iterate over each tuple in ecef_list_with_times
    for (coord, time) in ecef_list_with_times:
        # Convert ECEF coordinates to LLA coordinates
        lla_coords = navpy.ecef2lla(coord)
        
        # Extract individual components
        lla_lat = lla_coords[0]
        lla_lon = lla_coords[1]
        lla_alt = lla_coords[2]
        ecef_x = coord[0]
        ecef_y = coord[1]
        ecef_z = coord[2]
        
        # Create a tuple with the required components
        row = (time, lla_lat, lla_lon, lla_alt, ecef_x, ecef_y, ecef_z)
        
        # Append the tuple to the locations_df list
        locations_df.append(row)
    return pd.DataFrame(locations_df, columns=["GPS time", "Pos.X", "Pos.Y", "Pos.Z", "Lat", "Lon", "Alt"],index=None)

def calculate_satellite_position(ephemeris, transmit_time, one_epoch):
    earth_gravity = 3.986005e14
    Earth_angular_velocity = 7.2921151467e-5 
    relativistic_correction_factor  = -4.442807633e-10 # used to relativistic correction to the satellite's clock
    sv_position = pd.DataFrame()
    sv_position['satPRN'] = ephemeris.index
    sv_position.set_index('satPRN', inplace=True)
    sv_position['GPS time'] = transmit_time - ephemeris['t_oe']
    A = ephemeris['sqrtA'].pow(2)
    n_0 = np.sqrt(earth_gravity / A.pow(3))
    n = n_0 + ephemeris['deltaN']
    M_k = ephemeris['M_0'] + n * sv_position['GPS time']
    E_k = M_k
    err = pd.Series(data=[1]*len(sv_position.index))
    i = 0
    while err.abs().min() > 1e-8 and i < 10:
        new_vals = M_k + ephemeris['e']*np.sin(E_k)
        err = new_vals - E_k
        E_k = new_vals
        i += 1
        
    sinE_k = np.sin(E_k)
    cosE_k = np.cos(E_k)
    delT_r = relativistic_correction_factor  * ephemeris['e'].pow(ephemeris['sqrtA']) * sinE_k
    delT_oc = transmit_time - ephemeris['t_oc']
    sv_position['Sat.bias'] = ephemeris['SVclockBias'] + ephemeris['SVclockDrift'] * delT_oc + ephemeris['SVclockDriftRate'] * delT_oc.pow(2)

    v_k = np.arctan2(np.sqrt(1-ephemeris['e'].pow(2))*sinE_k,(cosE_k - ephemeris['e']))

    Phi_k = v_k + ephemeris['omega']

    sin2Phi_k = np.sin(2*Phi_k)
    cos2Phi_k = np.cos(2*Phi_k)

    du_k = ephemeris['C_us']*sin2Phi_k + ephemeris['C_uc']*cos2Phi_k
    dr_k = ephemeris['C_rs']*sin2Phi_k + ephemeris['C_rc']*cos2Phi_k
    di_k = ephemeris['C_is']*sin2Phi_k + ephemeris['C_ic']*cos2Phi_k

    u_k = Phi_k + du_k

    r_k = A*(1 - ephemeris['e']*np.cos(E_k)) + dr_k

    i_k = ephemeris['i_0'] + di_k + ephemeris['IDOT']*sv_position['GPS time']

    x_k_prime = r_k*np.cos(u_k)
    y_k_prime = r_k*np.sin(u_k)

    Omega_k = ephemeris['Omega_0'] + (ephemeris['OmegaDot'] - Earth_angular_velocity)*sv_position['GPS time'] - Earth_angular_velocity*ephemeris['t_oe']

    sv_position['Sat.X'] = x_k_prime*np.cos(Omega_k) - y_k_prime*np.cos(i_k)*np.sin(Omega_k)
    sv_position['Sat.Y'] = x_k_prime*np.sin(Omega_k) + y_k_prime*np.cos(i_k)*np.cos(Omega_k)
    sv_position['Sat.Z'] = y_k_prime*np.sin(i_k)
    sv_position["pseudorange"] = one_epoch["Pseudorange_Measurement"] + LIGHTSPEED * sv_position['Sat.bias']
    sv_position["cn0"] = one_epoch["Cn0DbHz"]
    
    return sv_position

def least_squares(receiver_positions, measured_pseudorange, initial_receiver_position, initial_clock_bias):
    position_change = 100 * np.ones(3)  # Change in position
    clock_bias = initial_clock_bias
    # Set up the G matrix with the right dimensions. We will later replace the first 3 columns
    # Note that clock_bias here is the clock bias in meters equivalent, so the actual clock bias is clock_bias / LIGHTSPEED
    G = np.ones((measured_pseudorange.size, 4))
    iterations = 0
    while np.linalg.norm(position_change) > 1e-3:
        # Eq. (2):
        distances = np.linalg.norm(receiver_positions - initial_receiver_position, axis=1)
        # Eq. (1):
        estimated_pseudorange = distances + initial_clock_bias
        # Eq. (3):
        delta_pseudorange = measured_pseudorange - estimated_pseudorange
        G[:, 0:3] = -(receiver_positions - initial_receiver_position) / distances[:, None]
        # Eq. (4):
        solution = np.linalg.inv(np.transpose(G) @ G) @ np.transpose(G) @ delta_pseudorange
        # Eq. (5):
        position_change = solution[0:3]
        clock_bias_change = solution[3]
        initial_receiver_position = initial_receiver_position + position_change
        initial_clock_bias = initial_clock_bias + clock_bias_change
    norm_delta_pseudorange = np.linalg.norm(delta_pseudorange)
    return initial_receiver_position, initial_clock_bias, norm_delta_pseudorange

def create_kml_file(coords):
    output_file = "coordinates.kml"
    kml = simplekml.Kml()
    for coord in coords:
        lat, lon, alt = coord
        kml.newpoint(name="", coords=[(lon, lat, alt)])
    kml.save(output_file)

def log_to_measurment(input_filepath):
    with open(input_filepath) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0][0] == '#':
                if 'Fix' in row[0]:
                    android_fixes = [row[1:]]
                elif 'Raw' in row[0]:
                    measurements = [row[1:]]
            else:
                if row[0] == 'Fix':
                    android_fixes.append(row[1:])
                elif row[0] == 'Raw':
                    measurements.append(row[1:])

    android_fixes = pd.DataFrame(android_fixes[1:], columns = android_fixes[0])
    measurements = pd.DataFrame(measurements[1:], columns = measurements[0])
    return measurements, android_fixes

def format_satelite_ID(measurements):
    measurements.loc[measurements['Svid'].str.len() == 1, 'Svid'] = '0' + measurements['Svid']
    measurements.loc[measurements['ConstellationType'] == '1', 'Constellation'] = 'G'
    measurements.loc[measurements['ConstellationType'] == '3', 'Constellation'] = 'R'
    measurements['satPRN'] = measurements['Constellation'] + measurements['Svid']
    return measurements

def handle_numeric_cols(measurements):
    measurements['Cn0DbHz'] = pd.to_numeric(measurements['Cn0DbHz'])
    measurements['TimeNanos'] = pd.to_numeric(measurements['TimeNanos'])
    measurements['FullBiasNanos'] = pd.to_numeric(measurements['FullBiasNanos'])
    measurements['ReceivedSvTimeNanos']  = pd.to_numeric(measurements['ReceivedSvTimeNanos'])
    measurements['PseudorangeRateMetersPerSecond'] = pd.to_numeric(measurements['PseudorangeRateMetersPerSecond'])
    measurements['ReceivedSvTimeUncertaintyNanos'] = pd.to_numeric(measurements['ReceivedSvTimeUncertaintyNanos'])
    
    # A few measurement values are not provided by all phones
    # We'll check for them and initialize them with zeros if missing
    if 'BiasNanos' in measurements.columns:
        measurements['BiasNanos'] = pd.to_numeric(measurements['BiasNanos'])
    else:
        measurements['BiasNanos'] = 0
    if 'TimeOffsetNanos' in measurements.columns:
        measurements['TimeOffsetNanos'] = pd.to_numeric(measurements['TimeOffsetNanos'])
    else:
        measurements['TimeOffsetNanos'] = 0
    return measurements

def calculate_datetime_cols(measurements):
        # calculate gps Time in nanos 
        measurements['GpsTimeNanos'] = measurements['TimeNanos'] - (measurements['FullBiasNanos'] - measurements['BiasNanos'])
        gpsepoch = datetime(1980, 1, 6, 0, 0, 0)
        measurements['UnixTime'] = pd.to_datetime(measurements['GpsTimeNanos'], utc = True, origin=gpsepoch)
        measurements['Epoch'] = 0
        measurements.loc[measurements['UnixTime'] - measurements['UnixTime'].shift() > timedelta(milliseconds=200), 'Epoch'] = 1
        measurements['Epoch'] = measurements['Epoch'].cumsum()
        # This should account for rollovers since it uses a week number specific to each measurement
        measurements['gnss_receive_time_nanoseconds'] = measurements['TimeNanos'] + measurements['TimeOffsetNanos'] - (measurements['FullBiasNanos'].iloc[0] + measurements['BiasNanos'].iloc[0])
        measurements['GpsWeekNumber'] = np.floor(1e-9 * measurements['gnss_receive_time_nanoseconds'] / WEEKSEC)
        measurements['time_since_reference'] = 1e-9*measurements['gnss_receive_time_nanoseconds'] - WEEKSEC * measurements['GpsWeekNumber']
        measurements['transmit_time_seconds'] = 1e-9*(measurements['ReceivedSvTimeNanos'] + measurements['TimeOffsetNanos'])
        # Calculate pseudorange in seconds
        measurements['pseudorange_seconds'] = measurements['time_since_reference'] - measurements['transmit_time_seconds']
        return measurements

def clause2():
    # Get path to sample file in data directory, which is located in the parent directory of this notebook
    if len(sys.argv) > 1:
        input_filepath = sys.argv[1]
    else:
        exit("should give log file")

    measurements, android_fixes = log_to_measurment(input_filepath)

    format_satelite_ID(measurements)
    # Remove all non-GPS measurements
    measurements = measurements.loc[measurements['Constellation'] == 'G']

    # Convert columns to numeric representation
    measurements = handle_numeric_cols(measurements)

    measurements = calculate_datetime_cols(measurements)    

    # calculate Pseudorange in meters
    measurements['Pseudorange_Measurement'] = LIGHTSPEED * measurements['pseudorange_seconds'] # simple time * speed

    
    # Initialize variables
    epoch = 0
    num_sats = 0
    sv_positions = pd.DataFrame()
    # Iterate over each epoch
    while True:
        # Filter measurements for the current epoch and pseudorange condition
        one_epoch = measurements.loc[(measurements['Epoch'] == epoch) & (measurements['pseudorange_seconds'] < 0.1)].drop_duplicates(subset='satPRN')
        # Check if there are 5 or more satellites in the current epoch
        num_sats = len(one_epoch)
        if num_sats >= 5:
            # Perform operations for the current epoch
            timestamp = one_epoch.iloc[0]['UnixTime'].to_pydatetime(warn=False)
            one_epoch.set_index('satPRN', inplace=True)
            sats = one_epoch.index.unique().tolist()
            ephemeris = manager.get_ephemeris(timestamp, sats)
            sv_position = calculate_satellite_position(ephemeris, one_epoch['transmit_time_seconds'], one_epoch)
            
            # Concatenate satellite positions for the current epoch
            sv_positions = pd.concat([sv_positions, sv_position])

        # Move to the next epoch
        epoch += 1
        
        # Exit loop if there are no more epochs
        if epoch >= measurements['Epoch'].max():
            break
    sv_positions.drop(columns=['Sat.bias']).to_csv('first_output.csv')
    return measurements, sv_positions

def clause3(measurements,sv_position):
    initial_bias = 0
    initial_position = np.array([0, 0, 0])
    # Satellite Initial Position (X, Y, Z)
    satellite_initial_position = sv_position[['Sat.X', 'Sat.Y', 'Sat.Z']].to_numpy()
    current_position = initial_position
    current_bias = initial_bias
    ecef_list = []
    ecef_list_with_times = []
    for epoch in measurements['Epoch'].unique():
        epoch_measurements = measurements.loc[(measurements['Epoch'] == epoch) & (measurements['pseudorange_seconds'] < 0.1)] 
        epoch_measurements = epoch_measurements.drop_duplicates(subset='satPRN').set_index('satPRN')
        if len(epoch_measurements.index) > 4:
            timestamp = epoch_measurements.iloc[0]['UnixTime'].to_pydatetime(warn=False)
            satellite_ids = epoch_measurements.index.unique().tolist()
            ephemeris_data = manager.get_ephemeris(timestamp, satellite_ids)
            satellite_positions = calculate_satellite_position(ephemeris_data, epoch_measurements['transmit_time_seconds'], measurements)
            satellite_positions_xyz = satellite_positions[['Sat.X', 'Sat.Y', 'Sat.Z']].to_numpy()
            pseudoranges = epoch_measurements['Pseudorange_Measurement'] + LIGHTSPEED * satellite_positions['Sat.bias']
            pseudoranges = pseudoranges.to_numpy()

            current_position, current_bias, delta_position = least_squares(satellite_positions_xyz, pseudoranges, current_position, current_bias)
            ecef_list.append(current_position)
            ecef_list_with_times.append((current_position,satellite_positions['GPS time'].min()))

    return ecef_list_with_times

def main():
    measurements,sv_position = clause2()
    ecef_list_with_times = clause3(measurements,sv_position)
    ################################
    # Clause 4
    ################################
    lla = [navpy.ecef2lla(coord) for (coord,time) in ecef_list_with_times]    
    
    ################################
    # Clause 5
    ################################
    create_kml_file(lla)
    locations_df = calculate_locations_data_frame(ecef_list_with_times)
    
    firstOutputDf = pd.read_csv('first_output.csv')
    
    final_df = pd.merge(firstOutputDf, locations_df, on="GPS time")
    final_df.to_csv('final.csv',index=None)
    

    

if __name__ == "__main__":
    main()