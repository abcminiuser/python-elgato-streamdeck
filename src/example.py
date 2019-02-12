#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import StreamDeck.StreamDeck as StreamDeck
import threading
from PIL import Image, ImageDraw, ImageFont


# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(width, height, rgb_order, icon_filename, label_text, flip, rotation):
    # Create new key image of the correct dimensions, black background
    image = Image.new("RGB", (width, height), 'black')

    # Add image overlay, rescaling the image asset if it is too large to fit the
    # requested dimensions via a high quality Lanczos scaling algorithm
    icon = Image.open(icon_filename).convert("RGBA")
    icon.thumbnail((width, height - 20), Image.LANCZOS)
    image.paste(icon, (0, 0), icon)

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # number onto the image
    font = ImageFont.truetype("Assets/Roboto-Regular.ttf", 14)
    draw = ImageDraw.Draw(image)
    draw.text((10, height - 20), text=label_text, font=font, fill=(255, 255, 255, 128))

    # StreamDeck Mini sends images in a different orientation than the original.
    image = image.rotate(rotation)

    # Get the raw r, g and b components of the generated image
    if flip:
        # Flip image horizontally to match the format the (original) StreamDeck expects
        r, g, b = image.transpose(Image.FLIP_LEFT_RIGHT).split()
    else:
        r, g, b = image.split()

    # Recombine the B, G and R elements in the order the display expects them,
    # and convert the resulting image to a sequence of bytes
    rgb = {"R": r, "G": g, "B": b}
    return Image.merge("RGB", (rgb[rgb_order[0]], rgb[rgb_order[1]], rgb[rgb_order[2]])).tobytes()


# Returns styling information for a key based on its position and state.
def get_key_style(deck, key, state):
    # Last button in the example application is the exit button
    exit_key_index = deck.key_count() - 1

    if key == exit_key_index:
        name = "exit"
        icon = "Assets/{}.png".format("Exit" if state else "Exit") # Dummy condition for alt state
        text = "Bye" if state else "Exit"
    else:
        name = "emoji"
        icon = "Assets/{}.png".format("Pressed" if state else "Released")
        text = "Pressed!" if state else "Key {}".format(key)

    return {"name": name, "icon": icon, "label": text}


# Creates a new key image based on the key index, style and current key state
# and updates the image on the StreamDeck.
def update_key_image(deck, key, state):
    # Get the required key image dimensions
    image_format = deck.key_image_format()
    width = image_format['width']
    height = image_format['height']
    rgb_order = image_format['order']
    flip = image_format['flip']
    rotation = image_format['rotation']

    # Determine what icon and label to use on the generated key
    style = get_key_style(deck, key, state)

    # Generate the custom key with the requested image and label
    image = render_key_image(width, height, rgb_order, style["icon"], style["label"], flip, rotation)

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


if __name__ == "__main__":
    manager = StreamDeck.DeviceManager()
    streamdecks, minidecks = manager.enumerate()

    print("Found {} Original Stream Deck(s) and {} Stream Deck Mini(s).\n".format(len(streamdecks), len(minidecks)), flush=True)

    decks = streamdecks + minidecks

    deck_count = 0

    for deck in decks:
        deck.open()
        deck.reset()

        deck.set_brightness(30)

        # Diagnostic output
        print("Deck at index {} has ID {}.\nIt is a {} with {} keys.".format(deck_count, deck.id(), deck.deck_type(), deck.key_count()), flush=True)
        print("Acceptable image upload format for this device is {}x{} pixels with a depth of {}, in {} order.".format(deck.key_image_format()['width'], deck.key_image_format()['height'], deck.key_image_format()['depth'], deck.key_image_format()['order']))
        rotating = ", but will rotate them by {} degrees".format(deck.key_image_format()['rotation']) if deck.key_image_format()['rotation']!=0 else ""
        flipverb = "will" if deck.key_image_format()['flip'] else "will not"
        print("Device expects that software {} flip the images before uploading{}.\n".format(flipverb, rotating))

        # Set initial key images
        for key in range(deck.key_count()):
            update_key_image(deck, key, False)

        # Register callback function for when a key state changes
        deck.set_key_callback(key_change_callback)

        deck_count += 1

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed)
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
