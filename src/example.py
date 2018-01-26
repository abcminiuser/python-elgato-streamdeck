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


def get_random_key_colour_image(deck):
    key_image_format = deck.key_image_format()

    width, height = (key_image_format['width'], key_image_format['height'])
    depth = key_image_format['depth']

    random_color = [int(random.random() * 0xFF) for b in range(depth)]
    for i in range(width * height):
        for b in range(depth):
            yield random_color[b]


def key_change_callback(deck, key, state):
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    if state:
        deck.set_key_image(key, get_random_key_colour_image(deck))

        if key == d.key_count() - 1:
            deck.reset()
            deck.close()


if __name__ == "__main__":
    manager = StreamDeck.DeviceManager()
    decks = manager.enumerate()

    print("Found {} Stream Decks.".format(len(decks)), flush=True)

    for d in decks:
        d.open()
        d.reset()

        print("Press key {} to exit.".format(d.key_count() - 1), flush=True)

        d.set_brightness(30)

        for k in range(d.key_count()):
            d.set_key_image(k, get_random_key_colour_image(d))

        current_key_states = d.key_states()
        print("Initial key states: {}".format(current_key_states))

        d.set_key_callback(key_change_callback)

        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            t.join()
