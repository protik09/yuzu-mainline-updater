#!/usr/bin/env python3

"""
Update Yuzu mainline in-situ.

@author Protik Banerji <protik09@gmail.com>

"""
import os
import re
import argparse
import shutil
import signal
import subprocess
import sys
import psutil
import urllib.request
from distutils.dir_util import copy_tree
from zipfile import ZipFile

import tkinter as tk
from tkinter import messagebox as mb
from tkinter import filedialog as fd
from tkinter import simpledialog as sd
from tkinter import ttk
from tqdm import tqdm


# Global variables that don't need to be
YUZU_URL = "https://github.com/yuzu-emu/yuzu-mainline/releases"
YUZU_URL_REGEX = r"/download/mainline.*/yuzu-windows-msvc-.*\.zip"
ZIP_FILE = "yuzu_latest.zip"
if os.name.startswith("nt"):
    YUZU_CMD = "yuzu-cmd.exe"
elif os.name.startswith("posix"):
    YUZU_CMD = "yuzu-cmd"
else:
    print("This cannot be run in a Java VM.")
    sys.exit(-1)

# folder_name = "yuzu-windows-msvc" # Used only during debugging

# GUI Stuff
def GetBackground():
    return 'white'


def GetButtonBackground():
    return 'white'


def GetTextColour():
    return 'black'


def GetButtonTextColour():
    return '#c51a4a'

def RunGUI(sdkpath, args):
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('default')

    ttk.Style().configure("TButton", padding=6, relief="groove", border=2,
                          foreground=GetButtonTextColour(), background=GetButtonBackground())
    ttk.Style().configure("TLabel", foreground=GetTextColour(), background=GetBackground())
    ttk.Style().configure("TCheckbutton",
                          foreground=GetTextColour(), background=GetBackground())
    ttk.Style().configure("TRadiobutton",
                          foreground=GetTextColour(), background=GetBackground())
    ttk.Style().configure("TLabelframe", foreground=GetTextColour(),
                          background=GetBackground())
    ttk.Style().configure("TLabelframe.Label",
                          foreground=GetTextColour(), background=GetBackground())
    ttk.Style().configure("TCombobox", foreground=GetTextColour(), background=GetBackground())
    ttk.Style().configure("TListbox", foreground=GetTextColour(), background=GetBackground())

    app = ProjectWindow(root, sdkpath, args)

    app.configure(background=GetBackground())

    root.mainloop()
    sys.exit(0)

def RunWarning(message):
    mb.showwarning('Yuzu Updater', message)
    sys.exit(0)

# Download stuff
class DownloadProgressBar(tqdm):
    def UpdateTo(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def DownloadFile(url, no_chunk=1):
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
                url, filename=ZIP_FILE, reporthook=t.UpdateTo)
    except Exception as e:
        print(e)
        print("\nCan't download from Github.\n")
        sys.exit(-1)

    # open(ZIP_FILE, 'wb').write(r.content)

    return

#Check if yuzu.exe is running
def ProcessRunning(processName):
    """
    Check if there is any running process that contains the given name processName.
    """
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(e)
            sys.exit(-1)
    return False

def KillProcessTree(processName):
    """
    Kill the process containing the string processName
    """
    #Iterate over the all the running process
    ospid = os.getpid()
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                pid = proc.pid()
                print("Proc")
                print("ProcID - {pid}, OSPID - {ospid}")
                # Try not to suicide process
                if proc.pid() == int(os.getpid()):
                    raise RuntimeError(f"Refuse to suicide current process - {proc.name()}")
                else:
                    # Kill the process
                    parent = psutil.Process(proc.pid())
                    children = parent.children(recursive=True)
                    children.append(parent)
                    for p in children:
                        p.send_signal(signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(e)
            sys.exit(-1)
    return False


# Main part of the program
if __name__ == "__main__":

    processName = "yuzu"
    choice = True
    # Check the current version of yuzu installed
    print("Checking current installed version of Yuzu")
    # subprocess.Popen([YUZU_CMD, '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # First check if Yuzu is running
    if ProcessRunning(processName):
        # Ask if you wanna close it
        try:
            user_input = input("Do you wanna kill the running Yuzu process?(y/n) : ")
            if (user_input == "y") or (user_input == "Y"):
                pass
            else:
                choice = True
        except Exception as e:
            pass
    else:
        pass
    if choice == True:
        KillProcessTree(processName)
    else:
        print("Yuzu is running please kill it manually.")
        sys.exit(-1)



    # Request the releases page from Github
    request_url = urllib.request.urlopen(YUZU_URL, timeout=1)
    releases_page_raw = request_url.read().decode()
    y = re.findall(YUZU_URL_REGEX, releases_page_raw)

    # The y[1] is used as the first y[0] will contain the executable with debug symbols enabled
    yuzu_latest_release_url = YUZU_URL + y[1]

    # Download the latest Github mainline release
    DownloadFile(yuzu_latest_release_url)

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
