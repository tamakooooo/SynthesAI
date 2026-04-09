"""
QR code display utilities for terminal.

Provides ASCII art QR code display for authentication.
"""

from pathlib import Path
from loguru import logger

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L

    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    logger.warning(
        "qrcode library not installed. Install with: pip install qrcode[pil]"
    )

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _print_qr_ascii_safe(qr: "qrcode.QRCode", invert: bool = False) -> None:
    """
    Print QR code using ASCII-safe characters for Windows GBK compatibility.

    Uses larger blocks for better visibility.

    Args:
        qr: QRCode object
        invert: Whether to invert colors
    """
    # Get QR matrix
    modules = qr.get_matrix()

    # Border size
    border = 4

    # Characters to use (ASCII-safe) - use double characters for better visibility
    dark_char = "##" if not invert else "  "
    light_char = "  " if not invert else "##"

    # Print top border
    for _ in range(border):
        print(light_char * (len(modules) + 2 * border))

    # Print QR code rows
    for row in modules:
        line = light_char * border  # Left border
        for module in row:
            line += dark_char if module else light_char
        line += light_char * border  # Right border
        print(line)

    # Print bottom border
    for _ in range(border):
        print(light_char * (len(modules) + 2 * border))


def display_qr_ascii(url: str, invert: bool = False) -> None:
    """
    Display QR code in terminal using ASCII art.

    Uses ASCII-safe characters (#) for Windows GBK compatibility.

    Args:
        url: URL to encode in QR code
        invert: Whether to invert colors (for light terminals)

    Raises:
        RuntimeError: If qrcode library is not installed
    """
    if not QRCODE_AVAILABLE:
        raise RuntimeError(
            "qrcode library not installed. Install with: pip install qrcode[pil]"
        )

    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=1,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Use custom ASCII renderer for Windows compatibility
    _print_qr_ascii_safe(qr, invert=invert)


def get_qr_terminal_string(url: str, invert: bool = False) -> str:
    """
    Generate QR code as string for display.

    Uses ASCII-safe characters for Windows GBK compatibility.

    Args:
        url: URL to encode in QR code
        invert: Whether to invert colors

    Returns:
        QR code as string (multiline)

    Raises:
        RuntimeError: If qrcode library is not installed
    """
    if not QRCODE_AVAILABLE:
        raise RuntimeError(
            "qrcode library not installed. Install with: pip install qrcode[pil]"
        )

    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=1,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Generate ASCII-safe string
    return _get_qr_string_safe(qr, invert=invert)


def _get_qr_string_safe(qr: "qrcode.QRCode", invert: bool = False) -> str:
    """
    Generate QR code string using ASCII-safe characters.

    Uses larger blocks for better visibility.

    Args:
        qr: QRCode object
        invert: Whether to invert colors

    Returns:
        QR code as multiline string
    """
    # Get QR matrix
    modules = qr.get_matrix()

    # Border size
    border = 4

    # Characters to use (ASCII-safe) - use double characters for better visibility
    dark_char = "##" if not invert else "  "
    light_char = "  " if not invert else "##"

    lines = []

    # Top border
    for _ in range(border):
        lines.append(light_char * (len(modules) + 2 * border))

    # QR code rows
    for row in modules:
        line = light_char * border  # Left border
        for module in row:
            line += dark_char if module else light_char
        line += light_char * border  # Right border
        lines.append(line)

    # Bottom border
    for _ in range(border):
        lines.append(light_char * (len(modules) + 2 * border))

    return "\n".join(lines)


def check_qrcode_library() -> bool:
    """
    Check if qrcode library is available.

    Returns:
        True if available, False otherwise
    """
    return QRCODE_AVAILABLE


def save_qr_image(
    url: str, filename: str = "qr_code.png", output_dir: str = "."
) -> Path | None:
    """
    Save QR code as PNG image file.

    Args:
        url: URL to encode in QR code
        filename: Output filename (default: qr_code.png)
        output_dir: Output directory (default: current directory)

    Returns:
        Path to saved image file, or None if failed

    Raises:
        RuntimeError: If required libraries are not installed
    """
    if not QRCODE_AVAILABLE:
        raise RuntimeError(
            "qrcode library not installed. Install with: pip install qrcode[pil]"
        )

    if not PIL_AVAILABLE:
        logger.warning(
            "PIL/Pillow not installed. Cannot save QR as image. Install with: pip install Pillow"
        )
        return None

    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(url)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to file
        output_path = Path(output_dir) / filename
        img.save(output_path)

        logger.info(f"QR code image saved to: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to save QR image: {e}")
        return None
