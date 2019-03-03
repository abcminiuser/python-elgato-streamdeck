#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .StreamDeck import StreamDeck


class StreamDeckOriginal(StreamDeck):
    """
    Represents a physically attached original StreamDeck device.
    """

    KEY_COUNT = 15
    KEY_COLS = 5
    KEY_ROWS = 3

    KEY_PIXEL_WIDTH = 72
    KEY_PIXEL_HEIGHT = 72
    KEY_PIXEL_DEPTH = 3
    KEY_PIXEL_ORDER = "BGR"
    KEY_FLIP = (True, False)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck (Original)"

    KEY_IMAGE_SIZE = KEY_PIXEL_WIDTH * KEY_PIXEL_HEIGHT * KEY_PIXEL_DEPTH
    START_PAGE = 1
    REPORT_LENGTH = 8191
    IMAGE_BYTES_PAGE_1 = 2583 * 3

    def _convert_key_id_origin(self, key):
        """
        Converts a key index from or to a origin at the physical top-left of
        the StreamDeck device.

        :param int key: Index of the button with either a device or top-left origin.

        :rtype: int
        :return: Key index converted to the opposite key origin (device or top-left).
        """

        key_col = key % self.KEY_COLS
        return (key - key_col) + ((self.KEY_COLS - 1) - key_col)

    def _read_key_states(self):
        """
        Reads the key states of the StreamDeck. This is used internally by
        :func:`~StreamDeck._read` to talk to the actual device.

        :rtype: list(bool)
        :return: Button states, with the origin at the top-left of the deck.
        """

        states = self.device.read(1 + self.KEY_COUNT)[1:]
        return [bool(states[self._convert_key_id_origin(k)]) for k in range(self.KEY_COUNT)]

    def reset(self):
        """
        Resets the StreamDeck, clearing all button images and showing the
        standby image.
        """

        payload = bytearray(17)
        payload[0:2] = [0x0B, 0x63]
        self.device.write_feature(payload)

    def set_brightness(self, percent):
        """
        Sets the global screen brightness of the StreamDeck, across all the
        physical buttons.

        :param int/float percent: brightness percent, from [0-100] as an `int`.
        """

        percent = min(max(percent, 0), 100)

        payload = bytearray(17)
        payload[0:6] = [0x05, 0x55, 0xaa, 0xd1, 0x01, percent]
        self.device.write_feature(payload)

    def get_serial_number(self):
        """
        Gets the serial number of the attached StreamDeck.

        :rtype: str
        :return: String containing the serial number of the attached device.
        """

        serial = self.device.read_feature(0x03, 17)
        return "".join(map(chr, serial[5:]))

    def get_firmware_version(self):
        """
        Gets the firmware version of the attached StreamDeck.

        :rtype: str
        :return: String containing the firmware version of the attached device.
        """

        version = self.device.read_feature(0x04, 17)
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

        image = bytes(image or self.KEY_IMAGE_SIZE)

        if min(max(key, 0), self.KEY_COUNT) != key:
            raise IndexError("Invalid key index {}.".format(key))

        if len(image) != self.KEY_IMAGE_SIZE:
            raise ValueError("Invalid image size {}.".format(len(image)))

        key = self._convert_key_id_origin(key)

        header_1 = [
            0x02, 0x01, self.START_PAGE, 0x00, 0x00, key + 1, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x42, 0x4d, 0xf6, 0x3c, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x36, 0x00, 0x00, 0x00, 0x28, 0x00,
            0x00, 0x00, 0x48, 0x00, 0x00, 0x00, 0x48, 0x00,
            0x00, 0x00, 0x01, 0x00, 0x18, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xc0, 0x3c, 0x00, 0x00, 0xc4, 0x0e,
            0x00, 0x00, 0xc4, 0x0e, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]
        header_2 = [
            0x02, 0x01, 0x02, 0x00, 0x01, key + 1, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]

        payload_1 = bytes(header_1) + image[: self.IMAGE_BYTES_PAGE_1]
        payload_2 = bytes(header_2) + image[self.IMAGE_BYTES_PAGE_1:]

        self.device.write(payload_1)
        self.device.write(payload_2)
