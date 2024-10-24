#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .StreamDeck import StreamDeck, ControlType


class StreamDeckPedal(StreamDeck):
    """
    Represents a physically attached StreamDeck Pedal device.
    """

    KEY_COUNT = 3
    KEY_COLS = 3
    KEY_ROWS = 1

    DECK_TYPE = "Stream Deck Pedal"
    DECK_VISUAL = False

    def _read_control_states(self):
        states = self.device.read(4 + self.KEY_COUNT)
        if states is None:
            return None

        states = states[4:]
        return {
            ControlType.KEY: [bool(s) for s in states]
        }

    def _reset_key_stream(self):
        pass

    def reset(self):
        pass

    def set_brightness(self, percent):
        pass

    def get_serial_number(self):
        serial = self.device.read_feature(0x06, 32)
        return self._extract_string(serial[2:])

    def get_firmware_version(self):
        version = self.device.read_feature(0x05, 32)
        return self._extract_string(version[6:])

    def set_key_image(self, key, image):
        pass

    def set_touchscreen_image(self, image, x_pos=0, y_pos=0, width=0, height=0):
        pass

    def set_key_color(self, key, r, g, b):
        pass

    def set_screen_image(self, image):
        pass
