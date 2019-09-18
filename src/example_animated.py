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
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper


# Folder location of image assets used by this example
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")

# Animation frames per second to attempt to display on the StreamDeck devices
FRAMES_PER_SECOND = 30


# Loads in a source image, extracts out the individual animation frames (if
# any) and returns an infinite generator that returns the next animation frame,
# in the StreamDeck device's native image format.
def create_animation_frames(deck, image_filename):
    icon_frames = list()

    # Open the source image asset
    icon = Image.open(os.path.join(ASSETS_PATH, image_filename))

    # Create a blank key image in the host image format, which we can
    # duplicate quickly for each animation frame to save time
    blank_image = PILHelper.create_image(deck)

    try:
        # Extract out each animation frame, resizing and converting to the
        # native device image format
        while True:
            image = blank_image.copy()

            # Resize the animation frame and paste it into the new image buffer
            icon_frame = icon.convert("RGBA")
            icon_frame.thumbnail(image.size, Image.LANCZOS)
            icon_frame_pos = ((image.width - icon_frame.width) // 2, (image.height - icon_frame.height) // 2)
            image.paste(icon_frame, icon_frame_pos, icon_frame)

            # Store the rendered animation frame in the device's native image
            # format for later use, so we don't need to keep converting it
            icon_frames.append(PILHelper.to_native_format(deck, image))

            # Move to next animation frame in the source image
            icon.seek(icon.tell() + 1)
    except EOFError:
        # End of file, all image frames have been extracted
        pass

    # Return an infinite cycle generator that returns the next animation frame
    # each time it is called
    return itertools.cycle(icon_frames)


# Prints key state change information and closes the StreamDeck device.
def key_change_callback(deck, key, state):
    # Print new key state
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    # Reset deck, clearing all button images
    deck.reset()

    # Close deck handle, terminating internal worker threads
    deck.close()


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        deck.open()
        deck.reset()

        # Set initial screen brightness to 30%
        deck.set_brightness(30)

        # Pre-render a list of animation frames for each source image, in the
        # native display format so that they can be quickly sent to the device
        print("Loading animations...")
        animations = [
            create_animation_frames(deck, "Elephant_Walking_animated.gif"),
            create_animation_frames(deck, "RGB_color_space_animated_view.gif"),
            create_animation_frames(deck, "Simple_CV_Joint_animated.gif"),
        ]
        print("Ready.")

        # Create a mapping of StreamDeck keys to animation image sets that will
        # be displayed
        key_images = dict()
        for k in range(deck.key_count()):
            key_images[k] = animations[k % len(animations)]

        # Helper function that is run periodically, to update the images on
        # each key.
        def update_frames():
            try:
                # Update the key images with the next animation frame
                for key, frames in key_images.items():
                    deck.set_key_image(key, next(frames))

                # Schedule the next periodic animation frame update
                threading.Timer(1.0 / FRAMES_PER_SECOND, update_frames).start()
            except (IOError, ValueError):
                # Something went wrong (deck closed?) - don't re-schedule the
                # next animation frame
                pass

        # Kick off the first animation update, which will also schedule the
        # next animation frame
        update_frames()

        # Register callback function for when a key state changes
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed)
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
