#!/usr/bin/env python3

import sys

import math
import yaml
import operator

import argparse
from os import path
from os.path import expanduser

from collections import namedtuple

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

# YAML Format description
YAML_PERSON_ROOT = 'persons'
YAML_PERSON_PORTRAIT_FILE = 'portrait_file'

# Portrait gallery dimensions
BATCH_WIDTH_IMAGES = 4
BATCH_HEIGHT_IMAGES = 3
PORTRAIT_WIDTH_PIXEL = 150
PORTRAIT_HEIGHT_PIXEL = 200
BATCH_MARGIN_X_PIXEL = 10
BATCH_MARGIN_Y_PIXEL = 15
PORTRAIT_DESC_HEIGHT_PIXEL = 50


# see http://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_datafile(filename):
    with open(filename, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError:
            return None


def put_portrait(img_canvas, person, position):
    # calculate top left image corner coords in px
    pos_px = position[0] * (PORTRAIT_WIDTH_PIXEL + BATCH_MARGIN_X_PIXEL) + BATCH_MARGIN_X_PIXEL,\
             position[1] * (PORTRAIT_HEIGHT_PIXEL + BATCH_MARGIN_Y_PIXEL + PORTRAIT_DESC_HEIGHT_PIXEL)\
             + BATCH_MARGIN_Y_PIXEL
    # TODO crop image to maintain aspect ratio
    portrait_resized = person['image'].resize((PORTRAIT_WIDTH_PIXEL, PORTRAIT_HEIGHT_PIXEL), Image.ANTIALIAS)
    img_canvas.paste(portrait_resized, pos_px)

    # calculate desc block top left corner coords in px
    desc_pos_px = pos_px[0], pos_px[1] + PORTRAIT_HEIGHT_PIXEL

    img_desc = Image.new('RGB', (PORTRAIT_WIDTH_PIXEL, PORTRAIT_DESC_HEIGHT_PIXEL), color=(200, 200, 200))
    draw = ImageDraw.Draw(img_desc)
    # use truetype font
    font = ImageFont.truetype("LiberationSans-Regular.ttf", 12)
    draw.text((5, 5), "{} {}".format(person["given_names"], person["family_name"]), (0, 0, 0), font=font)
    draw.text((5, 30), person["date_of_entry"], (0, 0, 0), font=font)

    img_canvas.paste(img_desc, desc_pos_px)


def create_batch(persons, batch_filename, default_portrait_file):
    # do not allow empty list
    assert persons

    for person in persons:
        try:
            person['image'] = Image.open(person[YAML_PERSON_PORTRAIT_FILE], 'r')
        except IOError:
            good = False
            if default_portrait_file:
                try:
                    person['image'] = Image.open(default_portrait_file, 'r')
                    good = True
                except IOError:
                    pass

            if not good:
                eprint("Could not open image file for {}, {}: {}".format(person['family_name'],
                                                                         person['given_names'],
                                                                         person[YAML_PERSON_PORTRAIT_FILE]))
                eprint("Aborting batch!")
                return False

    # calculate portrait batch size in pixel
    width_px = BATCH_WIDTH_IMAGES * (PORTRAIT_WIDTH_PIXEL + BATCH_MARGIN_X_PIXEL) + BATCH_MARGIN_X_PIXEL
    height_px = BATCH_HEIGHT_IMAGES * (PORTRAIT_HEIGHT_PIXEL + BATCH_MARGIN_Y_PIXEL + PORTRAIT_DESC_HEIGHT_PIXEL) \
                + BATCH_MARGIN_Y_PIXEL

    # create empty new image of appropriate format
    img_canvas = Image.new('RGB', (width_px, height_px), color=(255, 255, 255))

    #  O -- X --->
    #  |
    #  Y
    #  |
    x_coord = 0
    y_coord = 0
    for person in persons:
        put_portrait(img_canvas, person, (x_coord, y_coord))

        x_coord += 1
        if x_coord == BATCH_WIDTH_IMAGES:
            y_coord += 1
            x_coord = 0

    # write batch image
    img_canvas.save(batch_filename)
    return True


def create_portrait_gallery(data_dict, default_portrait_file):
    if YAML_PERSON_ROOT not in data_dict:
        return False

    sorted_persons = sorted(data_dict[YAML_PERSON_ROOT],
                            key=operator.itemgetter('sorting'))

    batch_size = BATCH_HEIGHT_IMAGES * BATCH_WIDTH_IMAGES
    batch_no = 0
    num_batches = len(sorted_persons) // batch_size
    if len(sorted_persons) % batch_size > 0:
        num_batches += 1
    assert num_batches > 0
    num_digits = math.ceil(math.log(num_batches + 1, 10))

    processed = 0
    while processed < len(sorted_persons):
        if not create_batch(sorted_persons[processed:processed+batch_size],
                            "/tmp/portrait_batch_{}.bmp".format(str(batch_no).zfill(num_digits)), default_portrait_file):
            return False
        processed += batch_size
        batch_no += 1

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
        parser.error("The data file %s is invalid." % expanded)
    else:
        return expanded


def main():
    parser = argparse.ArgumentParser(description="Create a portrait gallery.")
    parser.add_argument('--portrait-path', dest="path", required=True, metavar="PATH",
                        type=lambda x: is_valid_folder(parser, x), help="Portrait location")
    parser.add_argument('--data-file', dest="datafile", required=True, metavar="FILE",
                        type=lambda x: is_valid_file(parser, x), help="Definition file location")
    parser.add_argument('--default-portrait', dest="default_portrait", metavar="FILE",
                        help="Use this image if specified image could not be found instead of raising an error.")

    args = parser.parse_args()

    # check default portrait
    def_portrait_file = None
    if args.default_portrait:
        def_portrait_file = path.join(args.path, args.default_portrait)
        if not path.isfile(def_portrait_file):
            eprint("Default portrait {} not available. Aborting.".format(def_portrait_file))
            return -1

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
        eprint("YAML Parsing error!")
        return -1

    if not create_portrait_gallery(data_dict, def_portrait_file):
        eprint("Aborting on error")
        return -1
    else:
        print("Success")
        return 0


if __name__ == "__main__":
    main()
