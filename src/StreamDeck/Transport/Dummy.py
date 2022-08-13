#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import binascii
import logging

from .Transport import Transport, TransportError


class Dummy(Transport):
    """
    Dummy transport layer, for testing.
    """

    class Device(Transport.Device):
        def __init__(self, vid, pid):
            self.vid = vid
            self.pid = pid
            self.id = "{}:{}".format(vid, pid)
            self.is_open = False

        def open(self):
            if self.is_open:
                return

            logging.info("Deck opened")
            self.is_open = True

        def close(self):
            if not self.is_open:
                return

            logging.info("Deck closed")
            self.is_open = False

        def is_open(self):
            return True

        def connected(self):
            return True

        def vendor_id(self):
            return self.vid

        def product_id(self):
            return self.pid

        def path(self):
            return self.id

        def write_feature(self, payload):
            if not self.is_open:
                raise TransportError("Deck feature write while deck not open.")

            logging.info("Deck feature write (length %s):\n%s", len(payload), binascii.hexlify(payload, ' ').decode('utf-8'))
            return True

        def read_feature(self, report_id, length):
            if not self.is_open:
                raise TransportError("Deck feature read while deck not open.")

            logging.info("Deck feature read (length %s)", length)
            return bytearray(length)

        def write(self, payload):
            if not self.is_open:
                raise TransportError("Deck write while deck not open.")

            logging.info("Deck report write (length %s):\n%s", len(payload), binascii.hexlify(payload, ' ').decode('utf-8'))
            return True

        def read(self, length):
            if not self.is_open:
                raise TransportError("Deck read while deck not open.")

            logging.info("Deck report read (length %s)", length)
            return bytearray(length)

    @staticmethod
    def probe():
        pass

    def enumerate(self, vid, pid):
        return [Dummy.Device(vid=vid, pid=pid)]
