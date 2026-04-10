"""
Visual Knowledge Card Generator - Editorial Style

Generates professional visual knowledge cards in editorial style,
inspired by visual-note-card-skills design patterns.
"""

import asyncio
import base64
import io
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger
from PIL import Image


class VisualCardGenerator:
    """
    Generate professional editorial-style knowledge cards using HTML rendering.

    Design Features:
    - Fixed 1200px width layout
    - Grid-based framework cards
    - Dark/light dual-panel contrast
    - Claude-style orange-purple color scheme
    - Editorial typography (serif titles, sans-serif body, mono labels)
    """

    # Claude-style color palette (adapted for editorial design)
    COLORS = {
        "primary": "#FF6B35",        # Claude Orange
        "primary_dark": "#E85A2D",   # Darker orange
        "primary_deep": "#CC4A22",   # Deep orange
        "accent": "#764BA2",         # Claude Purple
        "accent_dark": "#5E3A82",    # Darker purple
        "bg": "#F5F1EC",             # Warm beige background
        "bg_light": "#FAF7F2",       # Lighter beige
        "bg_card": "#E8E3DC",        # Card background
        "black": "#1A1A1A",          # Deep black for dark panel
        "white": "#FFFFFF",          # White
        "gray": "#6B6B6B",           # Gray text
        "gray_light": "#999999",     # Light gray
        "highlight": "#FFB87A",      # Soft orange highlight
    }

    def __init__(self, width: int = 1200, output_format: str = "png"):
        """
        Initialize visual card generator.

        Args:
            width: Card width (fixed at 1200px for editorial design)
            output_format: Output format (png/jpeg)
        """
        self.width = width
        self.output_format = output_format

        logger.info(f"VisualCardGenerator initialized: width={width}, format={output_format}")

    def _generate_html(
        self,
        title: str,
        summary: str,
        key_points: list[str],
        key_concepts: list[dict[str, str]] | None = None,
        tags: list[str] | None = None,
        source: str | None = None,
        url: str | None = None,
    ) -> str:
        """
        Generate HTML template for knowledge card.

        Args:
            title: Card title
            summary: Content summary
            key_points: List of key points
            key_concepts: Optional list of key concepts with definitions
            tags: Optional tags
            source: Optional source name
            url: Optional source URL

        Returns:
            Complete HTML string
        """
        # Build framework cards (key points as grid cards)
        framework_cards_html = self._build_framework_cards(key_points)

        # Build dark panel (summary content)
        dark_panel_html = self._build_dark_panel(summary, key_concepts)

        # Build light panel (insights/highlights)
        light_panel_html = self._build_light_panel(key_points[:3] if key_points else [])

        # Build bottom highlight bar
        highlight_bar_html = self._build_highlight_bar(tags)

        # Build tags
        tags_html = " · ".join(tags) if tags else ""

        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Noto+Sans+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@500;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  :root {{
    --primary: {self.COLORS['primary']};
    --primary-dark: {self.COLORS['primary_dark']};
    --primary-deep: {self.COLORS['primary_deep']};
    --accent: {self.COLORS['accent']};
    --accent-dark: {self.COLORS['accent_dark']};
    --bg: {self.COLORS['bg']};
    --bg-light: {self.COLORS['bg_light']};
    --bg-card: {self.COLORS['bg_card']};
    --black: {self.COLORS['black']};
    --white: {self.COLORS['white']};
    --gray: {self.COLORS['gray']};
    --gray-light: {self.COLORS['gray_light']};
    --highlight: {self.COLORS['highlight']};
  }}

  body {{
    background: var(--bg);
    font-family: 'Noto Sans SC', sans-serif;
    color: var(--black);
    padding: 0;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
  }}

  .poster {{
    width: {self.width}px;
    background: var(--bg);
    padding: 36px 40px 28px;
    position: relative;
  }}

  .top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
  }}
  .top-bar .label-left,
  .top-bar .label-right {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--gray);
    font-weight: 700;
  }}
  .top-bar .label-right {{ text-align: right; }}

  .main-title {{
    margin: 10px 0 4px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 40px;
  }}
  .main-title .left h1 {{
    font-family: 'Noto Sans SC', sans-serif;
    font-size: 40px;
    font-weight: 900;
    line-height: 1.15;
    color: var(--primary);
  }}
  .main-title .right-info {{
    text-align: right;
    flex-shrink: 0;
    max-width: 320px;
  }}
  .main-title .right-info .subtitle {{
    font-size: 14.5px;
    font-weight: 700;
    line-height: 1.65;
    color: var(--black);
    margin-bottom: 8px;
  }}
  .main-title .right-info .url {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--gray-light);
    letter-spacing: 0.5px;
  }}

  .framework-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 10px;
    margin: 24px 0 18px;
  }}
  .fw-card {{
    background: var(--bg-card);
    padding: 16px 18px 14px;
    border-radius: 2px;
  }}
  .fw-card .badge {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }}
  .fw-card .badge .letter {{
    background: var(--primary);
    color: var(--white);
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 15px;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 3px;
  }}
  .fw-card:nth-child(3) .badge .letter {{ background: var(--accent); }}
  .fw-card:nth-child(4) .badge .letter {{ background: var(--primary-deep); }}
  .fw-card:nth-child(5) .badge .letter {{ background: var(--accent); }}
  .fw-card:nth-child(6) .badge .letter {{ background: var(--primary); }}
  .fw-card .badge .name {{
    font-weight: 900;
    font-size: 17px;
    color: var(--black);
  }}
  .fw-card .desc {{
    font-size: 13px;
    color: var(--gray);
    line-height: 1.6;
  }}
  .fw-card .desc strong {{
    color: var(--black);
    font-weight: 700;
  }}

  .content-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-bottom: 14px;
  }}

  .panel-dark {{
    background: var(--black);
    color: var(--white);
    padding: 26px 28px 24px;
    border-radius: 3px;
  }}
  .panel-dark .section-title {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 18px;
    font-size: 16px;
    font-weight: 900;
    letter-spacing: 0.5px;
  }}
  .panel-dark .section-title .icon {{ font-size: 18px; }}
  .panel-dark .block-title {{
    color: var(--accent);
    font-weight: 900;
    font-size: 15px;
    margin-bottom: 10px;
    margin-top: 18px;
  }}
  .panel-dark .block-title:first-of-type {{ margin-top: 0; }}
  .panel-dark ul {{
    list-style: none;
    padding: 0;
  }}
  .panel-dark ul li {{
    font-size: 13.5px;
    line-height: 1.75;
    padding-left: 16px;
    position: relative;
    color: #d4d4d4;
  }}
  .panel-dark ul li::before {{
    content: '■';
    position: absolute;
    left: 0;
    color: var(--primary);
    font-size: 8px;
    top: 3px;
  }}
  .panel-dark ul li strong {{
    color: #fff;
    font-weight: 700;
  }}
  .panel-dark .conclusion {{
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #333;
  }}
  .panel-dark .conclusion .label {{
    font-weight: 900;
    font-size: 14.5px;
    color: var(--white);
    margin-bottom: 6px;
  }}
  .panel-dark .conclusion p {{
    font-size: 13px;
    color: #aaa;
    line-height: 1.7;
  }}

  .panel-light {{
    background: var(--bg-light);
    padding: 26px 28px 24px;
    border-radius: 3px;
  }}
  .panel-light .section-title {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    font-size: 16px;
    font-weight: 900;
    letter-spacing: 0.5px;
  }}
  .panel-light .section-title .icon {{
    color: var(--accent);
    font-size: 18px;
  }}
  .insight-item {{
    margin-bottom: 22px;
    display: flex;
    gap: 14px;
  }}
  .insight-item:last-child {{ margin-bottom: 0; }}
  .insight-num {{
    font-family: 'Playfair Display', serif;
    font-size: 36px;
    font-weight: 900;
    color: var(--primary);
    line-height: 1;
    flex-shrink: 0;
    width: 36px;
    text-align: center;
  }}
  .insight-content h4 {{
    font-size: 15px;
    font-weight: 900;
    margin-bottom: 5px;
    line-height: 1.4;
    color: var(--black);
  }}
  .insight-content p {{
    font-size: 13px;
    color: var(--gray);
    line-height: 1.7;
  }}
  .insight-content p strong {{
    color: var(--black);
    font-weight: 700;
  }}

  .bottom-highlight {{
    background: var(--primary-dark);
    color: var(--white);
    padding: 18px 24px;
    border-radius: 3px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 30px;
    margin-bottom: 14px;
  }}
  .bottom-highlight .formula {{
    font-weight: 900;
    font-size: 15px;
    line-height: 1.7;
  }}
  .bottom-highlight .formula .eq {{
    color: var(--highlight);
  }}
  .bottom-highlight .note {{
    font-size: 13px;
    line-height: 1.7;
    color: #FFD4B8;
    max-width: 480px;
    text-align: right;
  }}

  .footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 4px;
  }}
  .footer .left-url {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--gray-light);
    letter-spacing: 0.5px;
  }}
  .footer .right-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 1.5px;
    color: var(--gray);
    font-weight: 700;
    text-transform: uppercase;
  }}
  .footer .right-brand .dot {{
    width: 6px;
    height: 6px;
    background: var(--primary);
    border-radius: 50%;
  }}
</style>
</head>
<body>
<div class="poster">

  <!-- TOP BAR -->
  <div class="top-bar">
    <div class="label-left">KNOWLEDGE CARD · LINK SUMMARY</div>
    <div class="label-right">{source or 'WEB CONTENT'}</div>
  </div>

  <!-- MAIN TITLE -->
  <div class="main-title">
    <div class="left">
      <h1>{title}</h1>
    </div>
    <div class="right-info">
      <div class="subtitle">内容摘要 · 核心要点<br>关键概念 · 知识提炼<br><strong>Learning Assistant</strong></div>
      <div class="url">{url or ''}</div>
    </div>
  </div>

  <!-- FRAMEWORK ROW -->
  <div class="framework-row">
    {framework_cards_html}
  </div>

  <!-- TWO-COLUMN CONTENT -->
  <div class="content-row">
    {dark_panel_html}
    {light_panel_html}
  </div>

  <!-- BOTTOM HIGHLIGHT BAR -->
  {highlight_bar_html}

  <!-- FOOTER -->
  <div class="footer">
    <div class="left-url">{url or 'learning-assistant.local'}</div>
    <div class="right-brand">
      <div class="dot"></div>
      Learning Assistant
    </div>
  </div>

</div>
</body>
</html>
        """

        return html_template

    def _build_framework_cards(self, key_points: list[str]) -> str:
        """Build framework card grid HTML."""
        if not key_points:
            return ""

        cards_html = []
        for i, point in enumerate(key_points[:6], 1):  # Limit to 6 cards
            # Split point into title and description if possible
            parts = point.split("：", 1) if "：" in point else point.split(":", 1)
            if len(parts) == 2:
                card_title, card_desc = parts[0].strip(), parts[1].strip()
            else:
                card_title = f"要点 {i}"
                card_desc = point

            card_html = f"""
            <div class="fw-card">
              <div class="badge">
                <div class="letter">{i}</div>
                <div class="name">{card_title}</div>
              </div>
              <div class="desc">{card_desc}</div>
            </div>
            """
            cards_html.append(card_html)

        return "\n".join(cards_html)

    def _build_dark_panel(
        self, summary: str, key_concepts: list[dict[str, str]] | None
    ) -> str:
        """Build dark panel HTML (summary + key concepts)."""
        # Summary section
        summary_html = f"""
        <div class="block-title">内容摘要</div>
        <ul>
          <li>{summary}</li>
        </ul>
        """

        # Key concepts section
        concepts_html = ""
        if key_concepts:
            concepts_html = """
            <div class="block-title" style="margin-top: 20px;">关键概念</div>
            <ul>
            """
            for concept in key_concepts[:3]:  # Limit to 3 concepts
                term = concept.get("term", "")
                definition = concept.get("definition", "")
                concepts_html += f"<li><strong>{term}</strong>：{definition}</li>\n"
            concepts_html += "</ul>"

        return f"""
        <div class="panel-dark">
          <div class="section-title">
            <span class="icon">📖</span>
            内容摘要
          </div>
          {summary_html}
          {concepts_html}
        </div>
        """

    def _build_light_panel(self, key_points: list[str]) -> str:
        """Build light panel HTML (numbered insights)."""
        insights_html = []
        for i, point in enumerate(key_points[:3], 1):
            # Extract title and description
            parts = point.split("：", 1) if "：" in point else point.split(":", 1)
            title = parts[0].strip() if len(parts) == 2 else f"核心要点 {i}"
            desc = parts[1].strip() if len(parts) == 2 else point

            insight_html = f"""
            <div class="insight-item">
              <div class="insight-num">{i}</div>
              <div class="insight-content">
                <h4>{title}</h4>
                <p>{desc}</p>
              </div>
            </div>
            """
            insights_html.append(insight_html)

        return f"""
        <div class="panel-light">
          <div class="section-title">
            <span class="icon">💡</span>
            核心洞察
          </div>
          {''.join(insights_html)}
        </div>
        """

    def _build_highlight_bar(self, tags: list[str] | None) -> str:
        """Build bottom highlight bar HTML."""
        if not tags:
            return ""

        tags_text = " · ".join([f"#{tag}" for tag in tags[:5]])

        return f"""
        <div class="bottom-highlight">
          <div class="formula">
            <span class="eq">关键词</span> · {tags_text}
          </div>
          <div class="note">
            由 Learning Assistant 自动生成 · 智能知识提炼
          </div>
        </div>
        """

    def generate_card_image(
        self,
        title: str,
        summary: str,
        key_points: list[str],
        key_concepts: list[dict[str, str]] | None = None,
        tags: list[str] | None = None,
        source: str | None = None,
        url: str | None = None,
        output_path: Path | None = None,
        render_png: bool = True,
    ) -> Image.Image | None:
        """
        Generate knowledge card as PIL Image or HTML template.

        Args:
            title: Card title
            summary: Content summary
            key_points: List of key points
            key_concepts: Optional key concepts with definitions
            tags: Optional tags
            source: Optional source name
            url: Optional source URL
            output_path: Optional path to save image/HTML
            render_png: If True, render to PNG using Playwright; if False, save HTML template

        Returns:
            PIL Image object or None if saved to file

        Raises:
            ImportError: If Playwright is not installed (when render_png=True)
            RuntimeError: If rendering fails
        """
        logger.info(f"Generating visual knowledge card for: {title[:50]}...")

        # Generate HTML template
        html_content = self._generate_html(
            title=title,
            summary=summary,
            key_points=key_points,
            key_concepts=key_concepts,
            tags=tags,
            source=source,
            url=url,
        )

        if render_png:
            # Render to PNG using Playwright
            if output_path:
                png_path = output_path.with_suffix(".png")
            else:
                png_path = None

            try:
                return asyncio.run(
                    self.render_html_to_image(
                        html_content=html_content,
                        output_path=png_path,
                        width=self.width,
                        scale=2.0,
                    )
                )
            except ImportError:
                logger.warning(
                    "Playwright not installed, falling back to HTML template"
                )
                # Fallback to HTML template
                if output_path:
                    html_path = output_path.with_suffix(".html")
                    html_path.parent.mkdir(parents=True, exist_ok=True)
                    html_path.write_text(html_content, encoding="utf-8")
                    logger.info(f"HTML template saved to: {html_path}")
                return None
        else:
            # Save HTML template only
            if output_path:
                html_path = output_path.with_suffix(".html")
                html_path.parent.mkdir(parents=True, exist_ok=True)
                html_path.write_text(html_content, encoding="utf-8")
                logger.info(f"HTML template saved to: {html_path}")
                return None

            # Return HTML as string
            return None

    def generate_card_html(
        self,
        title: str,
        summary: str,
        key_points: list[str],
        key_concepts: list[dict[str, str]] | None = None,
        tags: list[str] | None = None,
        source: str | None = None,
        url: str | None = None,
    ) -> str:
        """
        Generate knowledge card HTML template.

        Args:
            title: Card title
            summary: Content summary
            key_points: List of key points
            key_concepts: Optional key concepts with definitions
            tags: Optional tags
            source: Optional source name
            url: Optional source URL

        Returns:
            Complete HTML string
        """
        return self._generate_html(
            title=title,
            summary=summary,
            key_points=key_points,
            key_concepts=key_concepts,
            tags=tags,
            source=source,
            url=url,
        )

    async def render_html_to_image(
        self,
        html_content: str,
        output_path: Path | None = None,
        width: int = 1200,
        scale: float = 2.0,
    ) -> Image.Image | None:
        """
        Render HTML content to PNG image using Playwright.

        Args:
            html_content: Complete HTML string
            output_path: Optional path to save PNG image
            width: Viewport width (should match HTML template width)
            scale: Scale factor for rendering (2.0 for high resolution)

        Returns:
            PIL Image object or None if saved to file

        Raises:
            ImportError: If Playwright is not installed
            RuntimeError: If rendering fails
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error(
                "Playwright not installed. Install with: pip install playwright && playwright install chromium"
            )
            raise ImportError(
                "Playwright required for PNG rendering. "
                "Install with: pip install playwright && playwright install chromium"
            )

        logger.info(f"Rendering HTML to image (width={width}, scale={scale})")

        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(html_content)
            html_path = Path(f.name)

        try:
            # Launch browser and render
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)

                # Set device scale factor for high resolution
                device_scale_factor = scale  # Use scale as device_scale_factor
                page = await browser.new_page(
                    viewport={"width": width, "height": 2000},
                    device_scale_factor=device_scale_factor,
                )

                # Load HTML file
                await page.goto(f"file://{html_path}")

                # Wait for fonts to load
                await page.wait_for_timeout(1000)

                # Take screenshot of poster element
                poster_element = await page.query_selector(".poster")
                if not poster_element:
                    logger.error("Poster element not found in HTML")
                    raise RuntimeError("Poster element not found in HTML")

                screenshot_bytes = await poster_element.screenshot(
                    type="png",
                )

                await browser.close()

            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))

            # Save or return
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(output_path, "PNG", quality=95)
                logger.info(f"Image saved to: {output_path}")
                return None
            else:
                return image

        except Exception as e:
            logger.error(f"Failed to render HTML to image: {e}")
            raise RuntimeError(f"Failed to render HTML to image: {e}") from e

        finally:
            # Clean up temporary file
            try:
                html_path.unlink()
            except Exception:
                pass