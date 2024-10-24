#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .StreamDeck import StreamDeck, ControlType


class StreamDeckOriginal(StreamDeck):
    """
    Represents a physically attached StreamDeck Original device.
    """

    KEY_COUNT = 15
    KEY_COLS = 5
    KEY_ROWS = 3

    KEY_PIXEL_WIDTH = 72
    KEY_PIXEL_HEIGHT = 72
    KEY_IMAGE_FORMAT = "BMP"
    KEY_FLIP = (True, True)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck Original"
    DECK_VISUAL = True

    IMAGE_REPORT_LENGTH = 8191
    IMAGE_REPORT_HEADER_LENGTH = 16

    # 72 x 72 black BMP
    BLANK_KEY_IMAGE = [
        0x42, 0x4d, 0xf6, 0x3c, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x36, 0x00, 0x00, 0x00, 0x28, 0x00,
        0x00, 0x00, 0x48, 0x00, 0x00, 0x00, 0x48, 0x00,
        0x00, 0x00, 0x01, 0x00, 0x18, 0x00, 0x00, 0x00,
        0x00, 0x00, 0xc0, 0x3c, 0x00, 0x00, 0xc4, 0x0e,
        0x00, 0x00, 0xc4, 0x0e, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ] + [0] * (KEY_PIXEL_WIDTH * KEY_PIXEL_HEIGHT * 3)

    def _convert_key_id_origin(self, key):
        key_col = key % self.KEY_COLS
        return (key - key_col) + ((self.KEY_COLS - 1) - key_col)

    def _read_control_states(self):
        states = self.device.read(1 + self.KEY_COUNT)
        if states is None:
            return None

        states = states[1:]
        return {
            ControlType.KEY: [bool(states[s]) for s in map(self._convert_key_id_origin, range(self.KEY_COUNT))]
        }

    def _reset_key_stream(self):
        payload = bytearray(self.IMAGE_REPORT_LENGTH)
        payload[0] = 0x02
        self.device.write(payload)

    def reset(self):
        payload = bytearray(17)
        payload[0:2] = [0x0B, 0x63]
        self.device.write_feature(payload)

    def set_brightness(self, percent):
        if isinstance(percent, float):
            percent = int(100.0 * percent)

        percent = min(max(percent, 0), 100)

        payload = bytearray(17)
        payload[0:6] = [0x05, 0x55, 0xaa, 0xd1, 0x01, percent]
        self.device.write_feature(payload)

    def get_serial_number(self):
        serial = self.device.read_feature(0x03, 17)
        return self._extract_string(serial[5:])

    def get_firmware_version(self):
        version = self.device.read_feature(0x04, 17)
        return self._extract_string(version[5:])

    def set_key_image(self, key, image):
        if min(max(key, 0), self.KEY_COUNT) != key:
            raise IndexError("Invalid key index {}.".format(key))

        image = bytes(image or self.BLANK_KEY_IMAGE)
        image_report_payload_length = len(image) // 2

        key = self._convert_key_id_origin(key)

        page_number = 0
        bytes_remaining = len(image)
        while bytes_remaining > 0:
            this_length = min(bytes_remaining, image_report_payload_length)
            bytes_sent = page_number * image_report_payload_length

            header = [
                0x02,
                0x01,
                page_number + 1,
                0,
                1 if this_length == bytes_remaining else 0,
                key + 1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ]

            payload = bytes(header) + image[bytes_sent:bytes_sent + this_length]
            padding = bytearray(self.IMAGE_REPORT_LENGTH - len(payload))
            self.device.write(payload + padding)

            bytes_remaining = bytes_remaining - this_length
            page_number = page_number + 1

    def set_touchscreen_image(self, image, x_pos=0, y_pos=0, width=0, height=0):
        pass

    def set_key_color(self, key, r, g, b):
        pass

    def set_screen_image(self, image):
        pass
