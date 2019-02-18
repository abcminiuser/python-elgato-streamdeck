#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from abc import ABC, abstractmethod


class Transport(ABC):
    class Device(ABC):
        @abstractmethod
        def open(self):
            """
            Opens the HID device for input/output. This must be called prior to
            sending or receiving any HID reports.

            .. seealso:: See :func:`~Transport.Device.close` for the corresponding
                         close method.
            """
            pass

        @abstractmethod
        def close(self):
            """
            Closes the HID device for input/output.

            .. seealso:: See :func:`~~Transport.Device.open` for the corresponding
                         open method.
            """
            pass

        @abstractmethod
        def connected(self):
            """
            Indicates if the physical HID device this instance is attached to
            is still connected to the host.

            :rtype: bool
            :return: `True` if the device is still connected, `False` otherwise.
            """
            pass

        @abstractmethod
        def path(self):
            """
            Retrieves the logical path of the attached HID device within the
            current system. This can be used to differentiate one HID device
            from another.

            :rtype: str
            :return: Logical device path for the attached device.
            """
            pass

        @abstractmethod
        def write_feature(self, payload):
            """
            Sends a HID Feature report to the open HID device.

            :param enumerable() payload: Enumerate list of bytes to send to the
                                         device, as a feature report. The first
                                         byte of the report should be the Report
                                         ID of the report being sent.

            :rtype: int
            :return: Number of bytes successfully sent to the device.
            """
            pass

        @abstractmethod
        def write(self, payload):
            """
            Sends a HID Out report to the open HID device.

            :param enumerable() payload: Enumerate list of bytes to send to the
                                         device, as an Out report. The first
                                         byte of the report should be the Report
                                         ID of the report being sent.

            :rtype: int
            :return: Number of bytes successfully sent to the device.
            """
            pass

        @abstractmethod
        def read(self, length):
            """
            Performs a blocking read of a HID In report from the open HID device.

            :param int length: Maximum length of the In report to read.

            :rtype: list()
            :return: List of bytes containing the read In report. The first byte
                     of the report will be the Report ID of the report that was
                     read.
            """
            pass

    @abstractmethod
    def enumerate(self, vid, pid):
        """
        Enumerates all available USB HID devices on the system.

        :param int vid: USB Vendor ID to filter all devices by, `None` if the
                        device list should not be filtered by vendor.
        :param int pid: USB Product ID to filter all devices by, `None` if the
                        device list should not be filtered by product.

        :rtype: list(Transport.Device)
        :return: List of discovered USB HID devices.
        """
        pass
