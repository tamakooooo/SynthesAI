"""
Knowledge Card Image Generator - Claude Style

Generates visual knowledge cards with Claude's signature gradient style.
"""

import io
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from loguru import logger


class ClaudeStyleCardGenerator:
    """
    Generate knowledge cards in Claude's signature orange-purple gradient style.

    Claude Style Colors:
    - Gradient: Orange (#FF6B35) to Purple (#764BA2)
    - Background: Deep blue (#16213E)
    - Text: White (#FFFFFF) and light gray (#E8E8E8)
    - Accent: Bright orange (#FF8C61)
    """

    # Claude signature color palette
    COLORS = {
        "gradient_start": (255, 107, 53),   # Orange #FF6B35
        "gradient_end": (118, 75, 162),     # Purple #764BA2
        "background": (22, 33, 62),         # Deep blue #16213E
        "text_primary": (255, 255, 255),    # White #FFFFFF
        "text_secondary": (232, 232, 232),  # Light gray #E8E8E8
        "accent": (255, 140, 97),           # Bright orange #FF8C61
        "highlight": (255, 200, 87),        # Golden #FFC857
    }

    def __init__(
        self,
        width: int = 800,
        height: int = 1200,
        padding: int = 40,
        font_size_title: int = 32,
        font_size_heading: int = 24,
        font_size_body: int = 16,
    ):
        """
        Initialize card generator.

        Args:
            width: Card width in pixels
            height: Card height in pixels
            padding: Padding from edges
            font_size_title: Title font size
            font_size_heading: Heading font size
            font_size_body: Body text font size
        """
        self.width = width
        self.height = height
        self.padding = padding
        self.font_sizes = {
            "title": font_size_title,
            "heading": font_size_heading,
            "body": font_size_body,
        }

        # Load fonts (use default if custom fonts not found)
        self.fonts = self._load_fonts()

        logger.info(
            f"ClaudeStyleCardGenerator initialized: "
            f"size={width}x{height}, padding={padding}"
        )

    def _load_fonts(self) -> dict[str, ImageFont.FreeTypeFont]:
        """Load fonts for card rendering."""
        fonts = {}

        # Try to load custom fonts, fallback to default
        font_paths = [
            "assets/fonts/NotoSansSC-Regular.otf",  # Chinese font
            "assets/fonts/Inter-Regular.ttf",       # English font
        ]

        for font_name, size in self.font_sizes.items():
            try:
                # Try Chinese font first (for mixed content)
                if Path("assets/fonts/NotoSansSC-Regular.otf").exists():
                    fonts[font_name] = ImageFont.truetype(
                        "assets/fonts/NotoSansSC-Regular.otf", size
                    )
                else:
                    # Use default font
                    fonts[font_name] = ImageFont.load_default()
                    logger.warning(
                        f"Custom font not found, using default for {font_name}"
                    )
            except Exception as e:
                logger.warning(f"Font loading failed: {e}, using default")
                fonts[font_name] = ImageFont.load_default()

        return fonts

    def _create_gradient_background(
        self, image: Image.Image, start_color: tuple, end_color: tuple
    ) -> None:
        """
        Create gradient background from start_color to end_color.

        Args:
            image: PIL Image to draw on
            start_color: Gradient start color (RGB)
            end_color: Gradient end color (RGB)
        """
        draw = ImageDraw.Draw(image)

        # Create top gradient (Orange to Purple)
        gradient_height = self.height // 3
        for y in range(gradient_height):
            # Interpolate color
            ratio = y / gradient_height
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)

            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        # Fill rest with background color
        draw.rectangle(
            [0, gradient_height, self.width, self.height],
            fill=self.COLORS["background"]
        )

    def _wrap_text(
        self, text: str, font: ImageFont.FreeTypeFont, max_width: int
    ) -> list[str]:
        """
        Wrap text to fit within max_width.

        Args:
            text: Text to wrap
            font: Font to use for measuring
            max_width: Maximum width in pixels

        Returns:
            List of wrapped lines
        """
        lines = []

        # Estimate characters per line (rough approximation)
        avg_char_width = font.getlength("中") if "中" in text else font.getlength("x")
        chars_per_line = int(max_width / avg_char_width) - 2

        # Wrap text
        wrapped = textwrap.wrap(text, width=chars_per_line)
        lines.extend(wrapped)

        return lines

    def generate_card(
        self,
        title: str,
        summary: str,
        key_points: list[str],
        tags: list[str] | None = None,
        output_path: Path | None = None,
    ) -> Image.Image | None:
        """
        Generate knowledge card image.

        Args:
            title: Card title
            summary: Content summary (will be wrapped)
            key_points: List of key points (bullet points)
            tags: Optional tags to display
            output_path: Optional path to save image

        Returns:
            PIL Image object or None if saved to file
        """
        logger.info(f"Generating knowledge card for: {title[:50]}...")

        # Create image with gradient background
        image = Image.new("RGB", (self.width, self.height))
        self._create_gradient_background(
            image,
            self.COLORS["gradient_start"],
            self.COLORS["gradient_end"]
        )

        draw = ImageDraw.Draw(image)

        # Calculate layout positions
        y_offset = self.padding + 20

        # Draw title
        title_lines = self._wrap_text(
            title, self.fonts["title"], self.width - 2 * self.padding
        )
        for line in title_lines:
            draw.text(
                (self.padding, y_offset),
                line,
                font=self.fonts["title"],
                fill=self.COLORS["text_primary"]
            )
            y_offset += self.font_sizes["title"] + 10

        # Draw separator line
        y_offset += 20
        draw.line(
            [(self.padding, y_offset), (self.width - self.padding, y_offset)],
            fill=self.COLORS["accent"],
            width=2
        )
        y_offset += 30

        # Draw summary heading
        draw.text(
            (self.padding, y_offset),
            "内容摘要",
            font=self.fonts["heading"],
            fill=self.COLORS["highlight"]
        )
        y_offset += self.font_sizes["heading"] + 20

        # Draw summary text
        summary_lines = self._wrap_text(
            summary, self.fonts["body"], self.width - 2 * self.padding
        )
        for line in summary_lines[:8]:  # Limit to 8 lines
            draw.text(
                (self.padding, y_offset),
                line,
                font=self.fonts["body"],
                fill=self.COLORS["text_secondary"]
            )
            y_offset += self.font_sizes["body"] + 8

        y_offset += 40

        # Draw key points heading
        draw.text(
            (self.padding, y_offset),
            "核心要点",
            font=self.fonts["heading"],
            fill=self.COLORS["highlight"]
        )
        y_offset += self.font_sizes["heading"] + 20

        # Draw key points (bullet points)
        bullet_color = self.COLORS["accent"]
        for i, point in enumerate(key_points[:6], 1):  # Limit to 6 points
            # Draw bullet
            draw.ellipse(
                [
                    self.padding,
                    y_offset + 5,
                    self.padding + 10,
                    y_offset + 15
                ],
                fill=bullet_color
            )

            # Draw point text
            point_text = f"{i}. {point}"
            point_lines = self._wrap_text(
                point_text,
                self.fonts["body"],
                self.width - 2 * self.padding - 20
            )

            for line_idx, line in enumerate(point_lines[:2]):  # Limit to 2 lines per point
                x_offset = self.padding + 20 if line_idx == 0 else self.padding + 20
                draw.text(
                    (x_offset, y_offset),
                    line,
                    font=self.fonts["body"],
                    fill=self.COLORS["text_secondary"]
                )
                y_offset += self.font_sizes["body"] + 6

            y_offset += 15

        # Draw tags if provided
        if tags:
            y_offset += 30
            tags_text = " ".join([f"#{tag}" for tag in tags[:5]])
            draw.text(
                (self.padding, y_offset),
                tags_text,
                font=self.fonts["body"],
                fill=self.COLORS["accent"]
            )

        # Draw footer
        footer_y = self.height - self.padding - 30
        draw.text(
            (self.padding, footer_y),
            "Generated by Learning Assistant",
            font=self.fonts["body"],
            fill=self.COLORS["text_secondary"]
        )

        # Save or return image
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "PNG", quality=95)
            logger.info(f"Knowledge card saved to: {output_path}")
            return None
        else:
            return image

    def generate_card_bytes(
        self,
        title: str,
        summary: str,
        key_points: list[str],
        tags: list[str] | None = None,
    ) -> io.BytesIO:
        """
        Generate knowledge card as BytesIO stream.

        Args:
            title: Card title
            summary: Content summary
            key_points: List of key points
            tags: Optional tags

        Returns:
            BytesIO stream containing PNG image
        """
        image = self.generate_card(title, summary, key_points, tags)

        if image:
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG", quality=95)
            img_bytes.seek(0)
            return img_bytes
        else:
            raise RuntimeError("Failed to generate card image")