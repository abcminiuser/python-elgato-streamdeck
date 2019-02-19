#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from abc import ABC, abstractmethod

import threading


class StreamDeck(ABC):
    """
    Represents a physically attached original StreamDeck device.
    """

    KEY_COUNT = None
    KEY_COLS = None
    KEY_ROWS = None

    KEY_PIXEL_WIDTH = None
    KEY_PIXEL_HEIGHT = None
    KEY_PIXEL_DEPTH = None
    KEY_PIXEL_ORDER = None
    KEY_FLIP = None
    KEY_ROTATION = None

    DECK_TYPE = None

    def __init__(self, device):
        self.device = device
        self.last_key_states = [False] * self.KEY_COUNT
        self.read_thread = None
        self.key_callback = None

    def __del__(self):
        """
        Deletion handler for the StreamDeck, automatically closing the transport
        if it is currently open and terminating the transport reader thread.
        """
        try:
            self._setup_reader(None)

            self.device.close()
        except (IOError, ValueError):
            pass

    def _read(self):
        """
        Read handler for the underlying transport, listening for button state
        changes on the underlying device, caching the new states and firing off
        any registered callbacks.
        """
        while self.read_thread_run:
            payload = []

            try:
                payload = self.device.read(1 + self.KEY_COUNT)
            except (IOError, ValueError):
                self.read_thread_run = False

            if payload:
                new_key_states = [bool(s) for s in payload[1:]]

                if self.key_callback is not None:
                    for k, (old, new) in enumerate(zip(self.last_key_states, new_key_states)):
                        if old != new:
                            self.key_callback(self, k, new)

                self.last_key_states = new_key_states

    def _setup_reader(self, callback):
        """
        Sets up the internal transport reader thread with the given callback,
        for asynchronous processing of HID events from the device. IF the thread
        already exists, it is terminated and restarted with the new callback
        function.

        :param function callback: Callback to run on the reader thread.
        """
        if self.read_thread is not None:
            self.read_thread_run = False
            self.read_thread.join()

        if callback is not None:
            self.read_thread_run = True
            self.read_thread = threading.Thread(target=callback)
            self.read_thread.daemon = True
            self.read_thread.start()

    def open(self):
        """
        Opens the device for input/output. This must be called prior to setting
        or retrieving any device state.

        .. seealso:: See :func:`~StreamDeck.close` for the corresponding close method.
        """
        self.device.open()
        self._setup_reader(self._read)

    def close(self):
        """
        Closes the device for input/output.

        .. seealso:: See :func:`~StreamDeck.open` for the corresponding open method.
        """
        self.device.close()

    def connected(self):
        """
        Indicates if the physical StreamDeck device this instance is attached to
        is still connected to the host.

        :rtype: bool
        :return: `True` if the deck is still connected, `False` otherwise.
        """
        return self.device.connected()

    def id(self):
        """
        Retrieves the physical ID of the attached StreamDeck. This can be used
        to differentiate one StreamDeck from another.

        :rtype: str
        :return: Identifier for the attached device.
        """
        return self.device.path()

    def key_count(self):
        """
        Retrieves number of physical buttons on the attached StreamDeck device.

        :rtype: int
        :return: Number of physical buttons.
        """
        return self.KEY_COUNT

    def deck_type(self):
        """
        Retrieves the model of Stream Deck.

        :rtype: str
        :return: Text corresponding to the specific type of the device.
        """
        return self.DECK_TYPE

    def key_layout(self):
        """
        Retrieves the physical button layout on the attached StreamDeck device.

        :rtype: (int, int)
        :return (rows, columns): Number of button rows and columns.
        """
        return self.KEY_ROWS, self.KEY_COLS

    def key_image_format(self):
        """
        Retrieves the image format accepted by the attached StreamDeck device.
        Images should be given in this format when setting an image on a button.

        .. seealso:: See :func:`~StreamDeck.set_key_image` method to update the
                     image displayed on a StreamDeck button.

        :rtype: dict()
        :return: Dictionary describing the various image parameters
                 (width, height, pixel depth, RGB order, mirroring and
                 rotation).
        """
        return {
            "width": self.KEY_PIXEL_WIDTH,
            "height": self.KEY_PIXEL_HEIGHT,
            "depth": self.KEY_PIXEL_DEPTH,
            "order": self.KEY_PIXEL_ORDER,
            "flip": self.KEY_FLIP,
            "rotation": self.KEY_ROTATION,
        }

    def set_key_callback(self, callback):
        """
        Sets the callback function called each time a button on the StreamDeck
        changes state (either pressed, or released).

        .. note:: This callback will be fired from an internal reader thread.
                  Ensure that the given callback function is thread-safe.

        .. note:: Only one callback can be registered at one time.

        .. seealso:: See :func:`~StreamDeck.set_key_callback_async` method for
                     a version compatible with Python 3 `asyncio` asynchronous
                     functions.

        :param function callback: Callback function to fire each time a button
                                state changes.
        """
        self.key_callback = callback

    def set_key_callback_async(self, async_callback, loop=None):
        """
        Sets the asynchronous callback function called each time a button on the
        StreamDeck changes state (either pressed, or released). The given
        callback should be compatible with Python 3's `asyncio` routines.

        .. note:: The asynchronous callback will be fired in a thread-safe
                  manner.

        .. note:: This will override the callback (if any) set by
                  :func:`~StreamDeck.set_key_callback`.

        :param function async_callback: Asynchronous callback function to fire
                                        each time a button state changes.
        :param function loop: Asyncio loop to dispatch the callback into
        """
        import asyncio

        loop = loop or asyncio.get_event_loop()

        def callback(*args):
            asyncio.run_coroutine_threadsafe(async_callback(*args), loop)

        self.set_key_callback(callback)

    def key_states(self):
        """
        Retrieves the current states of the buttons on the StreamDeck.

        :rtype: list(bool)
        :return: List describing the current states of each of the buttons on
                 the device (`True` if the button is being pressed,
                 `False` otherwise).
        """
        return self.last_key_states

    @abstractmethod
    def reset(self):
        """
        Resets the StreamDeck, clearing all button images and showing the
        standby image.
        """
        pass

    @abstractmethod
    def set_brightness(self, percent):
        """
        Sets the global screen brightness of the ScreenDeck, across all the
        physical buttons.

        :param int/float percent: brightness percent, from [0-100] as an `int`,
                                  or normalized to [0.0-1.0] as a `float`.
        """
        pass

    @abstractmethod
    def set_key_image(self, key, image):
        """
        Sets the image of a button on the StremDeck to the given image. The
        image being set should be in the correct format for the device, as an
        enumerable collection of pixels.

        .. seealso:: See :func:`~StreamDeck.get_key_image_format` method for
                     information on the image format accepted by the device.

        :param int key: Index of the button whose image is to be updated.
        :param enumerable image: Pixel data of the image to set on the button.
                                 If `None`, the key will be cleared to a black
                                 color.
        """
        pass
