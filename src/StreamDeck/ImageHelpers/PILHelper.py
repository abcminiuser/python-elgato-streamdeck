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


def create_scaled_image(deck, image, margins=[0, 0, 0, 0], background='black'):
    """
    Creates a new key image that contains a scaled version of a given image,
    resized to best fit the given StreamDeck device's keys with the given
    margins around each side.

    The scaled image is centered within the new key image, offset by the given
    margins. The aspect ratio of the image is preserved.

    .. seealso:: See :func:`~PILHelper.to_native_format` method for converting a
                 PIL image instance to the native image format of a given
                 StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible image for.
    :param Image image: PIL Image object to scale
    :param list(int): Array of margin pixels in (top, right, bottom, left) order.
    :param str background: Background color to use, compatible with `PIL.Image.new()`.

    :rtrype: PIL.Image
    :return: Loaded PIL image scaled and centered
    """
    from PIL import Image

    if len(margins) != 4:
        raise ValueError("Margins should be given as an array of four integers.")

    final_image = create_image(deck, background=background)

    thumbnail_max_width = final_image.width - (margins[1] + margins[3])
    thumbnail_max_height = final_image.height - (margins[0] + margins[2])

    thumbnail = image.convert("RGBA")
    thumbnail.thumbnail((thumbnail_max_width, thumbnail_max_height), Image.LANCZOS)

    thumbnail_x = (margins[3] + (thumbnail_max_width - thumbnail.width) // 2)
    thumbnail_y = (margins[0] + (thumbnail_max_height - thumbnail.height) // 2)

    final_image.paste(thumbnail, (thumbnail_x, thumbnail_y), thumbnail)

    return final_image


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
