#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import binascii
import logging

from .Transport import Transport, TransportError

logger = logging.getLogger(__name__)


class Dummy(Transport):
    """
    Dummy transport layer, for testing.
    """

    class Device(Transport.Device):
        def __init__(self, vid, pid):
            self._vid = vid
            self._pid = pid
            self._id = f"{vid}:{pid}"
            self._open = False

        def open(self):
            if self._open:
                return

            logger.info("Deck opened")
            self._open = True

        def close(self):
            if not self._open:
                return

            logger.info("Deck closed")
            self._open = False

        def is_open(self):
            return self._open

        def connected(self):
            return True

        def vendor_id(self):
            return self._vid

        def product_id(self):
            return self._pid

        def path(self):
            return self._id

        def write_feature(self, payload):
            if not self._open:
                raise TransportError("Deck feature write while deck not open.")

            logger.info(
                "Deck feature write (length %s):\n%s",
                len(payload),
                binascii.hexlify(payload, " ").decode("utf-8"),
            )
            return True

        def read_feature(self, report_id, length):
            if not self._open:
                raise TransportError("Deck feature read while deck not open.")

            logger.info("Deck feature read (length %s)", length)
            return bytes(length)

        def write(self, payload):
            if not self._open:
                raise TransportError("Deck write while deck not open.")

            logger.info(
                "Deck report write (length %s):\n%s",
                len(payload),
                binascii.hexlify(payload, " ").decode("utf-8"),
            )
            return True

        def read(self, length):
            if not self._open:
                raise TransportError("Deck read while deck not open.")

            logger.info("Deck report read (length %s)", length)
            return bytes(length)

    @staticmethod
    def probe():
        pass

    def enumerate(self, vid, pid):
        return [Dummy.Device(vid=vid, pid=pid)]
