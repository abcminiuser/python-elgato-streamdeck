#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .StreamDeck import StreamDeck, ControlType, DialEventType, TouchscreenEventType
from ..ImageHelpers import PILHelper


def _dials_rotation_transform(value):
    if value < 0x80:
        # Clockwise rotation
        return value
    else:
        # Counterclockwise rotation
        return -(0x100 - value)


class StreamDeckPlusXL(StreamDeck):
    KEY_COUNT = 36
    KEY_COLS = 9
    KEY_ROWS = 4

    DIAL_COUNT = 6

    KEY_PIXEL_WIDTH = 112
    KEY_PIXEL_HEIGHT = 112
    KEY_IMAGE_FORMAT = "JPEG"
    KEY_FLIP = (False, False)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck + XL"
    DECK_VISUAL = True
    DECK_TOUCH = True

    TOUCHSCREEN_PIXEL_HEIGHT = 100
    TOUCHSCREEN_PIXEL_WIDTH = 1200
    TOUCHSCREEN_IMAGE_FORMAT = "JPEG"
    TOUCHSCREEN_FLIP = (False, False)
    TOUCHSCREEN_ROTATION = 0

    _INPUT_REPORT_LENGTH = 64

    _IMG_PACKET_LEN = 1024

    _KEY_PACKET_HEADER = 8
    _LCD_PACKET_HEADER = 16

    _KEY_PACKET_PAYLOAD_LEN = _IMG_PACKET_LEN - _KEY_PACKET_HEADER
    _LCD_PACKET_PAYLOAD_LEN = _IMG_PACKET_LEN - _LCD_PACKET_HEADER

    _DIAL_EVENT_TRANSFORM = {
        DialEventType.TURN: _dials_rotation_transform,
        DialEventType.PUSH: bool,
    }

    def __init__(self, device):
        super().__init__(device)
        self.BLANK_KEY_IMAGE = PILHelper.to_native_key_format(
            self, PILHelper.create_key_image(self, "black")
        )
        self.BLANK_TOUCHSCREEN_IMAGE = PILHelper.to_native_touchscreen_format(
            self, PILHelper.create_touchscreen_image(self, "black")
        )

    def _reset_key_stream(self):
        payload = bytearray(self._IMG_PACKET_LEN)
        payload[0] = 0x02
        self.device.write(payload)

    def reset(self):
        payload = bytearray(32)
        payload[0:2] = [0x03, 0x02]
        self.device.write_feature(payload)

    def _read_control_states(self):
        states = self.device.read(self._INPUT_REPORT_LENGTH)

        if states is None:
            return None

        states = states[1:]

        if states[0] == 0x00:  # Key Event
            new_key_states = [bool(s) for s in states[3:3 + self.KEY_COUNT]]

            return {
                ControlType.KEY: new_key_states
            }
        elif states[0] == 0x02:  # Touchscreen Event
            if states[3] == 1:
                event_type = TouchscreenEventType.SHORT
            elif states[3] == 2:
                event_type = TouchscreenEventType.LONG
            elif states[3] == 3:
                event_type = TouchscreenEventType.DRAG
            else:
                return None

            value = {
                'x': (states[6] << 8) + states[5],
                'y': (states[8] << 8) + states[7]
            }

            if event_type == TouchscreenEventType.DRAG:
                value["x_out"] = (states[10] << 8) + states[9]
                value["y_out"] = (states[12] << 8) + states[11]

            return {
                ControlType.TOUCHSCREEN: (event_type, value),
            }
        elif states[0] == 0x03:  # Dial Event
            if states[3] == 0x01:
                event_type = DialEventType.TURN
            elif states[3] == 0x00:
                event_type = DialEventType.PUSH
            else:
                return None

            values = [self._DIAL_EVENT_TRANSFORM[event_type](s) for s in states[4:4 + self.DIAL_COUNT]]

            return {
                ControlType.DIAL: {
                    event_type: values,
                }
            }

    def set_brightness(self, percent):
        if isinstance(percent, float):
            percent = int(100.0 * percent)

        percent = min(max(percent, 0), 100)

        payload = bytearray(32)
        payload[0:3] = [0x03, 0x08, percent]

        self.device.write_feature(payload)

    def get_serial_number(self):
        serial = self.device.read_feature(0x06, 32)
        return self._extract_string(serial[2:])

    def get_firmware_version(self):
        version = self.device.read_feature(0x05, 32)
        return self._extract_string(version[6:])

    def set_key_image(self, key, image):
        if min(max(key, 0), self.KEY_COUNT) != key:
            raise IndexError("Invalid key index {}.".format(key))

        image = bytes(image or self.BLANK_KEY_IMAGE)

        page_number = 0
        bytes_remaining = len(image)
        while bytes_remaining > 0:
            this_length = min(bytes_remaining, self._KEY_PACKET_PAYLOAD_LEN)

            header = [
                0x02,                                           # 0
                0x07,                                           # 1
                key & 0xff,                                     # 2 key_index
                1 if this_length == bytes_remaining else 0,     # 3 is_last
                this_length & 0xff,                             # 4 bytecount low byte
                (this_length >> 8) & 0xff,                      # 5 bytecount high byte
                page_number & 0xff,                             # 6 pagenumber low byte
                (page_number >> 8) & 0xff,                      # 7 pagenumber high byte
            ]

            bytes_sent = page_number * (self._KEY_PACKET_PAYLOAD_LEN)
            payload = bytes(header) + image[bytes_sent:bytes_sent + this_length]
            padding = bytearray(self._IMG_PACKET_LEN - len(payload))
            self.device.write(payload + padding)
            bytes_remaining = bytes_remaining - this_length
            page_number = page_number + 1

    def set_touchscreen_image(self, image, x_pos=0, y_pos=0, width=0, height=0):
        if not image:
            image = self.BLANK_TOUCHSCREEN_IMAGE
            x_pos = 0
            y_pos = 0
            width = self.TOUCHSCREEN_PIXEL_WIDTH
            height = self.TOUCHSCREEN_PIXEL_HEIGHT

        if min(max(x_pos, 0), self.TOUCHSCREEN_PIXEL_WIDTH) != x_pos:
            raise IndexError("Invalid x position {}.".format(x_pos))

        if min(max(y_pos, 0), self.TOUCHSCREEN_PIXEL_HEIGHT) != y_pos:
            raise IndexError("Invalid y position {}.".format(y_pos))

        if min(max(width, 1), self.TOUCHSCREEN_PIXEL_WIDTH - x_pos) != width:
            raise IndexError("Invalid draw width {}.".format(width))

        if min(max(height, 1), self.TOUCHSCREEN_PIXEL_HEIGHT - y_pos) != height:
            raise IndexError("Invalid draw height {}.".format(height))

        image = bytes(image)

        page_number = 0
        bytes_remaining = len(image)
        while bytes_remaining > 0:
            this_length = min(bytes_remaining, self._LCD_PACKET_PAYLOAD_LEN)
            bytes_sent = page_number * self._LCD_PACKET_PAYLOAD_LEN

            header = [
                0x02,  # 0
                0x0c,  # 1
                x_pos & 0xff,  # 2 xpos low byte
                (x_pos >> 8) & 0xff,  # 3 xpos high byte
                y_pos & 0xff,  # 4 ypos low byte
                (y_pos >> 8) & 0xff,  # 5 ypos high byte
                width & 0xff,  # 6 width low byte
                (width >> 8) & 0xff,  # 7 width high byte
                height & 0xff,  # 8 height low byte
                (height >> 8) & 0xff,  # 9 height high byte
                1 if this_length == bytes_remaining else 0,  # 10 is the last report?
                page_number & 0xff,  # 11 pagenumber low byte
                (page_number >> 8) & 0xff,  # 12 pagenumber high byte
                this_length & 0xff,  # 13 bytecount low byte
                (this_length >> 8) & 0xff,  # 14 bytecount high byte
                0x00,  # 15 padding
            ]

            payload = bytes(header) + image[bytes_sent:bytes_sent + this_length]
            padding = bytearray(self._IMG_PACKET_LEN - len(payload))
            self.device.write(payload + padding)

            bytes_remaining = bytes_remaining - this_length
            page_number = page_number + 1

    def set_key_color(self, key, r, g, b):
        pass

    def set_screen_image(self, image):
        pass
