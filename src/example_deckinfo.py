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


# Prints diagnostic information about a given StreamDeck.
def print_deck_info(index, deck):
    key_image_format = deck.key_image_format()
    touchscreen_image_format = deck.touchscreen_image_format()

    flip_description = {
        (False, False): "not mirrored",
        (True, False): "mirrored horizontally",
        (False, True): "mirrored vertically",
        (True, True): "mirrored horizontally/vertically",
    }

    print(f"Deck {index} - {deck.deck_type()}.")
    print(f"\t - ID: {deck.id()}")
    print(f"\t - Serial: '{deck.get_serial_number()}'")
    print(f"\t - Firmware Version: '{deck.get_firmware_version()}'")
    print(
        f"\t - Key Count: {deck.key_count()} (in a {deck.key_layout()[0]}x{deck.key_layout()[1]} grid)"
    )
    if deck.is_visual():
        print(
            "\t - Key Images: {}x{} pixels, {} format, rotated {} degrees, {}".format(
                key_image_format["size"][0],
                key_image_format["size"][1],
                key_image_format["format"],
                key_image_format["rotation"],
                flip_description[key_image_format["flip"]],
            )
        )

        if deck.is_touch():
            print(
                "\t - Touchscreen: {}x{} pixels, {} format, rotated {} degrees, {}".format(
                    touchscreen_image_format["size"][0],
                    touchscreen_image_format["size"][1],
                    touchscreen_image_format["format"],
                    touchscreen_image_format["rotation"],
                    flip_description[touchscreen_image_format["flip"]],
                )
            )
    else:
        print("\t - No Visual Output")


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print(f"Found {len(streamdecks)} Stream Deck(s).\n")

    for index, deck in enumerate(streamdecks):
        deck.open()
        deck.reset()

        print_deck_info(index, deck)

        deck.close()
