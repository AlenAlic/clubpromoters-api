from os import listdir
from os.path import isfile, join


def get_files(folder):
    return [f for f in listdir(folder) if isfile(join(folder, f))]
