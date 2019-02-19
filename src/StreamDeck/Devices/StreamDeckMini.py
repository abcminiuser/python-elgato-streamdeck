#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .StreamDeck import StreamDeck


class StreamDeckMini(StreamDeck):
    """
    Represents a physically attached StreamDeck Mini device.
    """

    KEY_COUNT = 6
    KEY_COLS = 3
    KEY_ROWS = 2

    KEY_PIXEL_WIDTH = 80
    KEY_PIXEL_HEIGHT = 80
    KEY_PIXEL_DEPTH = 3
    KEY_PIXEL_ORDER = "BGR"
    KEY_FLIP = (False, False)
    KEY_ROTATION = 90

    DECK_TYPE = "Stream Deck Mini"

    KEY_IMAGE_SIZE = KEY_PIXEL_WIDTH * KEY_PIXEL_HEIGHT * KEY_PIXEL_DEPTH
    START_PAGE = 0
    REPORT_LENGTH = 1024

    def reset(self):
        """
        Resets the StreamDeck, clearing all button images and showing the
        standby image.
        """

        payload = bytearray(17)
        payload[0:2] = [0x0B, 0x63]
        self.device.write_feature(payload)

    def set_brightness(self, percent):
        """
        Sets the global screen brightness of the ScreenDeck, across all the
        physical buttons.

        :param int/float percent: brightness percent, from [0-100] as an `int`,
                                  or normalized to [0.0-1.0] as a `float`.
        """

        if isinstance(percent, float):
            percent = int(100.0 * percent)

        percent = min(max(percent, 0), 100)

        payload = bytearray(17)
        payload[0:6] = [0x05, 0x55, 0xaa, 0xd1, 0x01, percent]
        self.device.write_feature(payload)

    def set_key_image(self, key, image):
        """
        Sets the image of a button on the StreamDeck to the given image. The
        image being set should be in the correct format for the device, as an
        enumerable collection of pixels.

        .. seealso:: See :func:`~StreamDeck.get_key_image_format` method for
                     information on the image format accepted by the device.

        :param int key: Index of the button whose image is to be updated.
        :param enumerable image: Pixel data of the image to set on the button.
                                 If `None`, the key will be cleared to a black
                                 color.
        """

        image = bytes(image or self.KEY_IMAGE_SIZE)

        if min(max(key, 0), self.KEY_COUNT) != key:
            raise IndexError("Invalid key index {}.".format(key))

        if len(image) != self.KEY_IMAGE_SIZE:
            raise ValueError("Invalid image size {}.".format(len(image)))

        header_1 = [
            0x02, 0x01, self.START_PAGE, 0x00, 0x00, key + 1, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        bmp_header = [
            0x42, 0x4d, 0xf6, 0x3c, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x36, 0x00, 0x00, 0x00, 0x28, 0x00,
            0x00, 0x00, 0x48, 0x00, 0x00, 0x00, 0x48, 0x00,
            0x00, 0x00, 0x01, 0x00, 0x18, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xc0, 0x3c, 0x00, 0x00, 0xc4, 0x0e,
            0x00, 0x00, 0xc4, 0x0e, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        # Lengths remaining after headers are added
        IMAGE_BYTES_FIRST_PAGE = self.REPORT_LENGTH - len(header_1) - len(bmp_header)
        IMAGE_BYTES_FOLLOWUP_PAGES = self.REPORT_LENGTH - len(header_1)

        # Bytes of data to fit into pages after the first
        remaining_bytes = len(image) - IMAGE_BYTES_FIRST_PAGE

        # Bytes leftover after the last full page
        leftovers = remaining_bytes % IMAGE_BYTES_FOLLOWUP_PAGES

        # Calc number of followup pages and add leftover partial page (if any)
        pages = (remaining_bytes // IMAGE_BYTES_FOLLOWUP_PAGES) + (leftovers != 0)

        # Generate first report
        payload_first = bytes(header_1) + bytes(bmp_header) + image[: IMAGE_BYTES_FIRST_PAGE]
        self.device.write(payload_first)

        # Initialize the slicing variable to the end of the first page
        last_slice_end = IMAGE_BYTES_FIRST_PAGE

        # Generate followup pages
        for report_page in range(self.START_PAGE + 1, pages):
            # Byte 3 is page number, byte 5 indicates followup, byte 6 is keynumber to update
            header_followup = [
                0x02, 0x01, report_page, 0x00, 0x01, key + 1, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

            # Figure out where to stop pulling data from the image for this page
            if (report_page == pages - 1) and (leftovers != 0):
                payload_end = last_slice_end + leftovers
            else:
                payload_end = last_slice_end + IMAGE_BYTES_FOLLOWUP_PAGES

            # Generate followup payload
            payload_next = bytes(header_followup) + image[last_slice_end:payload_end]
            self.device.write(payload_next)

            # Update slicing variable
            last_slice_end = payload_end
