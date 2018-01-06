#!/usr/bin/env python

#         Python Strem Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from StreamDeck.StreamDeck import DeviceManager

manager = DeviceManager()
decks = manager.enumerate()

print("Found {} Stream Decks.".format(len(decks)))

for d in decks:
    d.open()

    d.set_brightness(30)

    key_image_format = d.key_image_format()

    key_image_byte_count = key_image_format['width'] * \
        key_image_format['height'] * key_image_format['depth']

    key_image_buffer = bytearray(key_image_byte_count)

    import random
    colour_shift = int(random.random() * 255) % 3

    for k in range(0, d.key_count()):
        rand_colour_bgr = [int(random.random() * 255) for i in range(0, 3)]
        for i in range(0, len(key_image_buffer)):
            key_image_buffer[i] = rand_colour_bgr[i % 3]

        d.set_key_image(k, key_image_buffer)
