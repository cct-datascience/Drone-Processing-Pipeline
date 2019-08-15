#!/usr/bin/env python

"""Test script for extractor code
"""

import os
import sys
import numpy as np
import gdal

import extractor

def print_usage():
    """Displays information on how to use this script
    """
    argc = len(sys.argv)
    if argc:
        our_name = os.path.basename(sys.argv[0])
    else:
        our_name = os.path.basename(__file__)
    print(our_name + " <folder>|<filename> ...")
    print("    folder:   path to folder containing images to process")
    print("    filename: path to an image file to process")
    print("")
    print("  One or more folders and/or filenames can be used")
    print("  Only files at the top level of a folder are processed")

def check_arguments():
    """Checks that we have script argument parameters that appear valid
    """
    argc = len(sys.argv)
    if argc < 2:
        sys.stderr.write("One or more paths to images need to be specified on the command line\n")
        print_usage()
        return False

    # Check that the paths exist.
    have_errors = False
    for idx in range(1, argc):
        if not os.path.exists(sys.argv[idx]):
            print("The following path doesn't exist: " + sys.argv[idx])
            have_errors = True

    if have_errors:
        sys.stderr.write("Please correct any problems and try again\n")

    return not have_errors

def run_test(filename):
    """Runs the extractor code using pixels from the file
    Args:
        filename(str): Path to image file
    Returns:
        The result of calling the extractor's calculate() method
    Notes:
        Assumes the path passed in is valid. An error is reported if
        the file is not an image file.
    """
    try:
        of = gdal.Open(filename)
        if of:
            pix = np.array(of.ReadAsArray())
            cc_val = extractor.calculate(np.rollaxis(pix, 0, 3))
            print(filename + "," + str(cc_val))
    except Exception as ex:
        sys.stderr.write("Exception caught: " + str(ex) + "\n")
        sys.stderr.write("    File: " + filename + "\n")

def process_files():
    """Processes the command line file/folder arguments
    """
    argc = len(sys.argv)
    for idx in range(1, argc):
        cur_path = sys.argv[idx]
        if not os.path.isdir(cur_path):
            run_test(cur_path)
        else:
            allfiles = [os.path.join(cur_path, fn) for fn in os.listdir(cur_path) \
                                            if os.path.isfile(os.path.join(cur_path, fn))]
            for one_file in allfiles:
                run_test(one_file)

if __name__ == "__main__":
    if check_arguments():
        process_files()
