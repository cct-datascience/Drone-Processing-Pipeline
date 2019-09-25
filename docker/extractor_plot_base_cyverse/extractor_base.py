#!/usr/bin/env python

'''Extractor template for plot-level algorithms
'''

import os
import logging
import math
import random
import time
import json
import datetime
import sys
import requests
import numpy as np

from osgeo import ogr

import osr
import gdal

from terrautils.imagefile import image_get_geobounds, get_epsg
from terrautils.betydb import get_bety_key, get_bety_api

from extractor import calculate
import configuration

# The filename extensions of supported image types; must include leading period '.'
KNOWN_IMAGE_EXTENSIONS = ['.tif', '.tiif', '.jpg', ]

# The name of the extractor to use
EXTRACTOR_NAME = None

# Calculated sensor name is derived from specified extractor name
SENSOR_NAME = None

# Number of tries to open a CSV file before we give up
MAX_CSV_FILE_OPEN_TRIES = 10

# Maximum number of seconds a single wait for file open can take
MAX_FILE_OPEN_SLEEP_SEC = 30

# Array of trait names that should have array values associated with them
TRAIT_NAME_ARRAY_VALUE = ['site']

# Mapping of default trait names to fixecd values
TRAIT_NAME_MAP = {
    'access_level': '2',
    'species': 'Unknown',
    'citation_author': 'Unknown',
    'citation_year': 'Unknown',
    'citation_title': 'Unknown',
    'method': ''
}

# Used to generate random numbers
RANDOM_GENERATOR = None

# Variable field names
FIELD_NAME_LIST = None

def init_extraction(name, method_name):
    """Initializes the extractor environment
    Args:
       name(str): The name of the extractor
       method_name(str): Optional name of the scientific method to reference
    Return:
        N/A
    Exceptions:
        RuntimeError is raised if a missing or invalid name is passed in
    """
    # We need to add other sensor types for OpenDroneMap generated files before anything happens
    # The Sensor() class initialization defaults the sensor dictionary and we can't override
    # without many code changes
    # pylint: disable=global-statement
    global EXTRACTOR_NAME
    global SENSOR_NAME
    global TRAIT_NAME_ARRAY_VALUE
    global FIELD_NAME_LIST

    if not name:
        raise RuntimeError("Invalid name parameter passed to init_extraction")

    EXTRACTOR_NAME = name

    new_name = name.strip().replace(' ', '_').replace('\t', '_').replace('\n', '_').\
                           replace('\r', '_')
    SENSOR_NAME = new_name.lower()

    TRAIT_NAME_ARRAY_VALUE[0] = SENSOR_NAME

    # Set up the values for the trait name map
    TRAIT_NAME_MAP['citation_author'] = configuration.CITATION_AUTHOR
    TRAIT_NAME_MAP['citation_title'] = configuration.CITATION_TITLE
    TRAIT_NAME_MAP['citation_year'] = configuration.CITATION_YEAR
    if method_name:
        TRAIT_NAME_MAP['method_name'] = method_name

    # Get the field names into a list format
    if ',' in configuration.VARIABLE_NAMES:
        FIELD_NAME_LIST = configuration.VARIABLE_NAMES.split(',')
    else:
        FIELD_NAME_LIST = [configuration.VARIABLE_NAMES]

def __find_json_and_image_files(paths):
    """Finds and returns a list of images files contained in paths passed in. If folders
       are specified, they are also searched
    Args:
        paths (list): list of paths to process
    Return:
        Returns a tuple of found image files, found metadata (JSON) files, and files that
        are not accessible (inaccessible image and JSON files)
    """
    image_paths = []
    metadata_paths = []
    unavailable_files = []

    num_paths = len(paths) if paths else 0
    for idx in range(0, num_paths):
        one_path = paths[idx]
        if one_path.endswith('.json'):
            if os.path.exists(one_path):
                metadata_paths.append(one_path)
            else:
                unavailable_files.append(one_path)
        else:
            ext = os.path.splitext(one_path)[1]
            if ext and ext in KNOWN_IMAGE_EXTENSIONS:
                if os.path.exists(one_path):
                    image_paths.append(one_path)
                else:
                    unavailable_files.append(one_path)
            elif os.path.isdir(one_path):
                files = [os.path.join(one_path, one_name) for one_name in os.listdir(one_path)]
                new_images, new_metadata, new_missing = __find_json_and_image_files(files)
                image_paths.extend(new_images)
                metadata_paths.extend(new_metadata)
                unavailable_files.extend(new_missing)

    return (image_paths, metadata_paths, unavailable_files)

def __do_initialization(argv):
    """ Function to kick off initialization of this module by another script.
    Args:
        argv (list): list of command line arguments to refer to
    Return:
        Returns a tuple containing the germplasm name, experiment name, a list of found images, and a
        list of metadata files, in that order
    Exceptions:
        RuntimeError is raised if a configuration parameter is missing; also raised if init_extraction
        function detects an error
    """
    # Get the germplasm name
    argv_len = len(argv)
    if argv_len < 6:
        raise RuntimeError("A germplasm name, experiment name, timestamp, plot name, and an image file " +
                           "or folder must be specified")

    arg_germplasm_name = argv[1]
    arg_experiment_name = argv[2]
    arg_timestamp = argv[3]
    arg_plotname = argv[4]

    # Find expected files
    image_paths, metadata_paths, unavailable_files = __find_json_and_image_files(argv[5:])

    # Report any issues with the specified files
    if unavailable_files:
        logging.warning('Unable to access the following files: %s', '\n    '.join(unavailable_files))
    del unavailable_files

    if not image_paths:
        raise RuntimeError("Image files must be specified")

    # Perform other setup
    if hasattr(configuration, "METHOD_NAME"):
        method_name = getattr(configuration, "METHOD_NAME")
    else:
        method_name = None

    init_extraction(configuration.EXTRACTOR_NAME, method_name)

    return (arg_germplasm_name, arg_experiment_name, arg_timestamp, arg_plotname, image_paths, metadata_paths)

def __str_to_path(target):
    """Fixes a string to make it compatible with paths. Converts spaces, colons, semi-colons, periods,
       commas, forward and backward slashes ('/' and '\\'), single and double quotes (" and '), parenthesis,
       curly braces ('{' and '}') to underscores
    Args:
        target (str): the string to convert
    Return:
        Returns the converted string
    Exceptions:
        RuntimeError is raised if the target parameter is not a string
    """
    if not isinstance(target, str):
        raise RuntimeError("Invalid parameter type specified when coverting a string to be path-compatible")

    return_str = target
    for match in " :;.,/\\\'\"(){}":
        return_str = return_str.replace(match, '_')
    return return_str

def _get_plot_name(name):
    """Looks in the parameter and returns a plot name.

       Expects the plot name to be identified by having "By Plot" embedded in the name.
       The plot name is then surrounded by " - " characters. That valus is then returned.
    Args:
        name(iterable or string): An array/list of names or a single name string
    Return:
        Returns the found plot name or an empty string.
    """
    if isinstance(name, str):
        name = [name]

    plot_signature = "by plot"
    plot_separator = " - "
    # Loop through looking for a plot identifier (case insensitive)
    for one_name in name:
        low_name = one_name.lower()
        if plot_signature in low_name:
            parts = low_name.split(plot_separator)
            parts_len = len(parts)
            if parts_len > 1:
                start_pos = len(parts[0]) + len(plot_separator)
                end_pos = start_pos + len(parts[1])
                return one_name[start_pos:end_pos]

    return ""

def _get_open_backoff(prev=None):
    """Returns the number of seconds to backoff from opening a file
    Args:
        prev(int or float): the previous return value from this function
    Return:
        Returns the number of seconds (including fractional seconds) to wait
    Notes:
        The return value is deterministic, and always the same, when None is passed in
    """
    # pylint: disable=global-statement
    global RANDOM_GENERATOR
    global MAX_FILE_OPEN_SLEEP_SEC

    # Simple case
    if prev is None:
        return 1

    # Get a random number generator
    if RANDOM_GENERATOR is None:
        try:
            RANDOM_GENERATOR = random.SystemRandom()
        finally:
            # Set this so we don't try again
            RANDOM_GENERATOR = 0

    # Get a random number
    if RANDOM_GENERATOR:
        multiplier = RANDOM_GENERATOR.random()  # pylint: disable=no-member
    else:
        multiplier = random.random()

    # Calculate how long to sleep
    sleep = math.trunc(float(prev) * multiplier * 100) / 10.0
    if sleep > MAX_FILE_OPEN_SLEEP_SEC:
        sleep = max(0.1, math.trunc(multiplier * 100) / 10)

    return sleep

def update_betydb(bety_csv_header, bety_rows):
    """Sends the rows of csv data to BETYdb
    Args:
        bety_csv_header(str): comma separated list of column headers
        bety_rows(list): list of strings that are comma separated column data (list of data rows)
    """
    betyurl = get_bety_api('traits')
    request_params = {'key': get_bety_key()}
    filetype = 'csv'
    content_type = 'text/csv'
    data = [bety_csv_header]
    data.extend(bety_rows)

    resp = requests.post("%s.%s" % (betyurl, filetype), params=request_params,
                         data=os.linesep.join(data),
                         headers={'Content-type': content_type})

    if resp.status_code in [200, 201]:
        logging.info("Data successfully submitted to BETYdb.")
        return resp.json()['data']['ids_of_new_traits']
    else:
        logging.error("Error submitting data to BETYdb: %s -- %s", resp.status_code, resp.reason)
        resp.raise_for_status()

    return None

def get_bety_fields():
    """Returns the supported field names as a list
    """
    # pylint: disable=global-statement
    global FIELD_NAME_LIST

    return ('local_datetime', 'access_level', 'species', 'site', 'citation_author', 'citation_year',
            'citation_title', 'method') + tuple(FIELD_NAME_LIST)

def get_geo_fields():
    """Returns the supported field names as a list
    """
    return ('site', 'trait', 'lat', 'lon', 'dp_time', 'source', 'value', 'timestamp')


def get_default_trait(trait_name):
    """Returns the default value for the trait name
    Args:
       trait_name(str): the name of the trait to return the default value for
    Return:
        If the default value for a trait is configured, that value is returned. Otherwise
        an empty string is returned.
    """
    # pylint: disable=global-statement
    global TRAIT_NAME_ARRAY_VALUE
    global TRAIT_NAME_MAP

    if trait_name in TRAIT_NAME_ARRAY_VALUE:
        return []   # Return an empty list when the name matches
    elif trait_name in TRAIT_NAME_MAP:
        return TRAIT_NAME_MAP[trait_name]
    return ""

def get_bety_traits_table():
    """Returns the field names and default trait values
    Returns:
        A tuple containing the list of field names and a dictionary of default field values
    """
    # Compiled traits table
    fields = get_bety_fields()
    traits = {}
    for field_name in fields:
        traits[field_name] = get_default_trait(field_name)

    return (fields, traits)

def get_geo_traits_table():
    """Returns the field names and default trait values
    Returns:
        A tuple containing the list of field names and a dictionary of default field values
    """
    fields = get_geo_fields()
    traits = {}
    for field_name in fields:
        traits[field_name] = ""

    return (fields, traits)

def generate_traits_list(fields, traits):
    """Returns an array of trait values
    Args:
        fields(list): the list of fields to look up and return
        traits(dict): contains the set of trait values to return
    Return:
        Returns an array of trait values taken from the traits parameter
    Notes:
        If a trait isn't found, it's assigned an empty string
    """
    # compose the summary traits
    trait_list = []
    for field_name in fields:
        if field_name in traits:
            trait_list.append(traits[field_name])
        else:
            trait_list.append(get_default_trait(field_name))

    return trait_list

# Look through the file list to find the files we need
def load_image_files(files):
    """Loads image file nboundaries
    Args:
        files(list): the list of file to look through and access
    Returns:
        Returns a dict of georeferenced image files (indexed by filename and containing an
        object with the calculated image bounds as an ogr polygon and a list of the
        bounds as a tuple)

        The bounds are assumed to be rectilinear with the upper-left corner directly
        pulled from the file and the lower-right corner calculated based upon the geometry
        information stored in the file.

        The polygon points start at the upper left corner and proceed clockwise around the
        boundary. The returned polygon is closed: the first and last point are the same.

        The bounds tuple contains the min and max Y point values, followed by the min and
        max X point values.
    """
    imagefiles = {}

    for onefile in files:
        # If the file has a geo shape we store it for clipping
        bounds = image_get_geobounds(onefile)
        epsg = get_epsg(onefile)
        if bounds[0] != np.nan:
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(bounds[2], bounds[1])     # Upper left
            ring.AddPoint(bounds[3], bounds[1])     # Upper right
            ring.AddPoint(bounds[3], bounds[0])     # lower right
            ring.AddPoint(bounds[2], bounds[0])     # lower left
            ring.AddPoint(bounds[2], bounds[1])     # Closing the polygon

            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(ring)

            ref_sys = osr.SpatialReference()
            if epsg:
                if ref_sys.ImportFromEPSG(int(epsg)) != ogr.OGRERR_NONE:
                    raise RuntimeError("Failed to import EPSG " + str(epsg) + " for image file " + onefile)
                else:
                    poly.AssignSpatialReference(ref_sys)
            else:
                raise RuntimeError("File is missing an EPSG code: " + onefile)

            imagefiles[onefile] = {'bounds' : poly}

    # Return what we've found
    return imagefiles

def load_metadata(files):
    """Loads the metadata contained in the files. All the metadata is merged into
       one return dict; files loaded later may overwrite previously loaded metadata
    Args:
        files (list): the list of files containing JSON metadata to load
    Return:
        Returns a dictionary with all the loaded metadata
    """
    new_metadata = {}
    if files:
        try:
            for one_file in files:
                try:
                    with open(one_file, "r") as in_file:
                        file_md = json.load(in_file)
                        if file_md:
                            new_metadata.update(file_md)
                except Exception as ex:
                    logging.warning("Unable to load json from file '%s' due to exception", one_file)
                    logging.warning("    Exception: %s", str(ex))
        except Exception as ex:
            logging.error("An exception was caught loading metadata: %s", str(ex))
            raise RuntimeError("Unable to load metadata due to error logged exception")

    return new_metadata

def write_csv_file(filename, header, data):
    """Attempts to write out the data to the specified file. Will write the
       header information if it's the first call to write to the file.

       If the file is not available, it waits as configured until it becomes
       available, or returns an error.
       Args:
            filename(str): path to the file to write to
            header(str): Optional CSV formatted header to write to the file; can be set to None
            data(str): CSV formatted data to write to the file
        Return:
            Returns True if the file was written to and False otherwise
    """
    # pylint: disable=global-statement
    global MAX_CSV_FILE_OPEN_TRIES

    if not filename or not data:
        raise RuntimeError("Empty parameter passed to write_geo_csv")

    csv_file = None
    backoff_secs = None
    for tries in range(0, MAX_CSV_FILE_OPEN_TRIES):
        try:
            csv_file = open(filename, 'a+')
        except Exception as ex:
            pass

        if csv_file:
            break

        # If we can't open the file, back off and try again (unless it's our last try)
        if tries < MAX_CSV_FILE_OPEN_TRIES - 1:
            backoff_secs = _get_open_backoff(backoff_secs)
            logging.info("Sleeping for %s seconds before trying to open CSV file again", str(backoff_secs))
            time.sleep(backoff_secs)

    if not csv_file:
        logging.error("Unable to open CSV file for writing: '%s'", filename)
        return False

    wrote_file = False
    try:
        # Check if we need to write a header
        if os.fstat(csv_file.fileno()).st_size <= 0:
            if header:
                csv_file.write(header + "\n")

        # Write out data
        csv_file.write(data + "\n")

        wrote_file = True
    except Exception as ex:
        logging.error("Exception while writing CSV file: '%s'", filename)
        logging.error("    %s", str(ex))
    finally:
        csv_file.close()

    # Return whether or not we wrote to the file
    return wrote_file

# Entry point for processing files
# pylint: disable=too-many-locals,too-many-nested-blocks,too-many-branches,too-many-statements
def process_files(germplasm_name, experiment_name, timestamp, plot_name, images_list, metadata_list):
    """Performs plot level image extraction

    Args:
        germplasm_name (str): The name of the germplasm associated with the images
        experiment_name (str): The name of the experiment
        timestamp (str): An ISO 8601 long format timestamp
        plot_name (str): The name of the plot being processed
        images_list (list): A list of paths to the image files to process
        metadata_list (list): A list of paths to the metadata files to use
    """
    # pylint: disable=global-statement
    global SENSOR_NAME
    global FIELD_NAME_LIST

    # Initialize local variables
    out_csv = None

    # Intialize data writing overrides. We have some reverse logic here due to the intent of
    # the variables
    store_in_betydb = True if not hasattr(configuration, "NEVER_WRITE_BETYDB") \
                                        else not getattr(configuration, "NEVER_WRITE_BETYDB")
    create_csv_files = True if not hasattr(configuration, "NEVER_WRITE_CSV") \
                                        else not getattr(configuration, "NEVER_WRITE_CSV")

    # Find the files we're interested in
    loaded_files = load_image_files(images_list)
    num_loaded_files = len(loaded_files)
    if num_loaded_files <= 0:
        logging.info("No image files with geographic boundaries found")
        return

    # Load the metadata
    metadata = load_metadata(metadata_list)

    # Get the best timestamp
    if not 'T' in timestamp:
        timestamp += 'T12:00:00'
    if timestamp.find('T') > 0 and timestamp.rfind('-') > 0 and timestamp.find('T') < timestamp.rfind('-'):
        # Convert to local time. We can do this due to site definitions having
        # the time offsets as part of their definition
        localtime = timestamp[0:timestamp.rfind('-')]
    else:
        localtime = timestamp

    (bety_fields, bety_traits) = get_bety_traits_table()

    try:
        # Setup default trait values
        bety_traits['species'] = germplasm_name

        bety_csv_header = ','.join(map(str, bety_fields))

        # Loop through all the images (of which there should be one)
        bety_rows = []
        len_field_value = len(FIELD_NAME_LIST)
        for filename in loaded_files:

            try:
                calc_value = ""

                # Load the pixels
                clip_pix = np.array(gdal.Open(filename).ReadAsArray())
                calc_value = calculate(np.rollaxis(clip_pix, 0, 3))

                # Convert to something iterable that's in the correct order
                if isinstance(calc_value, set):
                    raise RuntimeError("A 'set' type of data was returned and isn't supported. " \
                                       "Please use a list or a tuple instead")
                elif isinstance(calc_value, dict):
                    # Assume the dictionary is going to have field names with their values
                    # We check whether we have the correct number of fields later. This also
                    # filters out extra fields
                    values = []
                    for key in FIELD_NAME_LIST:
                        if key in calc_value:
                            values.append(calc_value[key])
                elif not isinstance(calc_value, (list, tuple)):
                    values = [calc_value]

                # Sanity check our values
                len_calc_value = len(values)
                if not len_calc_value == len_field_value:
                    raise RuntimeError("Incorrect number of values returned. Expected " + str(len_field_value) +
                                       " and received " + str(len_calc_value))

                # Write the data points geographically and otherwise
                for idx in range(0, len_field_value):
                    # BETYdb can handle wide rows with multiple values so we just set the field
                    # values here and write the single row after the loop
                    bety_traits[FIELD_NAME_LIST[idx]] = str(values[idx])

                bety_traits['site'] = plot_name
                bety_traits['local_datetime'] = localtime
                trait_list = generate_traits_list(bety_fields, bety_traits)
                csv_data = ','.join(map(str, trait_list))
                if create_csv_files or store_in_betydb:
                    bety_rows.append(csv_data)

            except Exception as ex:
                logging.error("Error generating %s for %s", EXTRACTOR_NAME, plot_name)
                logging.error("    exception: %s", str(ex))
                continue

            if create_csv_files:
                out_csv = os.path.join(os.path.dirname(filename),
                                       __str_to_path(experiment_name) + '_' + SENSOR_NAME + '.csv')
                metadata_file = os.path.splitext(out_csv)[0] + '.json'
                logging.info("Writing CSV to %s", out_csv)
                logging.info("Writing metadata to %s", metadata_file)

                for one_row in bety_rows:
                    write_csv_file(out_csv, bety_csv_header, one_row)

                # Update this with the extractor info
                try:
                    # Write the metadata out to a file
                    logging.info("updating metadata")
                    comment = "Calculated " + SENSOR_NAME + " value"
                    if create_csv_files:
                        comment = comment + ", and wrote values to CSV file"
                    if store_in_betydb:
                        comment = comment + ", and wrote values to BETYdb"
                    comment += "."

                    # Arrange the metadata to write
                    content = {
                        SENSOR_NAME: {
                            'comment': comment,
                            'calculated_value': calc_value,
                            'timestamp': datetime.datetime.now().isoformat(),
                            'file': filename
                            }
                        }
                    if metadata:
                        metadata.update(content)
                        content = metadata

                    # Write the metadata
                    with open(metadata_file, 'w') as out_file:
                        out_file.write(json.dumps(content, indent=4))

                except Exception as ex:
                    logging.warning("Exception updating metadata: %s", str(ex))

            # Only process the first file that's valid
            if num_loaded_files > 1:
                logging.info("Multiple image files were found, only using first found")
                break

        # Upload any betydb data
        if store_in_betydb:
            if bety_rows:
                update_betydb(bety_csv_header, bety_rows)
            else:
                logging.info("No BETYdb data was generated to upload")
    finally:
        logging.info("Finished processing")

if __name__ == "__main__":
    # Call our "do the initialization" function
    GERMPLASM, EXPERIMENT, CONFIG_TIMESTAMP, PLOTNAME, IMAGE_FILES, METADATA_FILES = __do_initialization(sys.argv)

    process_files(GERMPLASM, EXPERIMENT, CONFIG_TIMESTAMP, PLOTNAME, IMAGE_FILES, METADATA_FILES)
