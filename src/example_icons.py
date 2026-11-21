#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import StreamDeck.StreamDeck as StreamDeck
import threading
import random
import sys
import os
import random
from PIL import Image
# only required for SVG
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

def get_random_icon():
    key = random.choice(list(icons.keys()))
    return key, icons[key]

def key_change_callback(deck, key, state):
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    if key == d.key_count() - 1:
            deck.reset()
            deck.close()
            return

    if state:
        icon_name, icon = get_random_icon()
        print("Key: {}".format(icon_name))
        deck.set_key_image(key, icon)

def image_to_bgr_bytes(rgb_image):
    r, g, b = rgb_image.transpose(Image.FLIP_LEFT_RIGHT).split()
    return Image.merge("RGB", (b, g, r)).tobytes()

def force_size(rgb_image):
    if max(rgb_image.size) > 72:
        rgb_image.thumbnail((72,72), Image.ANTIALIAS)
    if rgb_image.size != (72, 72):
        wrong_size = rgb_image
        img_w, img_h = wrong_size.size
        rgb_image = Image.new('RGB', (72, 72), color = 'black')
        offset = ((72 - img_w) // 2, (72 - img_h) // 2)
        rgb_image.paste(wrong_size, offset)
    return rgb_image

def load_icons(path = "./icons"):
    '''
        Supports images PIL can open.

        There is also rudimentary SVG support, but i.e. gradients often
        fail. SVG support was tested using https://github.com/icons8/flat-color-icons,
        that gave quite good results.
    '''
    path = os.path.abspath(path)
    icons = {}

    for entry in os.scandir(path):
        if entry.is_file():
            rgb_image = None
            if entry.path.endswith(".svg") or entry.path.endswith(".svgz"):
                drawing = svg2rlg(entry.path)
                rgb_image = renderPM.drawToPIL(drawing,dpi=72, bg=0x000000)
            else:
                rgb_image = Image.open(entry.path)
            rgb_image = force_size(rgb_image)
            icons[entry.name] = image_to_bgr_bytes(rgb_image)
            rgb_image.close()
    return icons

if __name__ == "__main__":

    icons = load_icons("./icons")

    manager = StreamDeck.DeviceManager()
    decks = manager.enumerate()

    print("Found {} Stream Decks.".format(len(decks)), flush=True)

    for d in decks:
        d.open()
        d.reset()

        print("Press key {} to exit.".format(d.key_count() - 1), flush=True)

        d.set_brightness(30)

        for k in range(d.key_count()):
            d.set_key_image(k, get_random_icon()[1])

        current_key_states = d.key_states()
        print("Initial key states: {}".format(current_key_states))

        d.set_key_callback(key_change_callback)

        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            t.join()
