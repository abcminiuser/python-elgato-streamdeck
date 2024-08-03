#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .Devices.StreamDeckMini import StreamDeckMini
from .Devices.StreamDeckNeo import StreamDeckNeo
from .Devices.StreamDeckOriginal import StreamDeckOriginal
from .Devices.StreamDeckOriginalV2 import StreamDeckOriginalV2
from .Devices.StreamDeckXL import StreamDeckXL
from .Devices.StreamDeckPedal import StreamDeckPedal
from .Devices.StreamDeckPlus import StreamDeckPlus
from .Transport.Dummy import Dummy
from .Transport.LibUSBHIDAPI import LibUSBHIDAPI
from .ProductIDs import USBVendorIDs, USBProductIDs


class ProbeError(Exception):
    """
    Exception thrown when attempting to probe for attached StreamDeck devices,
    but no suitable valid transport was found.
    """

    pass


class DeviceManager:
    """
    Central device manager, to enumerate any attached StreamDeck devices. An
    instance of this class must be created in order to detect and use any
    StreamDeck devices.
    """

    USB_VID_ELGATO = 0x0fd9
    USB_PID_STREAMDECK_ORIGINAL = 0x0060
    USB_PID_STREAMDECK_ORIGINAL_V2 = 0x006d
    USB_PID_STREAMDECK_MINI = 0x0063
    USB_PID_STREAMDECK_NEO = 0x009a
    USB_PID_STREAMDECK_XL = 0x006c
    USB_PID_STREAMDECK_MK2 = 0x0080
    USB_PID_STREAMDECK_PEDAL = 0x0086
    USB_PID_STREAMDECK_PLUS = 0x0084

    @staticmethod
    def _get_transport(transport):
        """
        Creates a new HID transport instance from the given transport back-end
        name. If no specific transport is supplied, an attempt to find an
        installed backend will be made.

        :param str transport: Name of a supported HID transport back-end to use, None to autoprobe.

        :rtype: Transport.* instance
        :return: Instance of a HID Transport class
        """

        transports = {
            "dummy": Dummy,
            "libusb": LibUSBHIDAPI,
        }

        if transport:
            transport_class = transports.get(transport)

            if transport_class is None:
                raise ProbeError("Unknown HID transport backend \"{}\".".format(transport))

            try:
                transport_class.probe()
                return transport_class()
            except Exception as transport_error:
                raise ProbeError("Probe failed on HID backend \"{}\".".format(transport), transport_error)
        else:
            probe_errors = {}

            for transport_name, transport_class in transports.items():
                if transport_name == "dummy":
                    continue

                try:
                    transport_class.probe()
                    return transport_class()
                except Exception as transport_error:
                    probe_errors[transport_name] = transport_error

            raise ProbeError("Probe failed to find any functional HID backend.", probe_errors)

    def __init__(self, transport=None):
        """
        Creates a new StreamDeck DeviceManager, used to detect attached StreamDeck devices.

        :param str transport: name of the the specific HID transport back-end to use, None to auto-probe.
        """
        self.transport = self._get_transport(transport)

    def enumerate(self):
        """
        Detect attached StreamDeck devices.

        :rtype: list(StreamDeck)
        :return: list of :class:`StreamDeck` instances, one for each detected device.
        """

        products = [
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_ORIGINAL, StreamDeckOriginal),
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_ORIGINAL_V2, StreamDeckOriginalV2),
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_MINI, StreamDeckMini),
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_NEO, StreamDeckNeo),
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_XL, StreamDeckXL),
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_MK2, StreamDeckOriginalV2),
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_PEDAL, StreamDeckPedal),
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_MINI_MK2, StreamDeckMini),
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_XL_V2, StreamDeckXL),
            (USBVendorIDs.USB_VID_ELGATO, USBProductIDs.USB_PID_STREAMDECK_PLUS, StreamDeckPlus),
        ]

        streamdecks = list()

        for vid, pid, class_type in products:
            found_devices = self.transport.enumerate(vid=vid, pid=pid)
            streamdecks.extend([class_type(d) for d in found_devices])

        return streamdecks
