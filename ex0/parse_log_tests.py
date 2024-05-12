import os
import csv
import unittest

from ex0.gnssutils import parse_log


def compare_csv_files(file1_path, file2_path):
    with open(file1_path, 'r') as file1:
        csv_reader1 = csv.reader(file1)
        data1 = list(csv_reader1)

    with open(file2_path, 'r') as file2:
        csv_reader2 = csv.reader(file2)
        data2 = list(csv_reader2)

    differences = []
    for row_num, (row1, row2) in enumerate(zip(data1, data2), start=1):
        for col_num, (cell1, cell2) in enumerate(zip(row1, row2), start=1):
            if cell1 != cell2:
                differences.append((file1_path, file2_path, row_num, col_num, cell1, cell2))

    return differences



class TestCSVComparison(unittest.TestCase):

    def test_compare_csv_files(self):
        files = ["Accel.csv", "Agc.csv", "Fix.csv", "Gyro.csv", "Mag.csv", "Nav.csv", "NMEA.csv", "OrientationDeg.csv",
                 "Raw.csv", "Status.csv", "Status.csv", "UncalAccel.csv",
                 "UncalGyro.csv", "UncalMag.csv"]
        logs = ["gnss_log_2024_04_13_19_51_17", 'gnss_log_2024_04_13_19_52_00', 'gnss_log_2024_04_13_19_53_33']
        directory1 = "TestsData"
        directory2_base = ""

        for log_folder in logs:
            directory2 = os.path.join(directory2_base, log_folder)
            for filename in files:
                file1_path = os.path.join(directory1, log_folder, filename)
                file2_path = os.path.join(directory2, filename)

                if os.path.isfile(file1_path) and os.path.isfile(file2_path):
                    # Compare files
                    differences = compare_csv_files(file1_path, file2_path)
                    if differences:
                        print(f"Differences found between {log_folder}:")
                        for diff in differences:
                            print("File 1:", diff[0])
                            print("File 2:", diff[1])
                            print("Row number:", diff[2])
                            print("Column number:", diff[3])
                            print("Value in file 1:", diff[4])
                            print("Value in file 2:", diff[5])
                        self.fail(f"Differences found between {log_folder}")


if __name__ == '__main__':

    unittest.main()
