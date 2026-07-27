#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#

# Example script showing some Stream Deck + XL specific functions

import threading

from PIL import Image, ImageDraw
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices.StreamDeck import DialEventType, TouchscreenEventType
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError


def make_key_image(deck, color, label):
    image = PILHelper.create_key_image(deck, background=color)
    draw = ImageDraw.Draw(image)
    draw.text((image.width / 2, image.height / 2), text=label, anchor="mm", fill="white")
    return PILHelper.to_native_key_format(deck, image)


# callback when keys are pressed or released
def key_change_callback(deck, key, key_state):
    print("Key: " + str(key) + " state: " + str(key_state))
    color = "green" if key_state else "black"
    deck.set_key_image(key, make_key_image(deck, color, str(key)))


# callback when dials are pressed/turned
def dial_change_callback(deck, dial, event, value):
    if event == DialEventType.PUSH:
        print(f"Dial {dial} pushed: {value}")

        # Draw a status line on the touchscreen window showing which dial
        # was pushed.
        image = PILHelper.create_touchscreen_image(deck, background="black")
        draw = ImageDraw.Draw(image)
        draw.text((10, image.height / 2), text=f"Dial {dial} pushed!", anchor="lm", fill="white")
        deck.set_touchscreen_image(PILHelper.to_native_touchscreen_format(deck, image))

    elif event == DialEventType.TURN:
        print(f"Dial {dial} turned: {value}")


# callback when the touchscreen window is touched
def touchscreen_event_callback(deck, evt_type, value):
    if evt_type == TouchscreenEventType.SHORT:
        print("Tap @ " + str(value['x']) + "," + str(value['y']))
    elif evt_type == TouchscreenEventType.LONG:
        print("Press @ " + str(value['x']) + "," + str(value['y']))
    elif evt_type == TouchscreenEventType.DRAG:
        print("Flick " + str(value['x']) + "," + str(value['y']) + " -> " + str(value['x_out']) + "," + str(value['y_out']))


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        if deck.DECK_TYPE != 'Stream Deck + XL':
            print(deck.DECK_TYPE)
            print("Sorry, this example only works with the Stream Deck + XL")
            continue

        deck.open()
        deck.reset()

        deck.set_key_callback(key_change_callback)
        deck.set_dial_callback(dial_change_callback)
        deck.set_touchscreen_callback(touchscreen_event_callback)

        print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))

        deck.set_brightness(75)

        # Light up every key with its index number
        for key in range(0, deck.KEY_COUNT):
            deck.set_key_image(key, make_key_image(deck, "black", str(key)))

        # Draw a full-width background image on the LCD panel behind the keys
        screen_image = PILHelper.create_screen_image(deck, background="black")
        deck.set_screen_image(PILHelper.to_native_screen_format(deck, screen_image))

        # Draw an initial message on the touchscreen window strip
        touch_image = PILHelper.create_touchscreen_image(deck, background="black")
        draw = ImageDraw.Draw(touch_image)
        draw.text((10, touch_image.height / 2), text="Press a key or turn/push a dial...", anchor="lm", fill="white")
        deck.set_touchscreen_image(PILHelper.to_native_touchscreen_format(deck, touch_image))

        # Wait until all application threads have terminated (for this
        # example, this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except (TransportError, RuntimeError):
                pass
