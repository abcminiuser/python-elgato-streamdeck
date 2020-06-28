#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import argparse
import logging
import sys

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from PIL import Image

def test(deck):
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

        test_scaled_image = PILHelper.create_scaled_image(deck, Image.new("RGB", (5, 5)))

        deck.set_key_callback(None)
        deck.reset()
        deck.set_brightness(30)
        deck.set_key_image(0, test_key_image)

        deck.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='StreamDeck Library test.')
    parser.add_argument('--model', required=False, help='Stream Deck model name to test')
    args = parser.parse_args()

    manager = DeviceManager(transport="dummy")
    streamdecks = manager.enumerate()

    test_streamdecks = streamdecks

    if args.model:
        test_streamdecks = [d for d in test_streamdecks if d.deck_type() == args.model]

    if len(test_streamdecks) is 0:
        logging.error("Error: No Stream Decks to test. Known models: {}".format([d.deck_type() for d in streamdecks]))
        sys.exit(1)

    for index, deck in enumerate(test_streamdecks):
        test(deck)
