import unittest
from unittest.mock import patch
import pandas as pd
import numpy as np
import warnings
warnings.simplefilter(action='ignore', category=Warning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
warnings.filterwarnings(action='ignore')
from gnss_parser import *




class TestCalculateSatellitePosition(unittest.TestCase):

    def setUp(self):
        # Sample ephemeris data for testing
        self.ephemeris = pd.DataFrame({
            't_oe': [0, 1, 2],
            'sqrtA': [1, 2, 3],
            'deltaN': [0.1, 0.2, 0.3],
            'M_0': [0.4, 0.5, 0.6],
            'e': [0.7, 0.8, 0.9],
            'SVclockBias': [1.0, 2.0, 3.0],
            'SVclockDrift': [0.1, 0.2, 0.3],
            'SVclockDriftRate': [0.01, 0.02, 0.03],
            'C_us': [0.001, 0.002, 0.003],
            'C_uc': [0.0001, 0.0002, 0.0003],
            'C_rs': [0.00001, 0.00002, 0.00003],
            'C_rc': [0.000001, 0.000002, 0.000003],
            'C_is': [0.0000001, 0.0000002, 0.0000003],
            'C_ic': [0.00000001, 0.00000002, 0.00000003],
            'i_0': [0.1, 0.2, 0.3],
            'IDOT': [0.01, 0.02, 0.03],
            'Omega_0': [0.4, 0.5, 0.6],
            'OmegaDot': [0.04, 0.05, 0.06],
            'omega': [0.07, 0.08, 0.09],
            't_oc': [10, 20, 30]  # Add t_oc column
        })
        # Sample one_epoch data for testing
        self.one_epoch = pd.DataFrame({
            'Pseudorange_Measurement': [10, 20, 30],
            'Cn0DbHz': [40, 50, 60]
        })
        # Sample transmit time
        self.transmit_time = 10

    def test_compute_satellite_positions(self):
        # Call the function
        result = calculate_satellite_position(self.ephemeris, self.transmit_time, self.one_epoch)

        # Assertions
        # Check if output DataFrame has the expected columns
        self.assertSetEqual(set(result.columns), {'GPS time', 'Sat.bias', 'Sat.X', 'Sat.Y', 'Sat.Z', 'pseudorange', 'cn0'})
        self.assertAlmostEqual(result.loc[0, 'Sat.X'], -0.494, delta=0.01)
        self.assertAlmostEqual(result.loc[0, 'Sat.Y'], -1.3826, delta=0.01)
        self.assertAlmostEqual(result.loc[0, 'Sat.Z'], -0.123, delta=0.01)


    def test_compute_pseudorange(self):
        # Call the function
        result = calculate_satellite_position(self.ephemeris, self.transmit_time, self.one_epoch)

        # Assertions
        # Check for correct computation of pseudorange
        self.assertAlmostEqual(result.loc[0, 'pseudorange'], 299792468.0, delta=200)


    def test_compute_cn0(self):
        # Call the function
        result = calculate_satellite_position(self.ephemeris, self.transmit_time, self.one_epoch)

        # Assertions
        # Check for correct computation of cn0
        self.assertEqual(result.loc[0, 'cn0'], 40)

    def test_invalid_input(self):
        # Test with invalid input (e.g., empty DataFrame)
        with self.assertRaises(KeyError):
            calculate_satellite_position(pd.DataFrame(), self.transmit_time, self.one_epoch)

class TestLeastSquares(unittest.TestCase):
    def test_least_squares_empty_input(self):
        # Test with empty input arrays
        receiver_positions = np.empty((0, 3))
        measured_pseudorange = np.array([])
        initial_receiver_position = np.array([0.1, 0.1, 0.1])
        initial_clock_bias = 1.0

        with self.assertRaises(ValueError):
            least_squares(receiver_positions, measured_pseudorange, initial_receiver_position, initial_clock_bias)

    def test_least_squares_dimension_mismatch(self):
        # Test with inputs of different dimensions
        receiver_positions = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])
        measured_pseudorange = np.array([1, 2])
        initial_receiver_position = np.array([0.1, 0.1, 0.1])
        initial_clock_bias = 1.0

        with self.assertRaises(ValueError):
            least_squares(receiver_positions, measured_pseudorange, initial_receiver_position, initial_clock_bias)

    def test_least_squares_non_singular_matrix(self):
        # Test with inputs containing extreme values
        receiver_positions = np.array([[1e10, 1e10, 1e10], [-1e10, -1e10, -1e10]])
        measured_pseudorange = np.array([1e10, 2e10])
        initial_receiver_position = np.array([1e9, -1e9, 1e9])
        initial_clock_bias = 1e9
        with self.assertRaises(np.linalg.LinAlgError):
            least_squares(receiver_positions, measured_pseudorange, initial_receiver_position, initial_clock_bias)

    def test_least_squares_extreme_values(self):
        # Test with inputs containing extreme values
        receiver_positions = np.array([[25023639.6240527,4783845.80416969,8137692.35013354],
                                      [-1620081.7744787,17327678.89277763 ,20172485.06377191],
                                      [15757452.40831777,1890975.95716349,21856363.72227612],
                                      [23098436.98302593,13303367.38708996,-3014966.4406808 ],
                                      [7810468.74605613,17849813.84424023,18350828.84000951]])
        measured_pseudorange = np.array([21196005.87649137,22839528.10111702,21704707.75126088,22215117.68794983,21298089.88169067])
        initial_receiver_position = np.array([0,0,0])
        initial_clock_bias = 0

        result_position, result_clock_bias, result_norm_delta_pseudorange = least_squares(
            receiver_positions, measured_pseudorange, initial_receiver_position, initial_clock_bias)
        self.assertAlmostEqual(result_norm_delta_pseudorange, 1673.956, delta=0.001)
        self.assertAlmostEqual(result_clock_bias, 590.656, delta=0.001)
        self.assertAlmostEqual(result_position[0], 4438536.937, delta=0.001)
        self.assertAlmostEqual(result_position[1], 3085403.903, delta=0.001)
        self.assertAlmostEqual(result_position[2], 3376938.435, delta=0.001)


class TestParseInputFilePipeline(unittest.TestCase):

    
    def setUp(self):
        # Create a temporary test input file
        self.valid_input_file = "testData/example_log.txt"

    def no_diff_between_dataFrames(self,df1,df2): 
        if 'Unnamed: 0' in df2.columns:
            df2 = df2.drop(columns=['Unnamed: 0'])

        
        # Check if columns are equal
        self.assertSetEqual(set(df1.columns), set(df2.columns))
        self.assertCountEqual(df1.index, df2.index)

        # Convert string data to numeric types where possible
        df1_numeric = df1.apply(pd.to_numeric, errors='coerce')
        df2_numeric = df2.apply(pd.to_numeric, errors='coerce')

        # Fill missing values with NaN
        df1_numeric = df1_numeric.fillna(0)
        df2_numeric = df2_numeric.fillna(0)

        tolerance = 1e+6  # Adjust the tolerance based on your requirements
        # Compare numeric columns using np.isclose()
        numeric_comparison = np.isclose(df1_numeric, df2_numeric, rtol=tolerance, atol=tolerance)
        self.assertTrue(numeric_comparison.all().all())

        # Handle non-numeric columns by checking equality
        # Identify non-numeric columns
        non_numeric_columns = set(df1.columns) - set(df1_numeric.columns)

        # Compare non-numeric columns by checking string equality
        non_numeric_comparison = all(
            (df1[col] == df2[col]).all() for col in non_numeric_columns
        )
        self.assertTrue(non_numeric_comparison)

    def test_log_to_measurment(self):
        # Test with a valid input file
        measurements, android_fixes = log_to_measurment(self.valid_input_file)
        # Check if the returned DataFrames are not None

        self.assertIsNotNone(measurements)
        self.assertIsNotNone(android_fixes)
        expected_android_fixes = pd.read_csv('testData/expected_android_fixes.csv')
        expected_measurements = pd.read_csv('testData/expected_measurements.csv')

        
        self.no_diff_between_dataFrames(measurements,expected_measurements)
        self.no_diff_between_dataFrames(android_fixes,expected_android_fixes)

    @patch('sys.argv', ['test_gnss_parser.py', 'testData/example_log.txt'])
    def test_clause2(self):
        measurements,sv_position = clause2()
        # Check if measurements and sv_position are pandas DataFrames
        self.assertIsInstance(measurements, pd.DataFrame)
        self.assertIsInstance(sv_position, pd.DataFrame)

        # Check if sv_position has the correct columns
        expected_columns = ['GPS time', 'Sat.bias', 'Sat.X', 'Sat.Y', 'Sat.Z', 'pseudorange', 'cn0']
        self.assertListEqual(list(sv_position.columns), expected_columns)

    
    @patch('sys.argv', ['test_gnss_parser.py', 'testData/example_log.txt'])
    def test_clause3(self):
        measurements ,sv_position = clause2()
        measurements =  measurements.head(50)    
        sv_position = sv_position.head(50)
        ecef_list = clause3(measurements, sv_position)
        
        excpected_ecef_list = [(pd.array([4436894.2780066 , 3085290.16479374, 3376331.62495113]), 3139.3385134040145),
                               (pd.array([4436885.83366258, 3085286.08353279, 3376328.15229751]), 3140.3385149930837),
                               (pd.array([4436888.10135707, 3085286.08342632, 3376328.11202359]), 3141.3385165710934), 
                               (pd.array([4436905.01334421, 3085290.20758007, 3376337.88831127]), 3142.3385181290796)]
        # Check if ecef_list has correct length and type
        self.assertEqual(len(ecef_list), 4)  
        self.assertListEqual(excpected_ecef_list, ecef_list) 
    
    @classmethod
    def tearDownClass(cls):
        os.remove('first_output.csv')
        return super().tearDownClass()

     




