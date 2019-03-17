#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script that prints out information about any discovered StreamDeck
# devices to the console.

from StreamDeck.DeviceManager import DeviceManager


# Prints diagnostic information about a given StreamDeck
def print_deck_info(index, deck):
    image_format = deck.key_image_format()

    flip_description = {
        (False, False): "not mirrored",
        (True, False): "mirrored horizontally",
        (False, True): "mirrored vertically",
        (True, True): "mirrored horizontally/vertically",
    }

    print("Deck {} - {}.".format(index, deck.deck_type()), flush=True)
    print("\t - ID: {}".format(deck.id()), flush=True)
    print("\t - Serial: {}".format(deck.get_serial_number()), flush=True)
    print("\t - Firmware Version: {}".format(deck.get_firmware_version()), flush=True)
    print("\t - Key Count: {} ({}x{} grid)".format(
        deck.key_count(),
        deck.key_layout()[0],
        deck.key_layout()[1]), flush=True)
    print("\t - Key Image Format: {}x{} pixels, {} order, rotated {} degrees, {}".format(
        image_format['width'], image_format['height'],
        image_format['order'],
        image_format['rotation'],
        flip_description[image_format['flip']]), flush=True)


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        deck.open()
        deck.reset()

        print_deck_info(index, deck)

        deck.close()
