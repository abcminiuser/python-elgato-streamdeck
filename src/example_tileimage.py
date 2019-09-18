#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script showing how to tile a larger image across multiple buttons, by
# first generating an image suitable for the entire deck, then cropping out and
# applying key-sized tiles to individual keys of a StreamDeck..

import os
import threading
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper


# Folder location of image assets used by this example
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")


# Generates an image that is correctly sized to fit across all keys of a given
# StreamDeck.
def create_full_deck_sized_image(deck, image_filename):
    key_width, key_height = deck.key_image_format()['size']
    key_rows, key_cols = deck.key_layout()

    full_deck_image_size = (key_width * key_cols, key_height * key_rows)

    # Resize the image to suit the StreamDeck's full image size (note: will not
    # preserve the correct aspect ratio).
    image = Image.open(os.path.join(ASSETS_PATH, image_filename)).convert("RGBA")
    return image.resize(full_deck_image_size, Image.LANCZOS)


# Crops out a key-sized image from a larger deck-sized image, at the location
# occupied by the given key index.
def crop_key_image_from_deck_sized_image(deck, image, key):
    key_width, key_height = deck.key_image_format()['size']
    key_rows, key_cols = deck.key_layout()

    # Determine which row and column the requested key is located on
    row = key // key_cols
    col = key % key_cols

    # Compute the region of the larger deck image that is occupied by the given
    # key.
    region = (col * key_width, row * key_height, (col + 1) * key_width, (row + 1) * key_height)
    segment = image.crop(region)

    # Create a new key-sized image, and paste in the cropped section of the
    # larger image.
    key_image = PILHelper.create_image(deck)
    key_image.paste(segment)

    return PILHelper.to_native_format(deck, key_image)


# Prints key state change information and closes the StreamDeck device.
def key_change_callback(deck, key, state):
    # Print new key state
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    # Reset deck, clearing all button images
    deck.reset()

    # Close deck handle, terminating internal worker threads
    deck.close()


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        deck.open()
        deck.reset()

        print("Opened '{}' device (serial number: '{}')\n".format(deck.deck_type(), deck.get_serial_number()))

        # Set initial screen brightness to 30%
        deck.set_brightness(30)

        # Load and resize a source image so that it will fill the given
        # StreamDeck.
        image = create_full_deck_sized_image(deck, "Harold.jpg")

        for k in range(deck.key_count()):
            # Extract out the section of the image that is occupied by the
            # current key.
            key_image = crop_key_image_from_deck_sized_image(deck, image, k)

            # Show the section of the main image onto the key.
            deck.set_key_image(k, key_image)

        # Register callback function for when a key state changes
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed)
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
