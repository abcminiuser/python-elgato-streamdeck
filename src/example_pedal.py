#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script showing basic library usage, printing button presses. This
# example only shows key events, and is intended to demonstrate how to get
# such events from device that lack screens, i.e. the StreamDeck Pedal.

import threading

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Transport.Transport import TransportError


def key_change_callback(deck, key, state):
    print("Deck {} Key {} = {}".format(deck.id(), key, "down" if state else "up"), flush=True)


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print(f"Found {len(streamdecks)} Stream Deck(s).\n")

    for index, deck in enumerate(streamdecks):
        deck.open()

        print(f"Opened '{deck.deck_type()}' device (serial number: '{deck.get_serial_number()}', fw: '{deck.get_firmware_version()}')")

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except (TransportError, RuntimeError):
                pass
