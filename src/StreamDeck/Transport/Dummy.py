#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import logging
import binascii

from .Transport import Transport


class Dummy(Transport):
    """
    Dummy transport layer, for testing.
    """

    class Device(Transport.Device):
        def __init__(self, device_id):
            self.id = device_id

        def open(self):
            logging.info('Deck opened')

        def close(self):
            logging.info('Deck closed')

        def connected(self):
            return True

        def path(self):
            return self.id

        def write_feature(self, payload):
            logging.info('Deck feature write (length %s): %s', len(payload), binascii.hexlify(payload))
            return True

        def read_feature(self, report_id, length):
            logging.info('Deck feature read (length %s)', length)
            raise IOError("Dummy device!")

        def write(self, payload):
            logging.info('Deck report write (length %s): %s', len(payload), binascii.hexlify(payload))
            return True

        def read(self, length):
            logging.info('Deck report read (length %s)', length)
            raise IOError("Dummy device!")

    @staticmethod
    def probe():
        pass

    def enumerate(self, vid, pid):
        return [Dummy.Device("{}:{}".format(vid, pid))]
