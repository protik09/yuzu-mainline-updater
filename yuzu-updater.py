#!/usr/bin/env python3

"""
Update Yuzu mainline in place.

@author Protik Banerji <protik09@gmail.com>

"""

import os
import re
import shutil
import sys
import urllib.request
from distutils.dir_util import copy_tree
from zipfile import ZipFile

from tqdm import tqdm

# Global variables that don't need to be
YUZU_URL = "https://github.com/yuzu-emu/yuzu-mainline/releases"
YUZU_URL_REGEX = r"/download/mainline.*/yuzu-windows-msvc-.*\.zip"
ZIP_FILE = "yuzu_latest.zip"
MBFACTOR = float(1 << 20)  # Number of bytes in a megabyte
# folder_name = "yuzu-windows-msvc" # Used only during debugging


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_file(url, no_chunk=1):
    """
    Download the file with a nice Progress Bar

    @url Full URL to remote file
    @no_chunk Number of chunks to download the file in

    """
    # Start the download
    try:
        # Delete the previous file, if available
        try:
            os.remove(ZIP_FILE)
        except Exception as e:
            print(e)
            print("\n\n")
        with DownloadProgressBar(unit='MB', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:
            urllib.request.urlretrieve(
                url, filename=ZIP_FILE, reporthook=t.update_to)
    except Exception as e:
        print(e)
        print("\nCan't download from Github.\n")
        sys.exit(-1)
        
    # open(ZIP_FILE, 'wb').write(r.content)

    return


# Main part of the program
if __name__ == "__main__":
    # Request the releases page from Github
    request_url = urllib.request.urlopen(YUZU_URL, timeout=1)
    releases_page_raw = request_url.read().decode()
    y = re.findall(YUZU_URL_REGEX, releases_page_raw)

    # The y[1] is used as the first y[0] will contain the executable with debug symbols enabled
    yuzu_latest_release_url = YUZU_URL + y[1]

    # Download the latest Github mainline release
    download_file(yuzu_latest_release_url)

    # Unzip to current folder
    with ZipFile(ZIP_FILE, 'r') as zip_ref:
        folder_name = zip_ref.namelist()[1].split("/")[0] # Get the folder name inside the zip file
        # Delete previous folder if it exists
        try:
            shutil.rmtree(folder_name)
        except Exception:
            pass
        zip_ref.extractall()

    # Copy everything over
    copy_tree(folder_name, os.getcwd())

    # Delete previous folder if it exists
    try:
        shutil.rmtree(folder_name)
        test = os.listdir(os.getcwd())
        # Delete the source xz file
        for item in test:
            if item.endswith(".xz"):
                os.remove(os.path.join(os.getcwd(), item))
    except Exception:
        pass
