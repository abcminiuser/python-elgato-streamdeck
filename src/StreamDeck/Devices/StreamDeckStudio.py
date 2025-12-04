#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .StreamDeck import ControlType, DialEventType, StreamDeck
from ..ImageHelpers import PILHelper


def _dials_rotation_transform(value):
    if value < 0x80:
        # Clockwise rotation
        return value
    else:
        # Counterclockwise rotation
        return -(0x100 - value)


class StreamDeckStudio(StreamDeck):
    KEY_COUNT = 32
    KEY_COLS = 16
    KEY_ROWS = 2

    DIAL_COUNT = 2

    KEY_PIXEL_WIDTH = 80
    KEY_PIXEL_HEIGHT = 120
    KEY_IMAGE_FORMAT = "JPEG"
    KEY_FLIP = (False, False)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck Studio"
    DECK_VISUAL = True

    _HID_INPUT_REPORT = 0x01
    _HID_OUTPUT_REPORT_ID = 0x02

    _DIAL_RING_CMD = 0x0F
    _DIAL_KNOB_CMD = 0x10
    _DIAL_RING_SEGMENTS = 24

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

    def _reset_key_stream(self):
        payload = bytearray(self._IMG_PACKET_LEN)
        payload[0] = self._HID_OUTPUT_REPORT_ID
        self.device.write(payload)

    def reset(self):
        payload = bytearray(32)
        payload[0:2] = [0x03, 0x02]
        self.device.write_feature(payload)

    def _read_control_states(self):
        states = self.device.read(43)

        if states is None:
            return None

        states = states[1:]

        if states[0] == 0x00:
            return self._parse_key_event(states)
        elif states[0] == 0x03:
            return self._parse_dial_event(states)

        return None

    def _parse_key_event(self, states):
        new_key_states = [bool(s) for s in states[3:35]]
        return {ControlType.KEY: new_key_states}

    def _parse_dial_event(self, states):
        if states[3] == 0x01:
            event_type = DialEventType.TURN
        elif states[3] == 0x00:
            event_type = DialEventType.PUSH
        else:
            return None

        values = [
            self._DIAL_EVENT_TRANSFORM[event_type](s)
            for s in states[4:4 + self.DIAL_COUNT]
        ]

        return {ControlType.DIAL: {event_type: values}}

    def set_brightness(self, percent):
        if isinstance(percent, float):
            percent = int(100.0 * percent)

        percent = max(0, min(percent, 100))

        payload = bytearray(32)
        payload[0:3] = [0x03, 0x08, percent]

        self.device.write_feature(payload)

    def get_serial_number(self):
        serial = self.device.read_feature(0x06, 32)
        return self._extract_string(serial[5:])

    def get_firmware_version(self):
        version = self.device.read_feature(0x05, 32)
        return self._extract_string(version[5:])

    def set_key_image(self, key, image):
        if not 0 <= key < self.KEY_COUNT:
            raise IndexError(f"Invalid key index {key}.")

        image = bytes(image or self.BLANK_KEY_IMAGE)

        page_number = 0
        bytes_remaining = len(image)

        while bytes_remaining > 0:
            this_length = min(bytes_remaining, self._KEY_PACKET_PAYLOAD_LEN)
            is_last = 1 if this_length == bytes_remaining else 0

            header = [
                self._HID_OUTPUT_REPORT_ID,
                0x07,
                key & 0xFF,  # key index
                is_last,
                this_length & 0xFF,  # bytecount low byte
                (this_length >> 8) & 0xFF,  # bytecount high byte
                page_number & 0xFF,  # page number low byte
                (page_number >> 8) & 0xFF,  # page number high byte
            ]

            bytes_sent = page_number * self._KEY_PACKET_PAYLOAD_LEN
            payload = bytes(header) + image[bytes_sent:bytes_sent + this_length]
            padding = bytearray(self._IMG_PACKET_LEN - len(payload))
            self.device.write(payload + padding)

            bytes_remaining -= this_length
            page_number += 1

    def set_touchscreen_image(self, image, x_pos=0, y_pos=0, width=0, height=0):
        pass

    def set_key_color(self, key, r, g, b):
        pass

    def set_screen_image(self, image):
        pass

    def set_encoder_knob_color(self, encoder, rgb):
        data = [
            self._HID_OUTPUT_REPORT_ID,
            self._DIAL_KNOB_CMD,
            encoder,
            rgb[0], rgb[1], rgb[2],
        ]
        self.device.write(bytes(data))

    def set_encoder_ring_color(self, encoder, rgb):
        data = [
            self._HID_OUTPUT_REPORT_ID,
            self._DIAL_RING_CMD,
            encoder,
        ] + [rgb[0], rgb[1], rgb[2]] * self._DIAL_RING_SEGMENTS
        self.device.write(bytes(data))

    def set_encoder_ring_percentage(
            self, encoder, rgb, value, segment_count=21):
        """
        Sets the color of a portion of the encoder ring based on a percentage
        value.
        Args:
            encoder (int): The encoder index (0 or 1).
            rgb (tuple): A tuple of (R, G, B) values for the color.
            value (int): The percentage value (0-100) to fill the ring.
            segment_count (int): The number of segments to light up for 100%
                (default is 21).
        """
        if not 0 < segment_count <= self._DIAL_RING_SEGMENTS:
            raise ValueError(
                f"Invalid segment count {segment_count}, "
                f"must be between 1 and {self._DIAL_RING_SEGMENTS}."
            )

        segments = round(value * segment_count / 100.0)
        led_data = (
            list(rgb) * segments + [0, 0, 0] * (self._DIAL_RING_SEGMENTS - segments)
        )

        if encoder == 0:
            offset = self._DIAL_RING_SEGMENTS * 3 // 2
            led_data = led_data[offset:] + led_data[:offset]

        data = [self._HID_OUTPUT_REPORT_ID, self._DIAL_RING_CMD, encoder] + led_data
        self.device.write(bytes(data))
