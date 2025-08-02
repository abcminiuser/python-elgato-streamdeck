#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from abc import ABC, abstractmethod


class TransportError(Exception):
    """
    Exception thrown when attempting to access a device using a backend
    transport that has failed (for example, if the requested device could not
    be accessed).
    """

    pass


class Transport(ABC):
    """
    Base transport layer, representing an abstract communication back-end which
    can be used to discovery attached StreamDeck devices.
    """

    class Device(ABC):
        """
        Base connection device, representing an abstract connected device which
        can be communicated with by an upper layer high level protocol.
        """

        @abstractmethod
        def open(self) -> None:
            """
            Opens the device for input/output. This must be called prior to
            sending or receiving any reports.

            .. seealso:: See :func:`~Transport.Device.close` for the
                         corresponding close method.
            """
            pass

        @abstractmethod
        def close(self) -> None:
            """
            Closes the device for input/output.

            .. seealso:: See :func:`~~Transport.Device.open` for the
                         corresponding open method.
            """
            pass

        @abstractmethod
        def is_open(self) -> bool:
            """
            Indicates if the physical device object this instance is attached
            to has been opened by the host.

            :rtype: bool
            :return: `True` if the device is open, `False` otherwise.
            """
            pass

        @abstractmethod
        def connected(self) -> bool:
            """
            Indicates if the physical device object this instance is attached
            to is still connected to the host.

            :rtype: bool
            :return: `True` if the device is still connected, `False` otherwise.
            """
            pass

        @abstractmethod
        def path(self) -> str:
            """
            Retrieves the logical path of the attached device within the
            current system. This can be used to uniquely differentiate one
            device from another.

            :rtype: str
            :return: Logical device path for the attached device.
            """
            pass

        @abstractmethod
        def vendor_id(self) -> int:
            """
            Retrieves the vendor ID value of the attached device.

            :rtype: int
            :return: Vendor ID of the attached device.
            """
            pass

        @abstractmethod
        def product_id(self) -> int:
            """
            Retrieves the product ID value of the attached device.

            :rtype: int
            :return: Product ID of the attached device.
            """
            pass

        @abstractmethod
        def write_feature(self, payload: bytes) -> int:
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
        def read_feature(self, report_id: int, length: int) -> bytes:
            """
            Reads a HID Feature report from the open HID device.

            :param int report_id: Report ID of the report being read.
            :param int length: Maximum length of the Feature report to read.

            :rtype: list(byte)
            :return: List of bytes containing the read Feature report. The
                     first byte of the report will be the Report ID of the
                     report that was read.
            """
            pass

        @abstractmethod
        def write(self, payload: bytes) -> int:
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
        def read(self, length: int) -> bytes:
            """
            Performs a blocking read of a HID In report from the open HID device.

            :param int length: Maximum length of the In report to read.

            :rtype: list(byte)
            :return: List of bytes containing the read In report. The first byte
                     of the report will be the Report ID of the report that was
                     read.
            """
            pass

    @staticmethod
    @abstractmethod
    def probe() -> None:
        """
        Attempts to determine if the back-end is installed and usable. It is
        expected that probe failures throw exceptions detailing their exact
        cause of failure.
        """
        pass

    @abstractmethod
    def enumerate(self, vid: int, pid: int) -> list[Device]:
        """
        Enumerates all available devices on the system using the current
        transport back-end.

        :param int vid: USB Vendor ID to filter all devices by, `None` if the
                        device list should not be filtered by vendor.
        :param int pid: USB Product ID to filter all devices by, `None` if the
                        device list should not be filtered by product.

        :rtype: list(Transport.Device)
        :return: List of discovered devices that are available through this
                 transport back-end.
        """
        pass
