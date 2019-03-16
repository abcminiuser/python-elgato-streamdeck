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

import itertools
import threading
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper


# Loads in a source image, extracts out the individual animation frames (if any) and returns an infinite
# generator that returns the next animation frame, in the StreamDeck device's native image format.
def create_frames(deck, image_filename):
    icon_frames = list()

    try:
        # Open the source image asset
        icon = Image.open("assets/{}".format(image_filename))

        # Extract out each animation frame, resizing and converting to the native device image format
        while True:
            image = PILHelper.create_image(deck)

            # Resize the animation frame and paste it into the new image buffer
            icon_frame = icon.convert("RGBA")
            icon_frame.thumbnail(image.size, Image.LANCZOS)
            icon_frame_pos = ((image.width - icon_frame.width) // 2, (image.height - icon_frame.height) // 2)
            image.paste(icon_frame, icon_frame_pos, icon_frame)

            # Store the rendered animation frame in the device's native image format for later use
            icon_frames += [PILHelper.to_native_format(deck, image)]

            # Move to next animation frame in the source image
            icon.seek(icon.tell() + 1)
    except EOFError:
        pass

    # Return an infinite cycle generator that returns the next animation frame each time it is called
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
        # native display format so that they can be quickly pushed to the device
        print("Loading animations...")
        animations = [
            create_frames(deck, "Elephant_Walking_animated.gif"),
            create_frames(deck, "RGB_color_space_animated_view.gif"),
            create_frames(deck, "Simple_CV_Joint_animated.gif"),
        ]
        print("Ready.")

        # Create a mapping of StreamDeck key to animation image that will be displayed
        key_images = dict()
        for k in range(deck.key_count()):
            key_images[k] = animations[k % len(animations)]

        # Helper function that is run periodically, to update the images on each key.
        def update_frames():
            try:
                # Update the key images with the next animation frame
                for key, frames in key_images.items():
                    deck.set_key_image(key, next(frames))
            except (IOError, ValueError):
                # Something went wrong (deck closed?) - abort the animation updates
                return

            # Schedule the next periodic animation frame update
            threading.Timer(0.1, update_frames).start()

        # Kick off the first animation update, which will also schedule the next animation frame
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
