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

for d in decks:
    d.open()

    d.set_brightness(30)

    key_image_format = d.key_image_format()
    key_image_buffer = bytearray(key_image_format['width'] * key_image_format['height'] * key_image_format['depth'])

    import random
    colour_shift = int(random.random() * 100) % 3

    for k in range(0, d.key_count()):
        for i in range(0, len(key_image_buffer)):
           key_image_buffer[i] = 255 if i % 3 == ((colour_shift + k) % 3) else 0

        print("Setting key {} image...".format(k))
        d.set_key_image(k, key_image_buffer)

