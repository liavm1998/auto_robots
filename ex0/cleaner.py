import os

def clean_files():
    files_to_delete = ['first_output.csv', 'final.csv', 'coordinates.kml']
    for file_name in files_to_delete:
        try:
            os.remove(file_name)
            print(f"{file_name} deleted successfully.")
        except FileNotFoundError:
            print(f"{file_name} not found.")

if __name__ == "__main__":
    clean_files()
