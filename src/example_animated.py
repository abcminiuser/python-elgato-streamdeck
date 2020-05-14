#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script showing one way to display animated images using the
# library, by pre-rendering all the animation frames into the StreamDeck
# device's native image format, and displaying them with a periodic
# timer.

import os
import itertools
import threading
from PIL import Image, ImageSequence
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError


# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")

# Animation frames per second to attempt to display on the StreamDeck devices.
FRAMES_PER_SECOND = 30


# Loads in a source image, extracts out the individual animation frames (if
# any) and returns an infinite generator that returns the next animation frame,
# in the StreamDeck device's native image format.
def create_animation_frames(deck, image_filename):
    icon_frames = list()

    # Open the source image asset.
    icon = Image.open(os.path.join(ASSETS_PATH, image_filename))

    # Iterate through each animation frame of the source image
    for frame in ImageSequence.Iterator(icon):
        # We need source frames in RGBA format, convert now before we resize it.
        icon_frame = frame.convert("RGBA")

        # Create new key image of the correct dimensions, black background.
        image = PILHelper.create_image(deck)

        # Resize the animation frame to best-fit the dimensions of a single key,
        # and paste it onto our blank frame centered as closely as possible.
        icon_frame.thumbnail(image.size, Image.LANCZOS)
        icon_frame_pos = ((image.width - icon_frame.width) // 2, (image.height - icon_frame.height) // 2)
        image.paste(icon_frame, icon_frame_pos, icon_frame)

        # Store the rendered animation frame in the device's native image
        # format for later use, so we don't need to keep converting it.
        icon_frames.append(PILHelper.to_native_format(deck, image))

    # Return an infinite cycle generator that returns the next animation frame
    # each time it is called.
    return itertools.cycle(icon_frames)


# Closes the StreamDeck device on key state change.
def key_change_callback(deck, key, state):
    # First take the lock, so we can ensure we're the only thread that's
    # updating the StreamDeck right now.
    with deck.animation_lock:
        # Reset deck, clearing all button images.
        deck.reset()

        # Close deck handle, terminating internal worker threads.
        deck.close()


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        deck.open()
        deck.reset()

        # We will be using the deck from multiple threads, and we want to be
        # able to update it atomically. Create a mutex we can use to ensure we
        # have exclusive access to this StreamDeck.
        deck.animation_lock = threading.Lock()

        print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))

        # Set initial screen brightness to 30%.
        deck.set_brightness(30)

        # Pre-render a list of animation frames for each source image, in the
        # native display format so that they can be quickly sent to the device.
        print("Loading animations...")
        animations = [
            create_animation_frames(deck, "Elephant_Walking_animated.gif"),
            create_animation_frames(deck, "RGB_color_space_animated_view.gif"),
            create_animation_frames(deck, "Simple_CV_Joint_animated.gif"),
        ]
        print("Ready.")

        # Create a mapping of StreamDeck keys to animation image sets that will
        # be displayed.
        key_images = dict()
        for k in range(deck.key_count()):
            key_images[k] = animations[k % len(animations)]

        # Helper function that is run periodically, to update the images on
        # each key.
        def update_frames():
            # First take the lock, so we can ensure we're the only thread that's
            # updating the StreamDeck right now.
            with deck.animation_lock:
                try:
                    # Update the key images with the next animation frame.
                    for key, frames in key_images.items():
                        deck.set_key_image(key, next(frames))

                    # Schedule the next periodic animation frame update.
                    threading.Timer(1.0 / FRAMES_PER_SECOND, update_frames).start()
                except (TransportError):
                    # Something went wrong while communicating with the device
                    # (closed?) - don't re-schedule the next animation frame.
                    pass

        # Kick off the first animation update, which will also schedule the
        # next animation frame.
        update_frames()

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
