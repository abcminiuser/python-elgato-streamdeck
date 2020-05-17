#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import logging

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    manager = DeviceManager(transport="dummy")
    streamdecks = manager.enumerate()

    logging.info("Got {} Dummy Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        logging.info("Using Deck Type: {}".format(deck.deck_type()))

        with deck:
            deck.open()

            connected = deck.connected()
            deck_id = deck.id()
            key_count = deck.key_count()
            deck_type = deck.deck_type()
            key_layout = deck.key_layout()
            image_format = deck.key_image_format()
            key_states = deck.key_states()

            test_key_image = PILHelper.create_image(deck)
            test_key_image = PILHelper.to_native_format(deck, test_key_image)

            deck.set_key_callback(None)
            deck.reset()
            deck.set_brightness(30)
            deck.set_key_image(0, test_key_image)

            deck.close()
