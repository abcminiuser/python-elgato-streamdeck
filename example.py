#!/usr/bin/env python

#         Python Strem Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from StreamDeck.StreamDeck import DeviceManager


def get_random_key_colour_image(deck):
    import random

    key_image_format = deck.key_image_format()

    key_image_byte_count = key_image_format['width'] * \
        key_image_format['height'] * key_image_format['depth']

    key_image_buffer = bytearray(key_image_byte_count)

    rand_colour_bgr = [int(random.random() * 255) for i in range(0, 3)]
    for i in range(0, len(key_image_buffer)):
        key_image_buffer[i] = rand_colour_bgr[i % 3]

    return key_image_buffer


def key_change_callback(deck, key, state):
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    if state:
        deck.set_key_image(key, get_random_key_colour_image(deck))


manager = DeviceManager()
decks = manager.enumerate()

print("Found {} Stream Decks.".format(len(decks)))

for d in decks:
    d.open()

    d.set_brightness(30)

    for k in range(0, d.key_count()):
        d.set_key_image(k, get_random_key_colour_image(d))

    current_key_states = d.key_states()
    print("Initial key states: {}".format(current_key_states))

    d.set_key_callback(key_change_callback)
