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
from PIL import Image, ImageDraw


def test_pil_helpers(deck):
    test_scaled_image = PILHelper.create_scaled_image(deck, Image.new("RGB", (1, 1)))     # noqa: F841

    test_key_image = PILHelper.create_image(deck)
    test_key_image = PILHelper.to_native_format(deck, test_key_image)


def test_basic_apis(deck):
    with deck:
        deck.open()

        connected = deck.connected()     # noqa: F841
        deck_id = deck.id()     # noqa: F841
        key_count = deck.key_count()     # noqa: F841
        deck_type = deck.deck_type()     # noqa: F841
        key_layout = deck.key_layout()     # noqa: F841
        image_format = deck.key_image_format()     # noqa: F841
        key_states = deck.key_states()     # noqa: F841

        deck.set_key_callback(None)
        deck.reset()
        deck.set_brightness(30)

        test_key_image = PILHelper.create_image(deck)
        test_key_image = PILHelper.to_native_format(deck, test_key_image)

        deck.set_key_image(0, None)
        deck.set_key_image(0, test_key_image)

        deck.close()


def test_key_pattern(deck):
    test_key_image = PILHelper.create_image(deck)

    draw = ImageDraw.Draw(test_key_image)
    draw.rectangle((0, 0) + test_key_image.size, fill=(0x11, 0x22, 0x33), outline=(0x44, 0x55, 0x66))

    test_key_image = PILHelper.to_native_format(deck, test_key_image)

    with deck:
        deck.open()
        deck.set_key_image(0, test_key_image)
        deck.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="StreamDeck Library test.")
    parser.add_argument("--model", help="Stream Deck model name to test")
    parser.add_argument("--test", help="Stream Deck test to run")
    args = parser.parse_args()

    manager = DeviceManager(transport="dummy")
    streamdecks = manager.enumerate()

    test_streamdecks = streamdecks
    if args.model:
        test_streamdecks = [deck for deck in test_streamdecks if deck.deck_type() == args.model]

    if len(test_streamdecks) == 0:
        logging.error("Error: No Stream Decks to test. Known models: {}".format([d.deck_type() for d in streamdecks]))
        sys.exit(1)

    tests = {
        "PIL Helpers": test_pil_helpers,
        "Basic APIs": test_basic_apis,
        "Key Pattern": test_key_pattern,
    }

    test_runners = tests
    if args.test:
        test_runners = {name: test for (name, test) in test_runners.items() if name == args.test}

    if len(test_runners) == 0:
        logging.error("Error: No Stream Decks tests to run. Known tests: {}".format([name for name, test in tests.items()]))
        sys.exit(1)

    for deck_index, deck in enumerate(test_streamdecks):
        logging.info("Using Deck Type: {}".format(deck.deck_type()))

        for name, test in test_runners.items():
            logging.info("Running Test: {}".format(name))
            test(deck)
            logging.info("Finished Test: {}".format(name))
