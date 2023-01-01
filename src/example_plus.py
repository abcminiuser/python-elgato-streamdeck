#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script showing some Stream Deck + specific functions

import os
import threading
import io

from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")


# image for idle state
img = Image.new('RGB', (120, 120), color='black')
released_icon = Image.open(os.path.join(ASSETS_PATH, 'Released.png')).resize((80,80))
img.paste(released_icon, (20, 20), released_icon)

img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_released_bytes = img_byte_arr.getvalue()

# image for pressed state
img = Image.new('RGB', (120, 120), color='black')
pressed_icon = Image.open(os.path.join(ASSETS_PATH, 'Pressed.png')).resize((80,80))
img.paste(pressed_icon, (20, 20), pressed_icon)

img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_pressed_bytes = img_byte_arr.getvalue()


# image for pressed state


# callback when buttons are pressed or released
def key_change(deck, key, key_state):
    print("Key: " + str(key) + " state: " + str(key_state))

    deck.set_key_image(key, img_pressed_bytes if key_state else img_released_bytes)

# callback when rotaries are pressed or released
def rotary_change(deck, rotary, rotary_state):
    print("rotary pushed: " + str(rotary) + " state: " + str(rotary_state))
    if rotary == 3 and rotary_state:
        deck.reset()
        deck.close()
    else:
        # build an image for the touch lcd
        img = Image.new('RGB', (800, 100), 'black')
        icon = Image.open(os.path.join(ASSETS_PATH, 'Exit.png')).resize((80,80))
        img.paste(icon, (690, 10), icon)

        for rotno in range(0, deck.ROTARY_COUNT-1):
            img.paste(pressed_icon if (rotary==rotno and rotary_state ) else released_icon, (30+(rotno*220), 10), pressed_icon if (rotary==rotno and rotary_state ) else released_icon)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        deck.set_lcd_image(0, 0, 800, 100, img_byte_arr)

# callback when rotaries are turned
def rotary_turned(values):
    for rotary_no, (value) in enumerate(values):
        if value != 0:
            print("rotary "+ str(rotary_no) +" turned: " + str(value))


# callback when lcd is touched
def lcd_touched(event_type, x, y, x_out = 0, y_out = 0):
    if event_type == deck.TOUCH_EVENT_SHORT:

        print("Short touch @ " + str(x) + "," + str(y))

    elif event_type == deck.TOUCH_EVENT_LONG:

        print("Long touch @ " + str(x) + "," + str(y))

    elif event_type == deck.TOUCH_EVENT_DRAG:

        print("Drag started @ " + str(x) + "," + str(y) +" ended @ "  + str(x_out) + "," + str(y_out) )


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        # This example only works with devices that have screens.

        if deck.DECK_TYPE != 'Stream Deck +':
            print(deck.DECK_TYPE)
            print("Sorry, this example only works with Stream Deck +")
            continue

        deck.open()
        deck.reset()

        deck.set_key_callback(key_change)
        deck.set_rotarypush_callback(rotary_change)
        deck.set_rotaryturn_callback(rotary_turned)
        deck.set_lcdtouch_callback(lcd_touched)

        print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))

        # Set initial screen brightness to 30%.
        deck.set_brightness(100)

        for key in range(0, deck.KEY_COUNT):
            deck.set_key_image(key, img_released_bytes)

        # build an image for the touch lcd
        img = Image.new('RGB', (800, 100), 'black')
        icon = Image.open(os.path.join(ASSETS_PATH, 'Exit.png')).resize((80,80))
        img.paste(icon, (690, 10), icon)

        for rotary in range(0, deck.ROTARY_COUNT-1):
            img.paste(released_icon, (30+(rotary*220), 10), released_icon)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')

        deck.set_lcd_image(0, 0, 800, 100, img_byte_arr.getvalue())

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass
