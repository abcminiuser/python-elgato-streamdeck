#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import threading
import time
from abc import ABC, abstractmethod
from enum import Enum

from ..Transport.Transport import TransportError


class TouchscreenEventType(Enum):
    """
    Type of event that has occurred for a Touchscreen.
    """

    SHORT = 1
    LONG = 2
    DRAG = 3


class DialEventType(Enum):
    """
    Type of event that has occurred for a Dial.
    """
    TURN = 1
    PUSH = 2


class ControlType(Enum):
    """
    Type of control. This is used when returning internal events from a
    StreamDeck subclass.

    :meta private:
    """
    KEY = 1
    DIAL = 2
    TOUCHSCREEN = 3


class StreamDeck(ABC):
    """
    Represents a physically attached StreamDeck device.
    """

    KEY_COUNT = 0
    KEY_COLS = 0
    KEY_ROWS = 0

    TOUCH_KEY_COUNT = 0

    KEY_PIXEL_WIDTH = 0
    KEY_PIXEL_HEIGHT = 0
    KEY_IMAGE_FORMAT = ""
    KEY_FLIP = (False, False)
    KEY_ROTATION = 0

    TOUCHSCREEN_PIXEL_WIDTH = 0
    TOUCHSCREEN_PIXEL_HEIGHT = 0
    TOUCHSCREEN_IMAGE_FORMAT = ""
    TOUCHSCREEN_FLIP = (False, False)
    TOUCHSCREEN_ROTATION = 0

    SCREEN_PIXEL_WIDTH = 0
    SCREEN_PIXEL_HEIGHT = 0
    SCREEN_IMAGE_FORMAT = ""
    SCREEN_FLIP = (False, False)
    SCREEN_ROTATION = 0

    DIAL_COUNT = 0

    DECK_TYPE = ""
    DECK_VISUAL = False
    DECK_TOUCH = False

    def __init__(self, device):
        self.device = device
        self.last_key_states = [False] * (self.KEY_COUNT + self.TOUCH_KEY_COUNT)
        self.last_dial_states = [False] * self.DIAL_COUNT
        self.read_thread = None
        self.run_read_thread = False
        self.read_poll_hz = 20

        self.key_callback = None
        self.dial_callback = None
        self.touchscreen_callback = None

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
    def _read_control_states(self):
        """
        Reads the raw key states from an attached StreamDeck.

        :return: dictionary containing states for all controls
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
        Read handler for the underlying transport, listening for control state
        changes on the underlying device, caching the new states and firing off
        any registered callbacks.
        """
        while self.run_read_thread:
            try:
                control_states = self._read_control_states()
                if control_states is None:
                    time.sleep(1.0 / self.read_poll_hz)
                    continue

                if ControlType.KEY in control_states:
                    for k, (old, new) in enumerate(zip(self.last_key_states, control_states[ControlType.KEY])):
                        if old == new:
                            continue

                        self.last_key_states[k] = new

                        if self.key_callback is not None:
                            self.key_callback(self, k, new)

                elif ControlType.DIAL in control_states:
                    if DialEventType.PUSH in control_states[ControlType.DIAL]:
                        for k, (old, new) in enumerate(zip(self.last_dial_states, control_states[ControlType.DIAL][DialEventType.PUSH])):
                            if old == new:
                                continue

                            self.last_dial_states[k] = new

                            if self.dial_callback is not None:
                                self.dial_callback(self, k, DialEventType.PUSH, new)

                    if DialEventType.TURN in control_states[ControlType.DIAL]:
                        for k, amount in enumerate(control_states[ControlType.DIAL][DialEventType.TURN]):
                            if amount == 0:
                                continue

                            if self.dial_callback is not None:
                                self.dial_callback(self, k, DialEventType.TURN, amount)

                elif ControlType.TOUCHSCREEN in control_states:
                    if self.touchscreen_callback is not None:
                        self.touchscreen_callback(self, *control_states[ControlType.TOUCHSCREEN])

            except TransportError:
                self.run_read_thread = False
                self.close()

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

            try:
                self.read_thread.join()
            except RuntimeError:
                pass

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

    def is_open(self):
        """
        Indicates if the StreamDeck device is currently open and ready for use.

        :rtype: bool
        :return: `True` if the deck is open, `False` otherwise.
        """
        return self.device.is_open()

    def connected(self):
        """
        Indicates if the physical StreamDeck device this instance is attached to
        is still connected to the host.

        :rtype: bool
        :return: `True` if the deck is still connected, `False` otherwise.
        """
        return self.device.connected()

    def vendor_id(self):
        """
        Retrieves the vendor ID attached StreamDeck. This can be used
        to determine the exact type of attached StreamDeck.

        :rtype: int
        :return: Vendor ID of the attached device.
        """
        return self.device.vendor_id()

    def product_id(self):
        """
        Retrieves the product ID attached StreamDeck. This can be used
        to determine the exact type of attached StreamDeck.

        :rtype: int
        :return: Product ID of the attached device.
        """
        return self.device.product_id()

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

    def touch_key_count(self):
        """
        Retrieves number of touch buttons on the attached StreamDeck device.

        :rtype: int
        :return: Number of touch buttons.
        """
        return self.TOUCH_KEY_COUNT

    def dial_count(self):
        """
        Retrieves number of physical dials on the attached StreamDeck device.

        :rtype: int
        :return: Number of physical dials
        """
        return self.DIAL_COUNT

    def deck_type(self):
        """
        Retrieves the model of Stream Deck.

        :rtype: str
        :return: String containing the model name of the StreamDeck device.
        """
        return self.DECK_TYPE

    def is_visual(self):
        """
        Returns whether the Stream Deck has a visual display output.

        :rtype: bool
        :return: `True` if the deck has a screen, `False` otherwise.
        """
        return self.DECK_VISUAL

    def is_touch(self):
        """
        Returns whether the Stream Deck can receive touch events

        :rtype: bool
        :return: `True` if the deck can receive touch events, `False` otherwise
        """
        return self.DECK_TOUCH

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

    def touchscreen_image_format(self):
        """
        Retrieves the image format accepted by the touchscreen of the Stream
        Deck. Images should be given in this format when drawing on
        touchscreen.

        .. seealso:: See :func:`~StreamDeck.set_touchscreen_image` method to
                     draw an image on the StreamDeck touchscreen.

        :rtype: dict()
        :return: Dictionary describing the various image parameters
                 (size, image format).
        """
        return {
            'size': (self.TOUCHSCREEN_PIXEL_WIDTH, self.TOUCHSCREEN_PIXEL_HEIGHT),
            'format': self.TOUCHSCREEN_IMAGE_FORMAT,
            'flip': self.TOUCHSCREEN_FLIP,
            'rotation': self.TOUCHSCREEN_ROTATION,
        }

    def screen_image_format(self):
        """
        Retrieves the image format accepted by the screen of the Stream
        Deck. Images should be given in this format when drawing on
        screen.

        .. seealso:: See :func:`~StreamDeck.set_screen_image` method to
                     draw an image on the StreamDeck screen.

        :rtype: dict()
        :return: Dictionary describing the various image parameters
                 (size, image format).
        """
        return {
            'size': (self.SCREEN_PIXEL_WIDTH, self.SCREEN_PIXEL_HEIGHT),
            'format': self.SCREEN_IMAGE_FORMAT,
            'flip': self.SCREEN_FLIP,
            'rotation': self.SCREEN_ROTATION,
        }

    def set_poll_frequency(self, hz):
        """
        Sets the frequency of the button polling reader thread, determining how
        often the StreamDeck will be polled for button changes.

        A higher frequency will result in a higher CPU usage, but a lower
        latency between a physical button press and a event from the library.

        :param int hz: Reader thread frequency, in Hz (1-1000).
        """
        self.read_poll_hz = min(max(hz, 1), 1000)

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

    def set_dial_callback(self, callback):
        """
        Sets the callback function called each time there is an interaction
        with a dial on the StreamDeck.

        .. note:: This callback will be fired from an internal reader thread.
                  Ensure that the given callback function is thread-safe.

        .. note:: Only one callback can be registered at one time.

        .. seealso:: See :func:`~StreamDeck.set_dial_callback_async` method
                     for a version compatible with Python 3 `asyncio`
                     asynchronous functions.

        :param function callback: Callback function to fire each time a button
                                state changes.
        """
        self.dial_callback = callback

    def set_dial_callback_async(self, async_callback, loop=None):
        """
        Sets the asynchronous callback function called each time there is an
        interaction with a dial on the StreamDeck. The given callback should
        be compatible with Python 3's `asyncio` routines.

        .. note:: The asynchronous callback will be fired in a thread-safe
                  manner.

        .. note:: This will override the callback (if any) set by
                  :func:`~StreamDeck.set_dial_callback`.

        :param function async_callback: Asynchronous callback function to fire
                                        each time a button state changes.
        :param asyncio.loop loop: Asyncio loop to dispatch the callback into
        """
        import asyncio

        loop = loop or asyncio.get_event_loop()

        def callback(*args):
            asyncio.run_coroutine_threadsafe(async_callback(*args), loop)

        self.set_dial_callback(callback)

    def set_touchscreen_callback(self, callback):
        """
        Sets the callback function called each time there is an interaction
        with a touchscreen on the StreamDeck.

        .. note:: This callback will be fired from an internal reader thread.
                  Ensure that the given callback function is thread-safe.

        .. note:: Only one callback can be registered at one time.

        .. seealso:: See :func:`~StreamDeck.set_touchscreen_callback_async`
                     method for a version compatible with Python 3 `asyncio`
                     asynchronous functions.

        :param function callback: Callback function to fire each time a button
                                state changes.
        """
        self.touchscreen_callback = callback

    def set_touchscreen_callback_async(self, async_callback, loop=None):
        """
        Sets the asynchronous callback function called each time there is an
        interaction with the touchscreen on the StreamDeck. The given callback
        should be compatible with Python 3's `asyncio` routines.

        .. note:: The asynchronous callback will be fired in a thread-safe
                  manner.

        .. note:: This will override the callback (if any) set by
                  :func:`~StreamDeck.set_touchscreen_callback`.

        :param function async_callback: Asynchronous callback function to fire
                                        each time a button state changes.
        :param asyncio.loop loop: Asyncio loop to dispatch the callback into
        """
        import asyncio

        loop = loop or asyncio.get_event_loop()

        def callback(*args):
            asyncio.run_coroutine_threadsafe(async_callback(*args), loop)

        self.set_touchscreen_callback(callback)

    def key_states(self):
        """
        Retrieves the current states of the buttons on the StreamDeck.

        :rtype: list(bool)
        :return: List describing the current states of each of the buttons on
                 the device (`True` if the button is being pressed, `False`
                 otherwise).
        """
        return self.last_key_states

    def dial_states(self):
        """
        Retrieves the current states of the dials (pressed or not) on the
        Stream Deck

        :rtype: list(bool)
        :return: List describing the current states of each of the dials on
                 the device (`True` if the dial is being pressed, `False`
                 otherwise).
        """
        return self.last_dial_states

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

        .. seealso:: See :func:`~StreamDeck.key_image_format` method for
                     information on the image format accepted by the device.

        :param int key: Index of the button whose image is to be updated.
        :param enumerable image: Raw data of the image to set on the button.
                                 If `None`, the key will be cleared to a black
                                 color.
        """
        pass

    @abstractmethod
    def set_touchscreen_image(self, image, x_pos=0, y_pos=0, width=0, height=0):
        """
        Draws an image on the touchscreen in a certain position. The image
        should be in the correct format for the devices, as an enumerable
        collection of bytes.

        .. seealso:: See :func:`~StreamDeck.touchscreen_image_format` method for
                     information on the image format accepted by the device.

        :param enumerable image: Raw data of the image to set on the button.
                                 If `None`, the touchscreen will be cleared.
        :param int x_pos: Position on x axis of the image to draw
        :param int y_pos: Position on y axis of the image to draw
        :param int width: width of the image
        :param int height: height of the image

        """
        pass

    @abstractmethod
    def set_key_color(self, key, r, g, b):
        """
        Sets the color of the touch buttons. These buttons are indexed
        in order after the standard keys.

        :param int key: Index of the button
        :param int r: Red value
        :param int g: Green value
        :param int b: Blue value

        """
        pass

    @abstractmethod
    def set_screen_image(self, image):
        """
        Draws an image on the touchless screen of the StreamDeck.

        .. seealso:: See :func:`~StreamDeck.screen_image_format` method for
                     information on the image format accepted by the device.

        :param enumerable image: Raw data of the image to set on the button.
                                 If `None`, the screen will be cleared.
        """
        pass
