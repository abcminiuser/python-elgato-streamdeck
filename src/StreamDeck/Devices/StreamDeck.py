#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import threading
import time
from abc import ABC, abstractmethod

from ..Transport.Transport import TransportError


class StreamDeck(ABC):
    """
    Represents a physically attached StreamDeck device.
    """

    KEY_COUNT = None
    KEY_COLS = None
    KEY_ROWS = None

    KEY_PIXEL_WIDTH = None
    KEY_PIXEL_HEIGHT = None
    KEY_IMAGE_CODEC = None
    KEY_FLIP = None
    KEY_ROTATION = None

    DECK_TYPE = None

    def __init__(self, device):
        self.device = device
        self.last_key_states = [False] * self.KEY_COUNT
        self.read_thread = None
        self.run_read_thread = False
        self.key_callback = None

        self.update_lock = threading.RLock()

    def __del__(self):
        """
        Delete handler for the StreamDeck, automatically closing the transport
        if it is currently open and terminating the transport reader thread.
        """
        try:
            self._setup_reader(None)
        except (TransportError, ValueError):
            pass

        try:
            self.device.close()
        except (TransportError):
            pass

    def __enter__(self):
        """
        Enter handler for the StreamDeck, taking the exclusive update lock on
        the deck. This can be used in a `with` statement to ensure that only one
        thread is currently updating the deck, even if it is doing multiple
        operations (e.g. setting the image on multiple keys).
        """
        self.update_lock.acquire()

    def __exit__(self, type, value, traceback):
        """
        Exit handler for the StreamDeck, releasing the exclusive update lock on
        the deck.
        """
        self.update_lock.release()

    @abstractmethod
    def _read_key_states(self):
        """
        Reads the raw key states from an attached StreamDeck.

        :rtype: list(bool)
        :return: List containing the raw key states.
        """
        pass

    @abstractmethod
    def _reset_key_stream(self):
        """
        Sends a blank key report to the StreamDeck, resetting the key image
        streamer in the device. This prevents previously started partial key
        writes that were not completed from corrupting images sent from this
        application.
        """
        pass

    def _extract_string(self, data):
        """
        Extracts out a human-readable string from a collection of raw bytes,
        removing any trailing whitespace or data after the first NUL byte.
        """

        return str(bytes(data), 'ascii', 'replace').partition('\0')[0].rstrip()

    def _read(self):
        """
        Read handler for the underlying transport, listening for button state
        changes on the underlying device, caching the new states and firing off
        any registered callbacks.
        """
        while self.run_read_thread:
            try:
                new_key_states = self._read_key_states()
                if new_key_states is None:
                    time.sleep(.05)
                    continue

                if self.key_callback is not None:
                    for k, (old, new) in enumerate(zip(self.last_key_states, new_key_states)):
                        if old != new:
                            self.key_callback(self, k, new)

                self.last_key_states = new_key_states
            except (TransportError):
                self.run_read_thread = False

    def _setup_reader(self, callback):
        """
        Sets up the internal transport reader thread with the given callback,
        for asynchronous processing of HID events from the device. If the thread
        already exists, it is terminated and restarted with the new callback
        function.

        :param function callback: Callback to run on the reader thread.
        """
        if self.read_thread is not None:
            self.run_read_thread = False
            self.read_thread.join()

        if callback is not None:
            self.run_read_thread = True
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

        self._reset_key_stream()
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
        :return: String containing the model name of the StreamDeck device..
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
                 (size, image format, image mirroring and rotation).
        """
        return {
            'size': (self.KEY_PIXEL_WIDTH, self.KEY_PIXEL_HEIGHT),
            'format': self.KEY_IMAGE_FORMAT,
            'flip': self.KEY_FLIP,
            'rotation': self.KEY_ROTATION,
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
        :param asyncio.loop loop: Asyncio loop to dispatch the callback into
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
                 the device (`True` if the button is being pressed, `False`
                 otherwise).
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
        Sets the global screen brightness of the StreamDeck, across all the
        physical buttons.

        :param int/float percent: brightness percent, from [0-100] as an `int`,
                                  or normalized to [0.0-1.0] as a `float`.
        """
        pass

    @abstractmethod
    def get_serial_number(self):
        """
        Gets the serial number of the attached StreamDeck.

        :rtype: str
        :return: String containing the serial number of the attached device.
        """
        pass

    @abstractmethod
    def get_firmware_version(self):
        """
        Gets the firmware version of the attached StreamDeck.

        :rtype: str
        :return: String containing the firmware version of the attached device.
        """
        pass

    @abstractmethod
    def set_key_image(self, key, image):
        """
        Sets the image of a button on the StreamDeck to the given image. The
        image being set should be in the correct format for the device, as an
        enumerable collection of bytes.

        .. seealso:: See :func:`~StreamDeck.get_key_image_format` method for
                     information on the image format accepted by the device.

        :param int key: Index of the button whose image is to be updated.
        :param enumerable image: Raw data of the image to set on the button.
                                 If `None`, the key will be cleared to a black
                                 color.
        """
        pass
