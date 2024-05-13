import sys
import unittest
import os
import pandas as pd
import numpy as np
import simplekml

from gnss_parser import clause2, clause3, calculate_satellite_position, least_squares

class TestGNSS(unittest.TestCase):

    def setUp(self):
        self.parent_directory = os.path.split(os.getcwd())[0]
        self.input_filepath = os.path.join(self.parent_directory, 'gnss_log_2024_04_13_19_51_17.csv', 'first_output.csv')

    def test_compare_kml_files(self):
        # Load the first KML file
        file1 = "coordinates.kml"
        kml1 = simplekml.Kml()
        with open(file1, 'r') as f:
            kml1 = f.read()

        # Load the second KML file
        #file2 = sys.argv[1]
        file2 = "gnss_log_2024_04_13_19_51_17.kml"
        kml2 = simplekml.Kml()
        with open(file2, 'r') as f:
            kml2 = f.read()

        # Compare the KML data from both files
        self.assertEqual(kml1, kml2)

    def test_compare_csv_files(self):
        # Load the first CSV file
        #file1 = sys.argv[1]
        file1 = "gnss_log_2024_04_13_19_51_17.csv"
        #file1 = sys.argv[2]
        df1 = pd.read_csv(file1)

        # Load the second CSV file
        file2 = "first_output.csv"
        df2 = pd.read_csv(file2)

        # Check if both DataFrames have the same columns
        self.assertListEqual(list(df1.columns), list(df2.columns))

        # Check if both DataFrames have the same values
        self.assertTrue(df1.equals(df2))
    def test_clause2(self):
        input_filepath = "gnss_log_2024_04_13_19_51_17.txt"
        measurements, sv_position = clause2()


        # Check if measurements and sv_position are pandas DataFrames
        self.assertIsInstance(measurements, pd.DataFrame)
        self.assertIsInstance(sv_position, pd.DataFrame)

        # Check if sv_position has the correct columns
        expected_columns = ['GPS time', 'Sat.bias', 'Sat.X', 'Sat.Y', 'Sat.Z', 'pseudorange', 'cn0']
        self.assertListEqual(list(sv_position.columns), expected_columns)

    # def test_clause3(self):
    #     measurements = pd.DataFrame({
    #         'Epoch': [0, 0, 1, 1, 2, 2],
    #         'satPRN': ['G01', 'G02', 'G01', 'G02', 'G03', 'G04'],
    #         'Pseudorange_Measurement': [100, 200, 150, 250, 180, 220],
    #         'transmit_time_seconds': [0.1, 0.1, 0.2, 0.2, 0.3, 0.3]
    #     })
    #     sv_position = pd.DataFrame({
    #         'Sat.X': [1000, 2000, 1500, 2500, 1800, 2200],
    #         'Sat.Y': [1000, 2000, 1500, 2500, 1800, 2200],
    #         'Sat.Z': [1000, 2000, 1500, 2500, 1800, 2200],
    #         'Sat.bias': [0, 0, 0, 0, 0, 0]
    #     })
    #
    #     ecef_list = clause3(measurements, sv_position)
    #
    #     # Check if ecef_list has correct length and type
    #     self.assertIsInstance(ecef_list, list)
    #     self.assertEqual(len(ecef_list), 3)  # Example number of epochs


    def test_least_squares(self):
        receiver_positions = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]])
        measured_pseudorange = np.array([0, 1, 2, 3])
        initial_receiver_position = np.array([0, 0, 0])
        initial_clock_bias = 0

        final_position, final_clock_bias, _ = least_squares(receiver_positions, measured_pseudorange, initial_receiver_position, initial_clock_bias)

        # Check if final position and clock bias are numpy arrays
        self.assertIsInstance(final_position, np.ndarray)
        self.assertIsInstance(final_clock_bias, float)

    def test_calculate_satellite_position(self):
        # Mock data for testing
        ephemeris_data = {
            't_oe': [1],
            'sqrtA': [1],
            'deltaN': [0],
            'M_0': [0],
            'e': [0.1],
            'omega': [0],
            'C_us': [0],
            'C_rs': [0],
            'C_is': [0],
            'Omega_0': [0],
            'IDOT': [0],
            't_oc': [0],
            'SVclockBias': [0],
            'SVclockDrift': [0],
            'SVclockDriftRate': [0],
            'constellation': ['G'],
            'C_uc': [0]  # Existing column
        }

        # Convert mock data to DataFrame
        ephemeris = pd.DataFrame(ephemeris_data)

        # Ensure 'C_ic' column is not present in the DataFrame
        self.assertNotIn('C_ic', ephemeris.columns)

        # Define transmit_time with some appropriate value
        transmit_time = pd.Series([0.1])

        # Mock one_epoch DataFrame
        one_epoch = pd.DataFrame({
            'Pseudorange_Measurement': [0],
            'Cn0DbHz': [30]
        })

        # Assert that calling the function raises a KeyError when 'C_ic' column is missing
        with self.assertRaises(KeyError):
            calculate_satellite_position(ephemeris, transmit_time, one_epoch)


if __name__ == '__main__':
    unittest.main()
