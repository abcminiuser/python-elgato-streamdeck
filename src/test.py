#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import logging
from StreamDeck.DeviceManager import DeviceManager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    manager = DeviceManager(transport="dummy")
    streamdecks = manager.enumerate()

    print("Got {} Dummy Stream Deck(s).\n".format(len(streamdecks)), flush=True)

    for index, deck in enumerate(streamdecks):
        deck.open()

        connected = deck.connected()
        deck_id = deck.id()
        key_count = deck.key_count()
        deck_type = deck.deck_type()
        key_layout = deck.key_layout()
        image_format = deck.key_image_format()
        key_states = deck.key_states()

        deck.set_key_callback(None)
        deck.reset()
        deck.set_brightness(30)
        deck.set_key_image(0, [])

        deck.close()
