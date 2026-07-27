#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Stream Deck + XL support.
#
# Implemented directly from Elgato's official "Stream Deck HID API" maker
# documentation:
#   General reference: https://docs.elgato.com/streamdeck/hid/general
#   Device specific:    https://docs.elgato.com/streamdeck/hid/stream-deck-plus-xl
#
# Summary of the device, per that documentation:
#   - VID 0x0FD9, PID 0x00C6
#   - 36 keys, arranged as a 9 (cols) x 4 (rows) matrix
#   - 6 rotary encoders ("dials"), each with a push button
#   - A touch-capable window strip (1200 x 100 px, logical/pre-rotation)
#   - A full LCD panel behind the keys (1280 x 800 px, logical/pre-rotation)
#   - Button images, the window image and the full screen image must all be
#     rotated 90 degrees counter-clockwise before being JPEG-encoded and sent

from .StreamDeck import StreamDeck, ControlType, DialEventType, TouchscreenEventType
from ..ImageHelpers import PILHelper


def _dials_rotation_transform(value):
    """
    Converts an unsigned byte (0-255) read off the wire into a signed tick
    count, matching the device's documented INT8 encoder delta: positive for
    clockwise ticks, negative for counter-clockwise ticks.
    """
    if value < 0x80:
        return value
    else:
        return -(0x100 - value)


class StreamDeckPlusXL(StreamDeck):
    """
    Represents a physically attached Stream Deck + XL device.
    """

    KEY_COUNT = 36
    KEY_COLS = 9
    KEY_ROWS = 4

    DIAL_COUNT = 6

    # Button image: 112 x 112 px, rotated 90 degrees CCW before upload.
    KEY_PIXEL_WIDTH = 112
    KEY_PIXEL_HEIGHT = 112
    KEY_IMAGE_FORMAT = "JPEG"
    KEY_FLIP = (False, False)
    KEY_ROTATION = 90

    DECK_TYPE = "Stream Deck + XL"
    DECK_VISUAL = True
    DECK_TOUCH = True

    # Touchscreen "window" strip: 1200 x 100 px (logical, pre-rotation),
    # rotated 90 degrees CCW before upload.
    TOUCHSCREEN_PIXEL_WIDTH = 1200
    TOUCHSCREEN_PIXEL_HEIGHT = 100
    TOUCHSCREEN_IMAGE_FORMAT = "JPEG"
    TOUCHSCREEN_FLIP = (False, False)
    TOUCHSCREEN_ROTATION = 90

    # Full LCD panel behind the keys: 1280 x 800 px (logical, pre-rotation),
    # rotated 90 degrees CCW before upload.
    SCREEN_PIXEL_WIDTH = 1280
    SCREEN_PIXEL_HEIGHT = 800
    SCREEN_IMAGE_FORMAT = "JPEG"
    SCREEN_FLIP = (False, False)
    SCREEN_ROTATION = 90

    _IMG_PACKET_LEN = 1024  # Max size for a data packet when setting images

    _KEY_PACKET_HEADER = 8
    _SCREEN_PACKET_HEADER = 8
    _LCD_PACKET_HEADER = 16

    _KEY_PACKET_PAYLOAD_LEN = _IMG_PACKET_LEN - _KEY_PACKET_HEADER
    _SCREEN_PACKET_PAYLOAD_LEN = _IMG_PACKET_LEN - _SCREEN_PACKET_HEADER
    _LCD_PACKET_PAYLOAD_LEN = _IMG_PACKET_LEN - _LCD_PACKET_HEADER

    _DIAL_EVENT_TRANSFORM = {
        DialEventType.TURN: _dials_rotation_transform,
        DialEventType.PUSH: bool,
    }

    def __init__(self, device):
        super().__init__(device)

        # Generated dynamically (instead of a hardcoded byte array like the
        # older devices use) since they run through the same rotation/format
        # pipeline as any other image set via this library, guaranteeing they
        # are always correct for this device's declared image formats.
        self.BLANK_KEY_IMAGE = PILHelper.to_native_key_format(
            self, PILHelper.create_key_image(self, "black")
        )
        self.BLANK_TOUCHSCREEN_IMAGE = PILHelper.to_native_touchscreen_format(
            self, PILHelper.create_touchscreen_image(self, "black")
        )
        self.BLANK_SCREEN_IMAGE = PILHelper.to_native_screen_format(
            self, PILHelper.create_screen_image(self, "black")
        )

    def _reset_key_stream(self):
        payload = bytearray(self._IMG_PACKET_LEN)
        payload[0] = 0x02
        self.device.write(payload)

    def reset(self):
        # Show Logo (Report ID 0x03, Command 0x02)
        payload = bytearray(32)
        payload[0:2] = [0x03, 0x02]
        self.device.write_feature(payload)

    def _read_control_states(self):
        # Large enough to cover the biggest input report we handle: report
        # ID (1) + command (1) + payload length (2) + one byte per key (36).
        states = self.device.read(4 + self.KEY_COUNT)
        if states is None:
            return None

        # Strip the leading Report ID byte, so states[0] is now the Command.
        states = states[1:]

        command = states[0]

        if command == 0x00:  # Key / Button Press State Change
            new_key_states = [bool(s) for s in states[3:3 + self.KEY_COUNT]]
            return {
                ControlType.KEY: new_key_states
            }
        elif command == 0x02:  # Touch Screen Activity
            contents_type = states[3]

            if contents_type == 0x01:
                event_type = TouchscreenEventType.SHORT  # TAP
            elif contents_type == 0x02:
                event_type = TouchscreenEventType.LONG  # PRESS
            elif contents_type == 0x03:
                event_type = TouchscreenEventType.DRAG  # FLICK
            else:
                return None

            value = {
                'x': (states[6] << 8) + states[5],
                'y': (states[8] << 8) + states[7],
            }

            if event_type == TouchscreenEventType.DRAG:
                value["x_out"] = (states[10] << 8) + states[9]
                value["y_out"] = (states[12] << 8) + states[11]

            return {
                ControlType.TOUCHSCREEN: (event_type, value),
            }
        elif command == 0x03:  # Encoders State Change
            contents_type = states[3]

            if contents_type == 0x01:
                event_type = DialEventType.TURN  # ROTATE
            elif contents_type == 0x00:
                event_type = DialEventType.PUSH  # BTN
            else:
                return None

            values = [self._DIAL_EVENT_TRANSFORM[event_type](s) for s in states[4:4 + self.DIAL_COUNT]]

            return {
                ControlType.DIAL: {
                    event_type: values,
                }
            }

        return None

    def set_brightness(self, percent):
        if isinstance(percent, float):
            percent = int(100.0 * percent)

        percent = min(max(percent, 0), 100)

        # Set Backlight Brightness (Report ID 0x03, Command 0x08)
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
        if min(max(key, 0), self.KEY_COUNT - 1) != key:
            raise IndexError("Invalid key index {}.".format(key))

        image = bytes(image or self.BLANK_KEY_IMAGE)

        page_number = 0
        bytes_remaining = len(image)
        while bytes_remaining > 0:
            this_length = min(bytes_remaining, self._KEY_PACKET_PAYLOAD_LEN)
            bytes_sent = page_number * self._KEY_PACKET_PAYLOAD_LEN

            # Update Button Image (Report ID 0x02, Command 0x07)
            header = [
                0x02,
                0x07,
                key & 0xff,
                1 if this_length == bytes_remaining else 0,
                this_length & 0xff,
                (this_length >> 8) & 0xff,
                page_number & 0xff,
                (page_number >> 8) & 0xff,
            ]

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

        # NOTE: x_pos/y_pos/width/height are "logical" coordinates (i.e. in
        # the pre-rotation 1200x100 space), per Elgato's documentation. The
        # image bytes passed in must already be rotated/encoded (this is what
        # PILHelper.to_native_touchscreen_format does for you).
        image = bytes(image)

        page_number = 0
        bytes_remaining = len(image)
        while bytes_remaining > 0:
            this_length = min(bytes_remaining, self._LCD_PACKET_PAYLOAD_LEN)
            bytes_sent = page_number * self._LCD_PACKET_PAYLOAD_LEN

            # Update Partial Window Image (Report ID 0x02, Command 0x0C)
            header = [
                0x02,
                0x0c,
                x_pos & 0xff,
                (x_pos >> 8) & 0xff,
                y_pos & 0xff,
                (y_pos >> 8) & 0xff,
                width & 0xff,
                (width >> 8) & 0xff,
                height & 0xff,
                (height >> 8) & 0xff,
                1 if this_length == bytes_remaining else 0,
                page_number & 0xff,
                (page_number >> 8) & 0xff,
                this_length & 0xff,
                (this_length >> 8) & 0xff,
                0x00,
            ]

            payload = bytes(header) + image[bytes_sent:bytes_sent + this_length]
            padding = bytearray(self._IMG_PACKET_LEN - len(payload))
            self.device.write(payload + padding)

            bytes_remaining = bytes_remaining - this_length
            page_number = page_number + 1

    def set_key_color(self, key, r, g, b):
        if min(max(key, 0), self.KEY_COUNT - 1) != key:
            raise IndexError("Invalid key index {}.".format(key))

        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError("Invalid color")

        # Fill Key / Button with Color (Report ID 0x03, Command 0x06)
        payload = bytearray(32)
        payload[0:6] = [0x03, 0x06, key, r, g, b]
        self.device.write_feature(payload)

    def set_screen_image(self, image):
        if not image:
            image = self.BLANK_SCREEN_IMAGE

        image = bytes(image)

        page_number = 0
        bytes_remaining = len(image)
        while bytes_remaining > 0:
            this_length = min(bytes_remaining, self._SCREEN_PACKET_PAYLOAD_LEN)
            bytes_sent = page_number * self._SCREEN_PACKET_PAYLOAD_LEN

            # Update Full Screen Image (Report ID 0x02, Command 0x08)
            header = [
                0x02,
                0x08,
                0x00,
                1 if this_length == bytes_remaining else 0,
                this_length & 0xff,
                (this_length >> 8) & 0xff,
                page_number & 0xff,
                (page_number >> 8) & 0xff,
            ]

            payload = bytes(header) + image[bytes_sent:bytes_sent + this_length]
            padding = bytearray(self._IMG_PACKET_LEN - len(payload))
            self.device.write(payload + padding)

            bytes_remaining = bytes_remaining - this_length
            page_number = page_number + 1
