#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#


def create_image(deck, background='black'):
    """
    Creates a new PIL Image with the correct image dimensions for the given
    StreamDeck device's keys.

    .. seealso:: See :func:`~PILHelper.to_native_format` method for converting a
                 PIL image instance to the native image format of a given
                 StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible image for.
    :param str background: Background color to use, compatible with `PIL.Image.new()`.

    :rtype: PIL.Image
    :return: Created PIL image
    """
    from PIL import Image

    image_format = deck.key_image_format()

    dimensions = (image_format['width'], image_format['height'])
    return Image.new("RGB", dimensions, background)


def to_native_format(deck, image):
    """
    Converts a given PIL image to the native image format for a StreamDeck,
    suitable for passing to :func:`~StreamDeck.set_key_image`.

    .. seealso:: See :func:`~PILHelper.create_image` method for creating a PIL
                 image instance for a given StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible native image for.
    :param PIL.Image image: PIL Image to convert to the native StreamDeck image format

    :rtype: enumerable()
    :return: Image converted to the given StreamDeck's native format
    """
    from PIL import Image

    image_format = deck.key_image_format()

    if image_format['rotation']:
        image = image.rotate(image_format['rotation'])

    if image_format['flip'][0]:
        image = image.transpose(Image.FLIP_LEFT_RIGHT)

    if image_format['flip'][1]:
        image = image.transpose(Image.FLIP_TOP_BOTTOM)

    # Get the raw r, g and b components of the generated image
    r, g, b = image.split()

    # Recombine the B, G and R elements in the order the display expects
    # them, and convert the resulting image to a sequence of bytes
    rgb = {"R": r, "G": g, "B": b}
    return Image.merge("RGB", [rgb[c] for c in image_format['order']]).tobytes()
