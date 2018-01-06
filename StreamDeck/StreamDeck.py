#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import threading


class DeviceManager(object):
    USB_VID_ELGATO = 0x0fd9
    USB_PID_STREAMDECK = 0x0060

    def _get_transport(self, transport):
        if transport == "hidapi":
            from .Transport.HIDAPI import HIDAPI
            return HIDAPI()
        else:
            raise IOError("Invalid HID transport backend \"{}\".".format(transport))

    def __init__(self, transport="hidapi"):
        self.transport = self._get_transport(transport)

    def enumerate(self):
        deck_devices = self.transport.enumerate(
            vid=self.USB_VID_ELGATO, pid=self.USB_PID_STREAMDECK)
        return [StreamDeck(d) for d in deck_devices]


class StreamDeck(object):
    KEY_COUNT = 15
    KEY_COLS = 5
    KEY_ROWS = 3

    KEY_PIXEL_WIDTH = 72
    KEY_PIXEL_HEIGHT = 72
    KEY_PIXEL_DEPTH = 3
    KEY_PIXEL_ORDER = "BGR"

    KEY_IMAGE_SIZE = KEY_PIXEL_WIDTH * KEY_PIXEL_HEIGHT * KEY_PIXEL_DEPTH

    def __init__(self, device):
        self.device = device
        self.last_key_states = [False] * self.KEY_COUNT
        self.read_thread = None
        self.key_callback = None

    def __del__(self):
        try:
            self._setup_reader(None)

            self.device.close()
        except:
            pass

    def _read(self):
        while self.read_thread_run:
            payload = self.device.read(17)

            if len(payload):
                new_key_states = [bool(s) for s in payload[1:]]

                if self.key_callback is not None:
                    for k, (old, new) in enumerate(zip(self.last_key_states, new_key_states)):
                        if old != new:
                            self.key_callback(self, k, new)

                self.last_key_states = new_key_states

    def _setup_reader(self, callback):
        if self.read_thread is not None:
            self.read_thread_run = False
            self.read_thread.join()

        if callback is not None:
            self.read_thread_run = True
            self.read_thread = threading.Thread(target=callback)
            self.read_thread.start()

    def open(self):
        self.device.open()
        self._setup_reader(self._read)

    def close(self):
        self.device.close()

    def connected(self):
        return self.device.connected()

    def id(self):
        return self.device.path()

    def key_count(self):
        return self.KEY_COUNT

    def key_layout(self):
        return (self.KEY_ROWS, self.KEY_COLS)

    def key_image_format(self):
        return {
            "width": self.KEY_PIXEL_WIDTH,
            "height": self.KEY_PIXEL_HEIGHT,
            "depth": self.KEY_PIXEL_DEPTH,
            "order": self.KEY_PIXEL_ORDER,
        }

    def set_brightness(self, percent):
        percent = min(max(percent, 0), 100)

        payload = bytearray(17)
        payload[0:6] = [0x05, 0x55, 0xaa, 0xd1, 0x01, percent]
        self.device.write_feature(payload)

    def set_key_image(self, key, image):
        if min(max(key, 0), self.KEY_COUNT) != key:
            raise IndexError("Invalid key index {}.".format(key))

        if len(image) != self.KEY_IMAGE_SIZE:
            raise ValueError("Invalid image size {}.".format(len(image)))

        payload = bytearray(8191)

        PAYLOAD_LEN_1 = 2583 * 3
        PAYLOAD_LEN_2 = 2601 * 3

        header = [
            0x02, 0x01, 0x01, 0x00, 0x00, key + 1, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x42, 0x4d, 0xf6, 0x3c, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x36, 0x00, 0x00, 0x00, 0x28, 0x00,
            0x00, 0x00, 0x48, 0x00, 0x00, 0x00, 0x48, 0x00,
            0x00, 0x00, 0x01, 0x00, 0x18, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xc0, 0x3c, 0x00, 0x00, 0xc4, 0x0e,
            0x00, 0x00, 0xc4, 0x0e, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]
        payload[0: len(header)] = header
        payload[len(header): len(header) + PAYLOAD_LEN_1] = \
            image[0: PAYLOAD_LEN_1]
        self.device.write(payload)

        header = [
            0x02, 0x01, 0x02, 0x00, 0x01, key + 1, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]
        payload[0: len(header)] = header
        payload[len(header): len(header) + PAYLOAD_LEN_2] = \
            image[PAYLOAD_LEN_1: PAYLOAD_LEN_1 + PAYLOAD_LEN_2]
        self.device.write(payload)

    def set_key_callback(self, callback):
        self.key_callback = callback

    def key_states(self):
        return self.last_key_states
