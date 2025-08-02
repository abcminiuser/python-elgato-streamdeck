#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import io
from PIL import Image

from ..Devices.StreamDeck import StreamDeck


def _create_image(image_format, background):
    return Image.new("RGB", image_format['size'], background)


def _scale_image(image, image_format, margins=(0, 0, 0, 0), background='black'):
    if len(margins) != 4:
        raise ValueError("Margins should be given as an array of four integers.")

    final_image = _create_image(image_format, background=background)

    thumbnail_max_width = final_image.width - (margins[1] + margins[3])
    thumbnail_max_height = final_image.height - (margins[0] + margins[2])

    thumbnail = image.convert("RGBA")
    thumbnail.thumbnail((thumbnail_max_width, thumbnail_max_height), Image.LANCZOS)

    thumbnail_x = (margins[3] + (thumbnail_max_width - thumbnail.width) // 2)
    thumbnail_y = (margins[0] + (thumbnail_max_height - thumbnail.height) // 2)

    final_image.paste(thumbnail, (thumbnail_x, thumbnail_y), thumbnail)

    return final_image


def _to_native_format(image, image_format):
    if image.size != image_format['size']:
        image.thumbnail(image_format['size'])

    if image_format['rotation']:
        image = image.rotate(image_format['rotation'])

    if image_format['flip'][0]:
        image = image.transpose(Image.FLIP_LEFT_RIGHT)

    if image_format['flip'][1]:
        image = image.transpose(Image.FLIP_TOP_BOTTOM)

    # We want a compressed image in a given codec, convert.
    with io.BytesIO() as compressed_image:
        image.save(compressed_image, image_format['format'], quality=100)
        return compressed_image.getvalue()


def create_image(deck: StreamDeck, background: str = 'black') -> Image.Image:
    """
    .. deprecated:: 0.9.5
        Use :func:`~PILHelper.create_key_image` method instead.
    """
    return create_key_image(deck, background)


def create_key_image(deck: StreamDeck, background: str = 'black') -> Image.Image:
    """
    Creates a new PIL Image with the correct image dimensions for the given
    StreamDeck device's keys.

    .. seealso:: See :func:`~PILHelper.to_native_key_format` method for converting a
                 PIL image instance to the native key image format of a given
                 StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible image for.
    :param str background: Background color to use, compatible with `PIL.Image.new()`.

    :rtype: PIL.Image
    :return: Created PIL image
    """
    return _create_image(deck.key_image_format(), background)


def create_touchscreen_image(deck: StreamDeck, background: str = 'black') -> Image.Image:
    """
    Creates a new PIL Image with the correct image dimensions for the given
    StreamDeck device's touchscreen.

    .. seealso:: See :func:`~PILHelper.to_native_touchscreen_format` method for converting a
                 PIL image instance to the native touchscreen image format of a given
                 StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible image for.
    :param str background: Background color to use, compatible with `PIL.Image.new()`.

    :rtype: PIL.Image
    :return: Created PIL image
    """
    return _create_image(deck.touchscreen_image_format(), background)


def create_screen_image(deck: StreamDeck, background: str = 'black') -> Image.Image:
    """
    Creates a new PIL Image with the correct image dimensions for the given
    StreamDeck device's screen.

    .. seealso:: See :func:`~PILHelper.to_native_screen_format` method for converting a
                 PIL image instance to the native screen image format of a given
                 StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible image for.
    :param str background: Background color to use, compatible with `PIL.Image.new()`.

    :rtype: PIL.Image
    :return: Created PIL image
    """
    return _create_image(deck.screen_image_format(), background)


def create_scaled_image(deck: StreamDeck, image: Image.Image, margins: tuple[int, int, int, int] = (0, 0, 0, 0), background: str = 'black') -> Image.Image:
    """
    .. deprecated:: 0.9.5
        Use :func:`~PILHelper.create_scaled_key_image` method instead.
    """
    return create_scaled_key_image(deck, image, margins, background)


def create_scaled_key_image(deck: StreamDeck, image: Image.Image, margins: tuple[int, int, int, int] = (0, 0, 0, 0), background: str = 'black') -> Image.Image:
    """
    Creates a new key image that contains a scaled version of a given image,
    resized to best fit the given StreamDeck device's keys with the given
    margins around each side.

    The scaled image is centered within the new key image, offset by the given
    margins. The aspect ratio of the image is preserved.

    .. seealso:: See :func:`~PILHelper.to_native_key_format` method for converting a
                 PIL image instance to the native key image format of a given
                 StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible image for.
    :param Image image: PIL Image object to scale
    :param list(int): Array of margin pixels in (top, right, bottom, left) order.
    :param str background: Background color to use, compatible with `PIL.Image.new()`.

    :rtrype: PIL.Image
    :return: Loaded PIL image scaled and centered
    """
    return _scale_image(image, deck.key_image_format(), margins, background)


def create_scaled_touchscreen_image(deck: StreamDeck, image: Image.Image, margins: tuple[int, int, int, int] = (0, 0, 0, 0), background: str = 'black') -> Image.Image:
    """
    Creates a new touchscreen image that contains a scaled version of a given image,
    resized to best fit the given StreamDeck device's touchscreen with the given
    margins around each side.

    The scaled image is centered within the new touchscreen image, offset by the given
    margins. The aspect ratio of the image is preserved.

    .. seealso:: See :func:`~PILHelper.to_native_touchscreen_format` method for converting a
                 PIL image instance to the native key image format of a given
                 StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible image for.
    :param Image image: PIL Image object to scale
    :param list(int): Array of margin pixels in (top, right, bottom, left) order.
    :param str background: Background color to use, compatible with `PIL.Image.new()`.

    :rtrype: PIL.Image
    :return: Loaded PIL image scaled and centered
    """
    return _scale_image(image, deck.touchscreen_image_format(), margins, background)


def create_scaled_screen_image(deck: StreamDeck, image: Image.Image, margins: tuple[int, int, int, int] = (0, 0, 0, 0), background: str = 'black') -> Image.Image:
    """
    Creates a new screen image that contains a scaled version of a given image,
    resized to best fit the given StreamDeck device's screen with the given
    margins around each side.

    The scaled image is centered within the new screen image, offset by the given
    margins. The aspect ratio of the image is preserved.

    .. seealso:: See :func:`~PILHelper.to_native_screen_format` method for converting a
                 PIL image instance to the native key image format of a given
                 StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible image for.
    :param Image image: PIL Image object to scale
    :param list(int): Array of margin pixels in (top, right, bottom, left) order.
    :param str background: Background color to use, compatible with `PIL.Image.new()`.

    :rtrype: PIL.Image
    :return: Loaded PIL image scaled and centered
    """
    return _scale_image(image, deck.screen_image_format(), margins, background)


def to_native_format(deck: StreamDeck, image: Image.Image) -> bytes:
    """
    .. deprecated:: 0.9.5
        Use :func:`~PILHelper.to_native_key_format` method instead.
    """
    return to_native_key_format(deck, image)


def to_native_key_format(deck: StreamDeck, image: Image.Image) -> bytes:
    """
    Converts a given PIL image to the native key image format for a StreamDeck,
    suitable for passing to :func:`~StreamDeck.set_key_image`.

    .. seealso:: See :func:`~PILHelper.create_image` method for creating a PIL
                 image instance for a given StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible native image for.
    :param PIL.Image image: PIL Image to convert to the native StreamDeck image format

    :rtype: enumerable()
    :return: Image converted to the given StreamDeck's native format
    """
    return _to_native_format(image, deck.key_image_format())


def to_native_touchscreen_format(deck: StreamDeck, image: Image.Image) -> bytes:
    """
    Converts a given PIL image to the native touchscreen image format for a StreamDeck,
    suitable for passing to :func:`~StreamDeck.set_touchscreen_image`.

    .. seealso:: See :func:`~PILHelper.create_touchscreen_image` method for creating a PIL
                 image instance for a given StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible native image for.
    :param PIL.Image image: PIL Image to convert to the native StreamDeck image format

    :rtype: enumerable()
    :return: Image converted to the given StreamDeck's native touchscreen format
    """
    return _to_native_format(image, deck.touchscreen_image_format())


def to_native_screen_format(deck: StreamDeck, image: Image.Image) -> bytes:
    """
    Converts a given PIL image to the native screen image format for a StreamDeck,
    suitable for passing to :func:`~StreamDeck.set_screen_image`.

    .. seealso:: See :func:`~PILHelper.create_screen_image` method for creating a PIL
                 image instance for a given StreamDeck device.

    :param StreamDeck deck: StreamDeck device to generate a compatible native image for.
    :param PIL.Image image: PIL Image to convert to the native StreamDeck image format

    :rtype: enumerable()
    :return: Image converted to the given StreamDeck's native screen format
    """
    return _to_native_format(image, deck.screen_image_format())
