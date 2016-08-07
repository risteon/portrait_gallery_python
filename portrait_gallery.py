#!/usr/bin/env python3

import yaml
import operator

import argparse
from os import path
from os.path import expanduser

from collections import namedtuple

from PIL import Image


# YAML Format description
YAML_PERSON_ROOT = 'persons'
YAML_PERSON_PORTRAIT_FILE = 'portrait_file'

# Portrait gallery dimension
GALLERY_WIDTH_IMAGES = 5
GALLERY_HEIGHT_IMAGES = 15


def parse_datafile(filename):
    with open(filename, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError:
            return None


def create_batch(persons):
    for person in persons:
        try:
            person['image'] = Image.open(person[YAML_PERSON_PORTRAIT_FILE], 'r')
        except IOError:
            print("Could not open image file for {}, {}: {}".format(person['family_name'],
                                                                    person['given_names'],
                                                                    person[YAML_PERSON_PORTRAIT_FILE]))
            print("Aborting batch!")
            return False

    return True


def create_portrait_gallery(data_dict):
    if YAML_PERSON_ROOT not in data_dict:
        return False

    sorted_persons = sorted(data_dict[YAML_PERSON_ROOT],
                            key=operator.itemgetter('sorting'))

    batch_size = GALLERY_HEIGHT_IMAGES * GALLERY_WIDTH_IMAGES
    processed = 0
    while processed < len(sorted_persons):
        if not create_batch(sorted_persons[processed:processed+batch_size]):
            return False
        processed += batch_size

    return True


def is_valid_folder(parser, arg):
    expanded = expanduser(arg)
    if not path.isdir(expanded):
        parser.error("The portrait path %s is invalid." % expanded)
    else:
        return expanded


def is_valid_file(parser, arg):
    expanded = expanduser(arg)
    if not path.isfile(expanded):
        parser.error("The definition file %s is invalid." % expanded)
    else:
        return expanded


def main():
    parser = argparse.ArgumentParser(description="Create a portrait gallery.")
    parser.add_argument('--portrait-path', dest="path", required=True, metavar="PATH",
                        type=lambda x: is_valid_folder(parser, x), help="Portrait location")
    parser.add_argument('--definition-file', dest="datafile", required=True, metavar="FILE",
                        type=lambda x: is_valid_file(parser, x), help="Definition file location")

    args = parser.parse_args()

    # read datafile
    try:
        data_dict = parse_datafile(args.datafile)
    except FileNotFoundError:
        print("YAML File not found!")
        return

    # set portrait file paths
    for person in data_dict[YAML_PERSON_ROOT]:
        person[YAML_PERSON_PORTRAIT_FILE] = path.join(args.path, person[YAML_PERSON_PORTRAIT_FILE])

    if not data_dict:
        print("YAML Parsing error!")
    else:
        if not create_portrait_gallery(data_dict):
            print("Aborting on error")
        else:
            print("Success")


if __name__ == "__main__":
    main()
