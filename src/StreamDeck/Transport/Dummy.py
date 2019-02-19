#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .Transport import Transport


class Dummy(Transport):
    """
    Dummy transport layer, for testing.
    """

    class Device(Transport.Device):
        def open(self):
            pass

        def close(self):
            pass

        def connected(self):
            return True

        def path(self):
            return "/?"

        def write_feature(self, payload):
            return True

        def write(self, payload):
            return True

        def read(self, length):
            return None

    def enumerate(self, vid, pid):
        return [Dummy.Device()]
