#!/usr/bin/env python3

import yaml
import operator
import argparse
from collections import namedtuple

from PIL import Image


# YAML Format description
YAML_PERSON_ROOT = 'persons'

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
            person['image'] = Image.open(person['portrait_file'], 'r')
        except IOError:
            print("Could not open image file for", person['family_name'], ",", person['given_names'])
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


def main():
    try:
        data_dict = parse_datafile("data.yaml")
    except FileNotFoundError:
        print("YAML File not found!")
        return

    if not data_dict:
        print("YAML Parsing error!")
    else:
        if not create_portrait_gallery(data_dict):
            print("Aborting on error")
        else:
            print("Success")


if __name__ == "__main__":
    main()
