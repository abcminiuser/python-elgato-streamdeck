#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import io


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

    return Image.new("RGB", image_format['size'], background)


def load_scaled_image(deck, image_path, background='black'):
    """
    Loads an image from image_path and scales it to fit the given StreamDeck
    device's keys, and centers it.

    .. seealso:: See :func:`~PILHelper.to_native_format` method for converting a
                 PIL image instance to the native image format of a given
                 StreamDeck device

    :rtrype: PIL.Image
    :return: Loaded PIL image scaled and centered
    """
    from PIL import Image

    image = create_image(deck, background=background)

    # Resize the source image asset to best-fit the dimensions of a single key,
    # and paste it onto our blank frame centered as closely as possible.
    icon = Image.open(image_path).convert("RGBA")
    icon.thumbnail((image.width, image.height), Image.LANCZOS)
    icon_pos = ((image.width - icon.width) // 2, (image.height - icon.height) // 2)
    image.paste(icon, icon_pos, icon)

    return image


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

    if image.size != image_format['size']:
        image.thumbnail(image_format['size'])

    # We want a compressed image in a given codec, convert.
    compressed_image = io.BytesIO()
    image.save(compressed_image, image_format['format'], quality=100)
    return compressed_image.getbuffer()
