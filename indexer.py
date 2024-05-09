import os


def parse_files(directory_path):
    # subdir - current directory being visited
    # dirs - subdirectories in the current subdir
    # files - list of files in current subdir
    for subdir, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(subdir, file)

            print(f"current file path: ", file_path)


if __name__ == '__main__':
    directory_path = "DEV"
    parse_files(directory_path)