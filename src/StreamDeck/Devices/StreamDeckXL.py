#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .StreamDeck import StreamDeck


class StreamDeckXL(StreamDeck):
    """
    Represents a physically attached StreamDeck XL device.
    """

    KEY_COUNT = 32
    KEY_COLS = 4
    KEY_ROWS = 8

    KEY_PIXEL_WIDTH = 96
    KEY_PIXEL_HEIGHT = 96
    KEY_PIXEL_DEPTH = 3
    KEY_PIXEL_ORDER = "BGR"
    KEY_FLIP = (True, False)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck XL"

    def _read_key_states(self):
        """
        Reads the key states of the StreamDeck. This is used internally by
        :func:`~StreamDeck._read` to talk to the actual device.

        :rtype: list(bool)
        :return: Button states, with the origin at the top-left of the deck.
        """

        states = self.device.read(1 + self.KEY_COUNT)[1:]
        return [bool(s) for s in states]

    def reset(self):
        """
        Resets the StreamDeck, clearing all button images and showing the
        standby image.
        """

        payload = bytearray(2)
        payload[0:2] = [0x03, 0x03]
        self.device.write_feature(payload)

    def set_brightness(self, percent):
        """
        Sets the global screen brightness of the StreamDeck, across all the
        physical buttons.

        :param int/float percent: brightness percent, from [0-100] as an `int`.
        """

        percent = min(max(percent, 0), 100)

        payload = bytearray(32)
        payload[0:2] = [0x03, 0x08, percent]
        self.device.write_feature(payload)

    def get_serial_number(self):
        """
        Gets the serial number of the attached StreamDeck.

        :rtype: str
        :return: String containing the serial number of the attached device.
        """

        serial = self.device.read_feature(0x06, 17)
        return "".join(map(chr, serial[2:]))

    def get_firmware_version(self):
        """
        Gets the firmware version of the attached StreamDeck.

        :rtype: str
        :return: String containing the firmware version of the attached device.
        """

        version = self.device.read_feature(0x05, 17)
        return "".join(map(chr, version[5:]))

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
