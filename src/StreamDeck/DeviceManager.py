#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .Devices.StreamDeckOriginal import StreamDeckOriginal
from .Devices.StreamDeckMini import StreamDeckMini


class DeviceManager(object):
    """
    Central device manager, to enumerate any attached StreamDeck devices. An
    instance of this class must be created in order to detect and use any
    StreamDeck devices.
    """

    USB_VID_ELGATO = 0x0fd9
    USB_PID_STREAMDECK_ORIGINAL = 0x0060
    USB_PID_STREAMDECK_MINI = 0x0063

    @staticmethod
    def _get_transport(transport):
        """
        Creates a new HID transport instance from the given transport back-end
        name.

        :param str transport: Name of a supported HID transport back-end to use.

        :rtype: Transport.* instance
        :return: Instance of a HID Transport class
        """
        if transport == "hidapi":
            from .Transport.HIDAPI import HIDAPI
            return HIDAPI()
        else:
            raise IOError("Invalid HID transport backend \"{}\".".format(transport))

    def __init__(self, transport="hidapi"):
        """
        Creates a new StreamDeck DeviceManager, used to detect attached StreamDeck devices.

        :param str transport: name of the the HID transport backend to use
        """
        self.transport = self._get_transport(transport)

    def enumerate(self):
        """
        Detect attached StreamDeck devices.

        :rtype: list(StreamDeck)
        :return: list of :class:`StreamDeck` instances, one for each detected device.
        """

        streamdeck_devices = self.transport.enumerate(
            vid=self.USB_VID_ELGATO, pid=self.USB_PID_STREAMDECK_ORIGINAL)
        streamdeckmini_devices = self.transport.enumerate(
            vid=self.USB_VID_ELGATO, pid=self.USB_PID_STREAMDECK_MINI)

        return ([StreamDeckOriginal(d) for d in streamdeck_devices], [StreamDeckMini(m) for m in streamdeckmini_devices])
