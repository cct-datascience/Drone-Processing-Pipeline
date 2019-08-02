#!/usr/bin/env python

"""Generates the extractor_info.json file from the configuration file
"""
import copy
import json
import re
import configuration

# The extractor information template to use
BASE_CONFIG = \
    {
        "@context": "http://clowder.ncsa.illinois.edu/contexts/extractors.jsonld",
        "name": None,
        "version": None,
        "description": None,
        "author": None,
        "contributors": [],
        "contexts": [],
        "repository": {
            "repType": "git",
            "repUrl": None
        },
        "process": {
            "dataset": [
                "file.added"
            ]
        },
        "external_services": [],
        "dependencies": [],
        "bibtex": []
    }

# The template file name for Dockerfile
DOCKERFILE_TEMPLATE_FILE_NAME = "Dockerfile.template"

def generate_info():
    """Generates the extractor_info.json file to the current folder
    """
    missing = []
    if not configuration.EXTRACTOR_NAME:
        missing.append("Extractor name")
    if not configuration.VERSION:
        missing.append("Extractor version")
    if not configuration.DESCRIPTION:
        missing.append("Extractor description")
    if not configuration.AUTHOR_NAME:
        missing.append("Author name")
    if not configuration.AUTHOR_EMAIL:
        missing.append("Author email")
    if not configuration.REPOSITORY:
        missing.append("Repository")
    if missing:
        raise RuntimeError("One or more configuration fields aren't defined in configuration.py: " \
                           + ", ".join(missing))

    # We make a deep copy so we can manipulate the dict without messing up the master
    config = copy.deepcopy(BASE_CONFIG)
    config['name'] = configuration.EXTRACTOR_NAME
    config['version'] = configuration.VERSION
    config['description'] = configuration.DESCRIPTION
    config['author'] = "%s <%s>" % (configuration.AUTHOR_NAME, configuration.AUTHOR_EMAIL)
    if 'repository' in config:
        config['repository']['repUrl'] = configuration.REPOSITORY

    with open("extractor_info.json", "w") as out_file:
        json.dump(config, out_file, indent=4)
        out_file.write("\n")

def generate_dockerfile():
    """Genertes a Dockerfile file using the configured information
    """
    missing = []
    if not configuration.EXTRACTOR_NAME:
        missing.append("Extractor name")
    if not configuration.AUTHOR_NAME:
        missing.append("Author name")
    if not configuration.AUTHOR_EMAIL:
        missing.append("Author email")
    if missing:
        raise RuntimeError("One or more configuration fields aren't defined in configuration.py: " \
                           + ", ".join(missing))

    new_name = configuration.EXTRACTOR_NAME.strip().replace(' ', '_').replace('\t', '_').\
                                            replace('\n', '_').replace('\r', '_')
    extractor_name = new_name.lower()

    template = [line.rstrip('\n') for line in open(DOCKERFILE_TEMPLATE_FILE_NAME, "r")]
    with open("Dockerfile", "w") as out_file:
        for line in template:
            if line.startswith("MAINTAINER"):
                out_file.write("MAINTAINER {0} <{1}>\n".format(configuration.AUTHOR_NAME, \
                               configuration.AUTHOR_EMAIL))
            elif line.lstrip().startswith("RABBITMQ_QUEUE"):
                white_space = re.match(r"\s*", line).group()
                out_file.write("{0}RABBITMQ_QUEUE=\"terra.dronepipeline.{1}\" \\\n". \
                         format(white_space, extractor_name))
            else:
                out_file.write("{0}\n".format(line))

# Make the call to generate the file
if __name__ == "__main__":
    generate_info()
    generate_dockerfile()
