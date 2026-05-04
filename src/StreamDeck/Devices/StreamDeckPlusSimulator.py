#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import io
import math
import threading
import time

import pygame
from PIL import Image, ImageDraw, ImageFont
from pygame.locals import (
    QUIT,
    KEYDOWN,
    MOUSEBUTTONDOWN,
    MOUSEBUTTONUP,
    MOUSEMOTION,
    KMOD_CTRL,
    KMOD_META,
    K_PLUS,
    K_EQUALS,
    K_MINUS,
    K_0,
)

from .StreamDeck import DialEventType, StreamDeck, TouchscreenEventType


class SimulatedDevice:
    """
    Simulates a physical USB device connection for the StreamDeckPlusSimulator.
    """

    def __init__(self):
        self.is_open_state = False
        self.callback = None
        self.key_states = [False] * StreamDeckPlusSimulator.KEY_COUNT
        self.dial_states = [False] * StreamDeckPlusSimulator.DIAL_COUNT
        self.key_images = [None] * StreamDeckPlusSimulator.KEY_COUNT
        self.touchscreen_image = None
        self.brightness = 100
        self.serial_number = "SIM"
        self.firmware_version = "1.0.0"

    def open(self):
        self.is_open_state = True

    def close(self):
        self.is_open_state = False

    def is_open(self):
        return self.is_open_state

    def read(self, length):
        # This is a stub; the simulator doesn't actually read from USB
        return None

    def write(self, data):
        pass

    def read_feature(self, report_id, length):
        # Simulate reading feature reports
        if report_id == 0x06:  # Serial number
            result = bytearray(32)
            result[0] = report_id
            for i, c in enumerate(self.serial_number.encode("ascii")):
                result[5 + i] = c
            return result
        elif report_id == 0x05:  # Firmware version
            result = bytearray(32)
            result[0] = report_id
            for i, c in enumerate(self.firmware_version.encode("ascii")):
                result[5 + i] = c
            return result
        return None

    def write_feature(self, data):
        pass


class StreamDeckPlusSimulator(StreamDeck):
    """
    Represents a simulated StreamDeck Plus device using pygame.
    """

    KEY_COUNT = 8
    KEY_COLS = 4
    KEY_ROWS = 2

    DIAL_COUNT = 4

    KEY_PIXEL_WIDTH = 120
    KEY_PIXEL_HEIGHT = 120
    KEY_IMAGE_FORMAT = "JPEG"
    KEY_FLIP = (False, False)
    KEY_ROTATION = 0

    DECK_TYPE = "Stream Deck + Simulator"
    DECK_VISUAL = True
    DECK_TOUCH = True

    TOUCHSCREEN_PIXEL_HEIGHT = 100
    TOUCHSCREEN_PIXEL_WIDTH = 800
    TOUCHSCREEN_IMAGE_FORMAT = "JPEG"
    TOUCHSCREEN_FLIP = (False, False)
    TOUCHSCREEN_ROTATION = 0

    # Layout configuration
    KEY_SPACING = 10
    DIAL_RADIUS = 25
    TOUCHSCREEN_Y_OFFSET = 280

    # The actual window size for the simulator
    # row of 4 keys, 2 rows, touchscreen, 4 dials. 20px margin on all sides for all elements
    MARGIN_PX = 20

    # Default scale factor (100% = 1.0)
    DEFAULT_SCALE = 1.0

    # Colours
    BACKGROUND_COLOR = (30, 30, 30)
    KEY_COLOR = (60, 60, 60)
    DIAL_COLOR = (80, 80, 80)
    DIAL_INDICATOR_COLOR = (200, 200, 200)
    TOUCHSCREEN_COLOR = (0, 0, 0)

    def __init__(self, scale_factor=DEFAULT_SCALE):
        # Create a simulated device
        device = SimulatedDevice()
        super().__init__(device)

        self._scale_factor = scale_factor  # Size multiplier for UI elements

        # Calculate window dimensions based on scale factor
        self._calculate_dimensions()

        # For tracking mouse state
        self.mouse_down = False
        self.active_dial = None
        self.dial_start_angle = 0
        self.touchscreen_drag_start = None
        self.touchscreen_press_time = None  # Track when touchscreen was pressed

        # Initialise pygame only when needed
        self.pygame_initialised = False
        self.screen = None
        self.running = False
        self.clock = None

        # Thread for automatic updates
        self.update_thread = None
        self.thread_running = False

        self.touchscreen_blank = True

    def scale(self, value):
        """Scale a value according to the current scale factor"""
        return int(value * self._scale_factor)

    def _calculate_dimensions(self):
        """Calculate window dimensions based on current scale factor"""
        self.WINDOW_WIDTH = max(
            self.KEY_COLS * self.scale(self.KEY_PIXEL_WIDTH)
            + self.scale(self.MARGIN_PX) * (self.KEY_COLS + 1),
            self.scale(self.TOUCHSCREEN_PIXEL_WIDTH) + self.scale(self.MARGIN_PX) * 2,
            self.DIAL_COUNT * self.scale(self.DIAL_RADIUS) * 2
            + self.scale(self.MARGIN_PX) * (self.DIAL_COUNT + 1),
        )
        self.WINDOW_HEIGHT = (
            self.scale(self.MARGIN_PX)
            + self.KEY_ROWS * self.scale(self.KEY_PIXEL_HEIGHT)
            + self.scale(self.MARGIN_PX) * self.KEY_ROWS
            + self.scale(self.TOUCHSCREEN_PIXEL_HEIGHT)
            + self.scale(self.MARGIN_PX)
            + 4 * self.scale(self.DIAL_RADIUS) * 2
            + self.scale(self.MARGIN_PX)
        )

    @property
    def scale_factor(self):
        return self._scale_factor

    @scale_factor.setter
    def scale_factor(self, value):
        """Set scale factor and recalculate dimensions"""
        if value <= 0:
            raise ValueError("Scale factor must be greater than 0")

        self._scale_factor = value
        self._calculate_dimensions()

        # Reinitialise the display if already running
        if self.pygame_initialised and self.running:
            # Create a new display with updated dimensions
            self.screen = pygame.display.set_mode(
                (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
            )
            pygame.display.set_caption(self.DECK_TYPE)

    def _initialise_pygame(self):
        if not self.pygame_initialised:
            pygame.init()
            self.screen = pygame.display.set_mode(
                (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
            )
            pygame.display.set_caption(self.DECK_TYPE)
            self.clock = pygame.time.Clock()
            self.pygame_initialised = True
            self.set_touchscreen_image(None)

    def _reset_key_stream(self):
        # Not needed for simulator
        pass

    def reset(self):
        # Clear all keys and touchscreen
        for i in range(self.KEY_COUNT):
            self.set_key_image(i, None)
        self.set_touchscreen_image(None)

    def set_brightness(self, percent):
        if isinstance(percent, float):
            percent = int(100.0 * percent)
        percent = min(max(percent, 0), 100)
        self.device.brightness = percent

    def get_serial_number(self):
        return self.device.serial_number

    def get_firmware_version(self):
        return self.device.firmware_version

    def set_key_image(self, key, image):
        if min(max(key, 0), self.KEY_COUNT) != key:
            raise IndexError("Invalid key index {}.".format(key))

        # Store the image for rendering
        self.device.key_images[key] = image

    def _default_touchscreen_image(self):
        # Create a default touchscreen image
        image = Image.new(
            "RGB",
            (self.TOUCHSCREEN_PIXEL_WIDTH, self.TOUCHSCREEN_PIXEL_HEIGHT),
            color="black",
        )
        draw = ImageDraw.Draw(image)
        draw.text(
            (self.TOUCHSCREEN_PIXEL_WIDTH // 2, self.TOUCHSCREEN_PIXEL_HEIGHT // 2),
            text="elgato",
            fill="white",
            anchor="mm",
            font=ImageFont.load_default(size=60),
        )
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return buffer.getvalue()

    def set_touchscreen_image(self, image, x_pos=0, y_pos=0, width=0, height=0):
        # Check if partial update is requested
        if x_pos != 0 or y_pos != 0 or width != 0 or height != 0:
            if self.device.touchscreen_image is None or self.touchscreen_blank:
                background = Image.new(
                    "RGB",
                    (self.TOUCHSCREEN_PIXEL_WIDTH, self.TOUCHSCREEN_PIXEL_HEIGHT),
                    color="black",
                )
                buffer = io.BytesIO()
                background.save(buffer, format="JPEG")
                self.device.touchscreen_image = buffer.getvalue()
                self.touchscreen_blank = False
            # Convert existing image to PIL format
            current_image = Image.open(io.BytesIO(self.device.touchscreen_image))

            # Convert new image data to PIL format
            new_image = Image.open(io.BytesIO(image))

            # If width/height not specified, use the entire image
            if width == 0:
                width = new_image.width
            if height == 0:
                height = new_image.height

            # Ensure new image is right size if needed
            if new_image.width != width or new_image.height != height:
                new_image = new_image.resize((width, height))

            # Paste the new image onto the existing one at specified position
            current_image.paste(new_image, (x_pos, y_pos))

            # Convert back to bytes
            buffer = io.BytesIO()
            current_image.save(buffer, format=self.TOUCHSCREEN_IMAGE_FORMAT)
            self.device.touchscreen_image = buffer.getvalue()
            return

        if image is None:
            self.device.touchscreen_image = self._default_touchscreen_image()
            self.touchscreen_blank = True
        else:
            # If not a partial update or no existing image, store the whole image
            self.device.touchscreen_image = image
            self.touchscreen_blank = False

    def set_key_color(self, key, r, g, b):
        # Not implemented for StreamDeckPlus
        pass

    def set_screen_image(self, image):
        # Not implemented for StreamDeckPlus
        pass

    def _read_control_states(self):
        # In the simulator, we don't use this method to process events
        # Events are processed in the update() method
        return None

    def open(self):
        """
        Opens the simulated device and initialises pygame.
        """
        super().open()
        self.running = True
        # Start update thread
        self.thread_running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def close(self):
        """
        Closes the simulated device and quits pygame.
        """
        self.running = False
        self.thread_running = False

        # Wait for update thread to finish
        if (
            self.update_thread
            and self.update_thread.is_alive()
            and self.update_thread != threading.current_thread()
        ):
            self.update_thread.join(timeout=1.0)

        if self.pygame_initialised:
            pygame.quit()
            self.pygame_initialised = False
            self.screen = None
        super().close()

    def _update_loop(self):
        """
        Background thread that continuously calls update() while the device is open.
        """
        while self.thread_running and self.running:
            self.update()
            time.sleep(1 / 30)  # ~30 FPS

    def update(self):
        """
        Update the simulator state and render the UI.
        This is automatically called from the background thread,
        but can still be called manually if needed.
        """
        if not self.running:
            return

        # Initialise pygame if not already done
        if not self.pygame_initialised:
            self._initialise_pygame()

        # Process events and render
        if self.pygame_initialised and self.clock is not None:
            self._process_events()
            self._render()
            self.clock.tick(
                30
            )  # Kind of equivalent to read_poll_hz, but this loop has more work

    def _process_events(self):
        """
        Process pygame events and update the UI.
        """
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                self.close()
                break

            self._handle_pygame_event(event)

    def _handle_pygame_event(self, event):
        """
        Handles pygame events and triggers appropriate StreamDeck callbacks.
        """
        # Handle scaling keyboard shortcuts
        if event.type == KEYDOWN:
            # Ctrl/Cmd + Plus to increase scale
            if event.key == K_PLUS or event.key == K_EQUALS:
                if pygame.key.get_mods() & (KMOD_CTRL | KMOD_META):
                    new_scale = min(self.scale_factor + 0.25, 3.0)
                    self.scale_factor = new_scale
                    return
            # Ctrl/Cmd + Minus to decrease scale
            elif event.key == K_MINUS:
                if pygame.key.get_mods() & (KMOD_CTRL | KMOD_META):
                    new_scale = max(self.scale_factor - 0.25, 0.5)
                    self.scale_factor = new_scale
                    return
            # Ctrl/Cmd + 0 to reset scale to 1.0
            elif event.key == K_0:
                if pygame.key.get_mods() & (KMOD_CTRL | KMOD_META):
                    self.scale_factor = 1.0
                    return

        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True

            # Check for key presses
            for key_idx in range(self.KEY_COUNT):
                key_rect = self._get_key_rect(key_idx)
                if key_rect.collidepoint(event.pos):
                    self.device.key_states[key_idx] = True
                    if self.key_callback:
                        self.key_callback(self, key_idx, True)
                    return

            # Check for touchscreen interaction
            touchscreen_rect = self._get_touchscreen_rect()
            if touchscreen_rect.collidepoint(event.pos):
                self.touchscreen_drag_start = event.pos
                self.touchscreen_press_time = (
                    pygame.time.get_ticks()
                )  # Record press time

            # Check for dial presses
            for dial_idx in range(self.DIAL_COUNT):
                dial_pos = self._get_dial_pos(dial_idx)
                dist = (
                    (event.pos[0] - dial_pos[0]) ** 2
                    + (event.pos[1] - dial_pos[1]) ** 2
                ) ** 0.5
                if dist <= self.scale(self.DIAL_RADIUS):
                    self.device.dial_states[dial_idx] = True
                    self.active_dial = dial_idx
                    self.dial_start_angle = self._get_angle(dial_pos, event.pos)
                    if self.dial_callback:
                        self.dial_callback(
                            self,
                            dial_idx,
                            DialEventType.PUSH,
                            True,
                        )

        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

            # Check for key releases
            for key_idx in range(self.KEY_COUNT):
                if self.device.key_states[key_idx]:
                    self.device.key_states[key_idx] = False
                    if self.key_callback:
                        self.key_callback(self, key_idx, False)

            # Check for dial releases
            if self.active_dial is not None:
                dial_idx = self.active_dial
                self.device.dial_states[dial_idx] = False
                self.active_dial = None
                if self.dial_callback:
                    self.dial_callback(
                        self,
                        dial_idx,
                        DialEventType.PUSH,
                        False,
                    )

            # Check for touchscreen interaction end
            if self.touchscreen_drag_start and self.touchscreen_press_time:
                touchscreen_rect = self._get_touchscreen_rect()
                if (
                    touchscreen_rect.collidepoint(event.pos)
                    and self.touchscreen_callback
                ):
                    # Calculate drag distance
                    drag_dist = (
                        (event.pos[0] - self.touchscreen_drag_start[0]) ** 2
                        + (event.pos[1] - self.touchscreen_drag_start[1]) ** 2
                    ) ** 0.5

                    # Calculate press duration in milliseconds
                    press_duration = (
                        pygame.time.get_ticks() - self.touchscreen_press_time
                    )

                    # Calculate the positions in touchscreen coordinates
                    start_x = (
                        self.touchscreen_drag_start[0] - touchscreen_rect.left
                    ) * (self.TOUCHSCREEN_PIXEL_WIDTH / touchscreen_rect.width)
                    start_y = (
                        self.touchscreen_drag_start[1] - touchscreen_rect.top
                    ) * (self.TOUCHSCREEN_PIXEL_HEIGHT / touchscreen_rect.height)
                    end_x = (event.pos[0] - touchscreen_rect.left) * (
                        self.TOUCHSCREEN_PIXEL_WIDTH / touchscreen_rect.width
                    )
                    end_y = (event.pos[1] - touchscreen_rect.top) * (
                        self.TOUCHSCREEN_PIXEL_HEIGHT / touchscreen_rect.height
                    )

                    # Determine event type based on drag distance regardless of timing
                    if drag_dist > self.scale(10):  # Significant movement = DRAG
                        self.touchscreen_callback(
                            self,
                            TouchscreenEventType.DRAG,
                            {
                                "x": int(start_x),
                                "y": int(start_y),
                                "x_out": int(end_x),
                                "y_out": int(end_y),
                            },
                        )
                    elif press_duration > 500:  # Minimal movement + long press = LONG
                        self.touchscreen_callback(
                            self,
                            TouchscreenEventType.LONG,
                            {"x": int(end_x), "y": int(end_y)},
                        )
                    else:  # Minimal movement + short press = SHORT
                        self.touchscreen_callback(
                            self,
                            TouchscreenEventType.SHORT,
                            {"x": int(end_x), "y": int(end_y)},
                        )

                self.touchscreen_drag_start = None
                self.touchscreen_press_time = None

        elif event.type == MOUSEMOTION and self.mouse_down:
            # Handle dial rotation
            if self.active_dial is not None:
                dial_pos = self._get_dial_pos(self.active_dial)
                current_angle = self._get_angle(dial_pos, event.pos)
                angle_diff = current_angle - self.dial_start_angle

                # Normalize to -180 to 180
                if angle_diff > 180:
                    angle_diff -= 360
                elif angle_diff < -180:
                    angle_diff += 360

                # Use angle difference to determine rotation amount
                # Convert to values similar to what the real StreamDeck+ would report
                if abs(angle_diff) > 5:  # Threshold to avoid jitter
                    rotation_value = int(
                        angle_diff / 10
                    )  # Scale down to reasonable values
                    self.dial_start_angle = current_angle

                    if self.dial_callback:
                        self.dial_callback(
                            self, self.active_dial, DialEventType.TURN, rotation_value
                        )
        elif event.type == MOUSEBUTTONDOWN and event.button in [4, 5]:
            # Rotate dials by scrolling
            for dial_idx in range(self.DIAL_COUNT):
                dial_pos = self._get_dial_pos(dial_idx)
                dist = (
                    (event.pos[0] - dial_pos[0]) ** 2
                    + (event.pos[1] - dial_pos[1]) ** 2
                ) ** 0.5
                if dist <= self.scale(self.DIAL_RADIUS):
                    if self.dial_callback:
                        self.dial_callback(
                            self,
                            dial_idx,
                            DialEventType.TURN,
                            1 if event.button == 4 else -1,
                        )
                    break

    def _get_angle(self, center, point):
        """Calculate angle in degrees between center and point."""
        dx = point[0] - center[0]
        dy = point[1] - center[1]
        angle = (360 + int(math.degrees(math.atan2(dy, dx)))) % 360
        return angle

    def _render(self):
        """
        Renders the StreamDeck Plus simulator UI.
        """
        if not self.pygame_initialised or self.screen is None:
            return

        # Clear screen
        self.screen.fill(self.BACKGROUND_COLOR)

        highlight_thickness = max(3, self.scale(3))  # active key highlight, scaled

        # Draw keys
        for i in range(self.KEY_COUNT):
            key_rect = self._get_key_rect(i)
            pygame.draw.rect(self.screen, self.KEY_COLOR, key_rect)

            # Display the actual key image if set
            if self.device.key_images[i] is not None:
                # Convert raw JPEG bytes to pygame surface
                image = pygame.image.load(io.BytesIO(self.device.key_images[i]))

                # Scale image to fit key
                image = pygame.transform.scale(image, (key_rect.width, key_rect.height))

                # Apply flip/rotation if needed
                if self.KEY_FLIP[0] or self.KEY_FLIP[1]:
                    image = pygame.transform.flip(
                        image, self.KEY_FLIP[0], self.KEY_FLIP[1]
                    )

                if self.KEY_ROTATION != 0:
                    image = pygame.transform.rotate(image, self.KEY_ROTATION)

                # Blit image onto key rectangle
                self.screen.blit(image, key_rect.topleft)

            # Highlight pressed keys
            if self.device.key_states[i]:
                pygame.draw.rect(
                    self.screen, (100, 100, 255), key_rect, highlight_thickness
                )

        # Draw dials
        for i in range(self.DIAL_COUNT):
            dial_pos = self._get_dial_pos(i)
            pygame.draw.circle(
                self.screen, self.DIAL_COLOR, dial_pos, self.scale(self.DIAL_RADIUS)
            )

            # Highlight pressed dials
            if self.device.dial_states[i]:
                pygame.draw.circle(
                    self.screen,
                    (100, 100, 255),
                    dial_pos,
                    self.scale(self.DIAL_RADIUS),
                    highlight_thickness,
                )

        # Draw touchscreen
        touchscreen_rect = self._get_touchscreen_rect()
        pygame.draw.rect(self.screen, self.TOUCHSCREEN_COLOR, touchscreen_rect)

        # Display the actual touchscreen image if set
        if self.device.touchscreen_image is not None:
            # Convert raw JPEG bytes to pygame surface
            image = pygame.image.load(io.BytesIO(self.device.touchscreen_image))

            # Scale image to fit touchscreen area
            image = pygame.transform.scale(
                image, (touchscreen_rect.width, touchscreen_rect.height)
            )

            # Apply flip/rotation if needed
            if self.TOUCHSCREEN_FLIP[0] or self.TOUCHSCREEN_FLIP[1]:
                image = pygame.transform.flip(
                    image, self.TOUCHSCREEN_FLIP[0], self.TOUCHSCREEN_FLIP[1]
                )

            if self.TOUCHSCREEN_ROTATION != 0:
                image = pygame.transform.rotate(image, self.TOUCHSCREEN_ROTATION)

            # Blit image onto touchscreen rectangle
            self.screen.blit(image, touchscreen_rect.topleft)

        # Update display
        pygame.display.flip()

    def _get_key_rect(self, key_idx) -> pygame.Rect:
        """
        Gets the rectangle for a specific key.
        """
        row = key_idx // self.KEY_COLS
        col = key_idx % self.KEY_COLS

        key_width = self.scale(self.KEY_PIXEL_WIDTH)
        key_height = key_width  # Square keys

        # Calculate available width and spacing between keys
        available_width = self.WINDOW_WIDTH - (2 * self.scale(self.MARGIN_PX))
        column_width = available_width / self.KEY_COLS

        # Center the key in its column
        x = (
            self.scale(self.MARGIN_PX)
            + col * column_width
            + (column_width - key_width) / 2
        )
        y = self.scale(self.MARGIN_PX) + row * (key_height + self.scale(self.MARGIN_PX))

        return pygame.Rect(x, y, key_width, key_height)

    def _get_dial_pos(self, dial_idx) -> tuple[int, int]:
        """
        Gets the position for a specific dial.
        """
        dial_spacing = self.WINDOW_WIDTH // (self.DIAL_COUNT + 1)
        x = dial_spacing * (dial_idx + 1)
        y = (
            self.scale(self.MARGIN_PX) * 2
            + (self.scale(self.KEY_PIXEL_HEIGHT) + self.scale(self.MARGIN_PX))
            * self.KEY_ROWS
            + self.scale(self.DIAL_RADIUS)
            + self.scale(self.TOUCHSCREEN_PIXEL_HEIGHT)
        )
        return (x, y)

    def _get_touchscreen_rect(self) -> pygame.Rect:
        """
        Gets the rectangle for the touchscreen.
        """
        x = self.scale(self.MARGIN_PX)
        y = self.scale(self.MARGIN_PX) * 2 + self.KEY_ROWS * (
            self.scale(self.KEY_PIXEL_HEIGHT) + self.scale(self.KEY_SPACING)
        )

        return pygame.Rect(
            x,
            y,
            self.scale(self.TOUCHSCREEN_PIXEL_WIDTH),
            self.scale(self.TOUCHSCREEN_PIXEL_HEIGHT),
        )
