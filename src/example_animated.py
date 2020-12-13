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
import os
import threading
import time

from fractions import Fraction
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
        # Create new key image of the correct dimensions, black background.
        frame_image = PILHelper.create_scaled_image(deck, frame)

        # Pre-convert the generated image to the native format of the StreamDeck
        # so we don't need to keep converting it when showing it on the device.
        native_frame_image = PILHelper.to_native_format(deck, frame_image)

        # Store the rendered animation frame for later user.
        icon_frames.append(native_frame_image)

    # Return an infinite cycle generator that returns the next animation frame
    # each time it is called.
    return itertools.cycle(icon_frames)


# Closes the StreamDeck device on key state change.
def key_change_callback(deck, key, state):
    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
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

        # Helper function that will run a periodic loop which updates the
        # images on each key.
        def animate(fps):
            # Convert frames per second to frame time in seconds.
            #
            # Frame time often cannot be fully expressed by a float type,
            # meaning that we have to use fractions.
            frame_time = Fraction(1, fps)

            # Get a starting absolute time reference point.
            #
            # We need to use an absolute time clock, instead of relative sleeps
            # with a constant value, to avoid drifting.
            #
            # Drifting comes from an overhead of scheduling the sleep itself -
            # it takes some small amount of time for `time.sleep()` to execute.
            next_frame = Fraction(time.time())

            # Periodic loop that will render every frame at the set FPS until
            # the StreamDeck device we're using is closed.
            while True:
                try:
                    # Use a scoped-with on the deck to ensure we're the only
                    # thread using it right now.
                    with deck:
                        # Update the key images with the next animation frame.
                        for key, frames in key_images.items():
                            deck.set_key_image(key, next(frames))
                except TransportError as err:
                    print("TransportError: {0}".format(err))
                    # Something went wrong while communicating with the device
                    # (closed?) - don't re-schedule the next animation frame.
                    break

                # Set the next frame absolute time reference point.
                #
                # We are running at the fixed `fps`, so this is as simple as
                # adding the frame time we calculated earlier.
                next_frame += frame_time

                # Knowing the start of the next frame we can calculate how long
                # we have to sleep until its start.
                sleep_interval = float(next_frame) - time.time()

                # Schedule the next periodic frame update.
                #
                # `sleep_interval` can be a negative number when current FPS
                # setting is too high for the combination of host and
                # StreamDeck to handle.
                #
                # It would mean that we are running late and don't have to
                # sleep at all before rendering the next frame.
                if sleep_interval >= 0:
                    time.sleep(sleep_interval)

        # Kick off the key image animating thread.
        threading.Thread(target=animate, args=(FRAMES_PER_SECOND,)).start()

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()
