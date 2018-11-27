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


# Custom tiles with run-time generated text and custom image via the PIL module
def get_key_image(deck, key, state):
    # Get the required key image dimensions
    image_format = deck.key_image_format()
    width = image_format['width']
    height = image_format['height']
    order = image_format['order']

    # Create new key image of the correct dimensions, black background
    image = Image.new("RGB", (width, height), 'black')

    # Add image overlay, rescaling the image asset if it is too large to fit the
    # requested dimensions via a high quality Lanczos scaling algorithm
    icon = Image.open("Assets/{}.png".format("Pressed" if state else "Released")).convert("RGBA")
    icon.thumbnail((width, height - 20), Image.LANCZOS)
    image.paste(icon, (0, 0), icon)

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # number onto the image
    font = ImageFont.truetype("Assets/Roboto-Regular.ttf", 14)
    draw = ImageDraw.Draw(image)
    draw.text((10, height - 20), text="Key {}".format(key), font=font, fill=(255, 255, 255, 128))

    # Get the raw r, g and b components of the generated image (note we need to
    # flip it horizontally to match the format the StreamDeck expects)
    r, g, b = image.transpose(Image.FLIP_LEFT_RIGHT).split()

    # Recombine the B, G and R elements in the order the display expects them,
    # and convert the resulting image to a sequence of bytes
    rgb = { "R": r, "G": g, "B": b }
    return Image.merge("RGB", (rgb[order[0]], rgb[order[1]], rgb[order[2]])).tobytes()


def key_change_callback(deck, key, state):
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    deck.set_key_image(key, get_key_image(deck, key, state))

    if key == deck.key_count() - 1:
        deck.reset()
        deck.close()


if __name__ == "__main__":
    manager = StreamDeck.DeviceManager()
    decks = manager.enumerate()

    print("Found {} Stream Decks.".format(len(decks)), flush=True)

    for deck in decks:
        deck.open()
        deck.reset()

        print("Press key {} to exit.".format(deck.key_count() - 1), flush=True)

        deck.set_brightness(30)

        for key in range(deck.key_count()):
            deck.set_key_image(key, get_key_image(deck, key, False))

        deck.set_key_callback(key_change_callback)

        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
