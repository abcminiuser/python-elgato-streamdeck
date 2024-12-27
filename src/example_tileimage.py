#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script showing how to tile a larger image across multiple buttons, by
# first generating an image suitable for the entire deck, then cropping out and
# applying key-sized tiles to individual keys of a StreamDeck.

import os
import threading

from PIL import Image, ImageOps
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")


# Generates an image that is correctly sized to fit across all keys of a given
# StreamDeck.
def create_full_deck_sized_image(deck, key_spacing, image_filename):
    key_rows, key_cols = deck.key_layout()
    key_width, key_height = deck.key_image_format()['size']
    spacing_x, spacing_y = key_spacing

    # Compute total size of the full StreamDeck image, based on the number of
    # buttons along each axis. This doesn't take into account the spaces between
    # the buttons that are hidden by the bezel.
    key_width *= key_cols
    key_height *= key_rows

    # Compute the total number of extra non-visible pixels that are obscured by
    # the bezel of the StreamDeck.
    spacing_x *= key_cols - 1
    spacing_y *= key_rows - 1

    # Compute final full deck image size, based on the number of buttons and
    # obscured pixels.
    full_deck_image_size = (key_width + spacing_x, key_height + spacing_y)

    # Resize the image to suit the StreamDeck's full image size. We use the
    # helper function in Pillow's ImageOps module so that the image's aspect
    # ratio is preserved.
    image = Image.open(os.path.join(ASSETS_PATH, image_filename)).convert("RGBA")
    image = ImageOps.fit(image, full_deck_image_size, Image.LANCZOS)
    return image


# Crops out a key-sized image from a larger deck-sized image, at the location
# occupied by the given key index.
def crop_key_image_from_deck_sized_image(deck, image, key_spacing, key):
    key_rows, key_cols = deck.key_layout()
    key_width, key_height = deck.key_image_format()['size']
    spacing_x, spacing_y = key_spacing

    # Determine which row and column the requested key is located on.
    row = key // key_cols
    col = key % key_cols

    # Compute the starting X and Y offsets into the full size image that the
    # requested key should display.
    start_x = col * (key_width + spacing_x)
    start_y = row * (key_height + spacing_y)

    # Compute the region of the larger deck image that is occupied by the given
    # key, and crop out that segment of the full image.
    region = (start_x, start_y, start_x + key_width, start_y + key_height)
    segment = image.crop(region)

    # Create a new key-sized image, and paste in the cropped section of the
    # larger image.
    key_image = PILHelper.create_key_image(deck)
    key_image.paste(segment)

    return PILHelper.to_native_key_format(deck, key_image)


# Closes the StreamDeck device on key state change.
def key_change_callback(deck, key, state):
    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        # Reset deck, clearing all button images.
        deck.reset()

        # Close deck handle, terminating internal worker threads.
        deck.close()


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        # This example only works with devices that have screens.
        if not deck.is_visual():
            continue

        deck.open()
        deck.reset()

        print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))

        # Set initial screen brightness to 30%.
        deck.set_brightness(30)

        # Approximate number of (non-visible) pixels between each key, so we can
        # take those into account when cutting up the image to show on the keys.
        key_spacing = (36, 36)

        # Load and resize a source image so that it will fill the given
        # StreamDeck.
        image = create_full_deck_sized_image(deck, key_spacing, "Harold.jpg")

        print("Created full deck image size of {}x{} pixels.".format(image.width, image.height))

        # Extract out the section of the image that is occupied by each key.
        key_images = dict()
        for k in range(deck.key_count()):
            key_images[k] = crop_key_image_from_deck_sized_image(deck, image, key_spacing, k)

        # Use a scoped-with on the deck to ensure we're the only thread
        # using it right now.
        with deck:
            # Draw the individual key images to each of the keys.
            for k in range(deck.key_count()):
                key_image = key_images[k]

                # Show the section of the main image onto the key.
                deck.set_key_image(k, key_image)

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except (TransportError, RuntimeError):
                pass
