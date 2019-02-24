#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import threading
import os
from inspect import getsourcefile
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from PIL import Image, ImageDraw, ImageFont


# returns absolute path to this module
# allows to load files relative to module instead of relative to current working directory
# i.e. module does not need to be placed in current working directory
def ospath_to_module():
    return os.path.dirname(getsourcefile(lambda: 0))

# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(deck, icon_filename, label_text):
    # Create new key image of the correct dimensions, black background
    image = PILHelper.create_image(deck)

    # Add image overlay, rescaling the image asset if it is too large to fit the
    # requested dimensions via a high quality Lanczos scaling algorithm
    icon = Image.open(icon_filename).convert("RGBA")
    icon.thumbnail((image.width, image.height - 20), Image.LANCZOS)
    image.paste(icon, (0, 0), icon)

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # number onto the image
    font = ImageFont.truetype(os.path.join(ospath_to_module(),"Assets", "Roboto-Regular.ttf"), 14)
    draw = ImageDraw.Draw(image)
    draw.text((10, image.height - 20), text=label_text, font=font, fill=(255, 255, 255, 128))

    return PILHelper.to_native_format(deck, image)


# Returns styling information for a key based on its position and state.
def get_key_style(deck, key, state):
    # Last button in the example application is the exit button
    exit_key_index = deck.key_count() - 1

    if key == exit_key_index:
        name = "exit"
        icon = os.path.join(ospath_to_module(), "Assets", "{}.png".format("Exit"))
        text = "Bye" if state else "Exit"
    else:
        name = "emoji"
        icon = os.path.join(ospath_to_module(), "Assets", "{}.png".format("Pressed" if state else "Released"))
        text = "Pressed!" if state else "Key {}".format(key)

    return {"name": name, "icon": icon, "label": text}


# Creates a new key image based on the key index, style and current key state
# and updates the image on the StreamDeck.
def update_key_image(deck, key, state):
    # Determine what icon and label to use on the generated key
    style = get_key_style(deck, key, state)

    # Generate the custom key with the requested image and label
    image = render_key_image(deck, style["icon"], style["label"])

    # Update requested key with the generated image
    deck.set_key_image(key, image)


# Prints key state change information, updates rhe key image and performs any
# associated actions when a key is pressed.
def key_change_callback(deck, key, state):
    # Print new key state
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    # Update the key image based on the new key state
    update_key_image(deck, key, state)

    # Check if the key is changing to the pressed state
    if state:
        key_style_name = get_key_style(deck, key, state)["name"]

        # When an exit button is pressed, close the application
        if key_style_name == "exit" and state:
            # Reset deck, clearing all button images
            deck.reset()

            # Close deck handle, terminating internal worker threads
            deck.close()


# Prints diagnostic information about a given StrewmDeck
def print_deck_info(deck):
    image_format = deck.key_image_format()

    flip_description = {
        (False, False): "not mirrored",
        (True, False): "mirrored horizontally",
        (False, True): "mirrored vertically",
        (True, True): "mirrored horizontally/vertically",
    }

    print("Deck {} - {}.".format(index, deck.deck_type()), flush=True)
    print("\t - ID: {}".format(deck.id()), flush=True)
    print("\t - Key Count: {}".format(deck.key_count()), flush=True)
    print("\t - Key Image Format: {}x{} pixels, {} order, rotated {} degrees, {}".format(
        image_format['width'], image_format['height'],
        image_format['order'],
        image_format['rotation'],
        flip_description[image_format['flip']]), flush=True)


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)), flush=True)

    for index, deck in enumerate(streamdecks):
        print_deck_info(deck)

        deck.open()
        deck.reset()
        deck.set_brightness(30)

        # Set initial key images
        for key in range(deck.key_count()):
            update_key_image(deck, key, False)

        # Register callback function for when a key state changes
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed)
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
