#!/usr/bin/env python3

"""
Update Yuzu mainline in-situ.

@author Protik Banerji <protik09@gmail.com>

"""
import os
import re
import shutil
import signal
import subprocess
import sys
import psutil
import urllib.request
from distutils.dir_util import copy_tree
from zipfile import ZipFile

from tqdm import tqdm

# Global variables that don't need to be
YUZU_URL = "https://github.com/yuzu-emu/yuzu-mainline/releases"
YUZU_VERSION_REMOTE_REGEX = r"yuzu\s\d{3,4}"
ZIP_FILE = "yuzu_latest.zip"
if os.name.startswith("nt"):
    YUZU_CMD = "yuzu-cmd.exe"
    YUZU_URL_REGEX = r"/download/mainline.*/yuzu-windows-msvc-.*\.zip"
    processName = "yuzu.exe"
elif os.name.startswith("posix"):
    YUZU_CMD = "yuzu-cmd"
    YUZU_URL_REGEX = r"/download/mainline.*/yuzu-linux-.*\.tar.xz"
    processName = "yuzu"
else:
    print("This cannot be run in a Java VM.")
    sys.exit(-1)

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
        EndProgram()

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
                print (f"\nProcess {proc.name()} found.")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(e)
            EndProgram()
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
            if processName.lower() == proc.name().lower():
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
            EndProgram()
    return False

def EndProgram(exit_code = -1):
    if (exit_code != 0):
        print(f"\n\nEnd Program with exit code {exit_code}")
    else:
        print(f"\n\nProgram Ended Successfully!!!")

    _ = input("\n\nPlease press any key to exit ......\n\n")
    sys.exit(exit_code)

# Main part of the program
if __name__ == "__main__":

    # Check the current version of yuzu installed
    print("Checking current installed version of Yuzu")
    # The following should technically work according to the documentation, but doesn't, becuase of a bug in the auto-naming scheme in
    # yuzu-cmd.exe not fixed since version 636. Workaround by just writing a yuzu_version text file.
    yuzu_version_file = "yuzu_version.txt"
    if os.path.exists(yuzu_version_file):
        with open(yuzu_version_file) as f:
            yuzu_version_installed = f.readline()
            if yuzu_version_installed.isdigit():
                pass
            else:
                # Delete the empty yuzu version file
                try:
                    test = os.listdir(os.getcwd())
                    # Delete the source file
                    for item in test:
                        if item.endswith(str(yuzu_version_file)):
                            print("Deleting existing empty file")
                            os.remove(os.path.join(os.getcwd(), item))
                except Exception as e:
                    print(e)
                EndProgram(4)
    else:
        yuzu_version_raw = str(subprocess.Popen([YUZU_CMD, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read())
        yuzu_version_installed = re.findall(r'mainline-\d{3,4}-', yuzu_version_raw)[0].split("-")[1]
    print(f"Yuzu verion {yuzu_version_installed} installed.")

    # Request the releases page from Github
    request_url = urllib.request.urlopen(YUZU_URL, timeout=1)
    releases_page_raw = request_url.read().decode()
    # Check the remote yuzu version
    yuzu_version_remote = re.findall(YUZU_VERSION_REMOTE_REGEX, releases_page_raw)[0].split(" ")[1]
    print(f"Yuzu verion {yuzu_version_remote} found online.")


    # Check if versions are the same
    if int(yuzu_version_installed) > int(yuzu_version_remote):
        print("WHHHAATT??? How is your version higher than the remote one? MAGICCCC!!!!")
        EndProgram(666)
    elif int(yuzu_version_installed) == int(yuzu_version_remote):
        print("Your Yuzu install is up to date.")
        EndProgram(0)
    else: # Yuzu installed is lower version than remote yuzu
        # Check if Yuzu is running
        if ProcessRunning(processName):
            print("\nYuzu process is running. Please exit manually before using updater again.")
            EndProgram(2)
            # # Ask if you wanna close it (This requires escalation) TODO
            # try:
            #     user_input = input(
            #         "\nDo you wanna kill the running Yuzu process?(y/n) : ")
            #     if (user_input == "y") or (user_input == "Y"):
            #         # KillProcessTree(processName)
            #         print("\nYuzu process is running. Please exit manually before using updater again.")
            #         EndProgram(2)
            #     else:
            # except Exception as e:
            #     print(e)
            #     EndProgram(3)
        else:
            # Since process is not running just go on to download the stuff
            pass

        # Find the appropriate executable URL
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
        
        # Write the version file for future use
        with open(yuzu_version_file, 'wb') as f:
            f.write(bytes(yuzu_version_remote, encoding='utf8'))
        EndProgram(0)
