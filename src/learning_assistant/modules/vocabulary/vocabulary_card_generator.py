"""
Vocabulary Visual Card Generator.

Generates editorial-style vocabulary learning cards with word grids,
context stories, and detailed word explanations.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from learning_assistant.modules.vocabulary.models import VocabularyOutput


class VocabularyCardGenerator:
    """
    Vocabulary-specific editorial visual card generator.

    Generates HTML/PNG cards with:
    - Word grid (brief display)
    - Context story panel
    - Detailed word explanations
    - Editorial typography and layout
    """

    def __init__(self, width: int = 1200):
        """Initialize vocabulary card generator.

        Args:
            width: Card width (fixed at 1200px for editorial style)
        """
        self.width = width
        logger.info(f"VocabularyCardGenerator initialized: width={width}")

    def _build_word_grid_minimal(self, vocabulary_cards: list[Any]) -> str:
        """Build minimal word grid (number + word only).

        Args:
            vocabulary_cards: List of VocabularyCard objects

        Returns:
            HTML string for minimal word grid
        """
        grid_items = []

        for i, card in enumerate(vocabulary_cards[:10], 1):  # Limit to 10 words
            item_html = f"""
            <div class="word-item">
              <div class="word-number">{i}</div>
              <div class="word-text">{card.word}</div>
            </div>
            """
            grid_items.append(item_html)

        return "\n".join(grid_items)

    def _build_word_list(self, vocabulary_cards: list[Any]) -> str:
        """Build word list for left panel (number + word + phonetic + pos + definition).

        Args:
            vocabulary_cards: List of VocabularyCard objects

        Returns:
            HTML string for word list
        """
        list_items = []

        for i, card in enumerate(vocabulary_cards[:10], 1):  # Show 10 words
            # Get phonetic
            phonetic = ""
            if card.phonetic:
                phonetic = card.phonetic.us or card.phonetic.uk or ""

            # Get definition (prefer zh)
            definition = card.definition.zh if card.definition.zh else (card.definition.en or "")

            # Build info line: pos · definition
            info_line = f'<span class="item-pos">{card.part_of_speech}</span> · {definition}'

            # Build phonetic HTML
            phonetic_html = f'<div class="item-phonetic">{phonetic}</div>' if phonetic else ''

            item_html = f"""
            <div class="word-list-item">
              <div class="item-header">
                <div class="item-number">{i}</div>
                <div class="item-word">{card.word}</div>
                {phonetic_html}
              </div>
              <div class="item-info">{info_line}</div>
            </div>
            """
            list_items.append(item_html)

        return "\n".join(list_items)

    def _build_word_focus(self, vocabulary_cards: list[Any]) -> str:
        """Build word focus for right panel (detailed explanations).

        Args:
            vocabulary_cards: List of VocabularyCard objects

        Returns:
            HTML string for word focus panel
        """
        focus_items = []

        # Show first 6 words in detail
        for i, card in enumerate(vocabulary_cards[:6], 1):
            # Get phonetic
            phonetic = ""
            if card.phonetic:
                phonetic = card.phonetic.us or card.phonetic.uk or ""

            # Get definition
            definition = card.definition.zh if card.definition.zh else (card.definition.en or "")

            # Get example
            example_text = ""
            if card.example_sentences and len(card.example_sentences) > 0:
                first_example = card.example_sentences[0]
                example_en = first_example.sentence
                example_zh = first_example.translation or ""

                # Highlight word
                example_en_highlighted = example_en.replace(
                    card.word, f"<strong>{card.word}</strong>"
                )

                example_text = example_en_highlighted
                if example_zh:
                    example_text += f" {example_zh}"

            focus_item_html = f"""
            <div class="focus-item">
              <div class="focus-header">
                <div class="focus-number">{i}</div>
                <div class="focus-word">{card.word}</div>
              </div>
              <div class="focus-def">{definition}</div>
              {f'<div class="focus-example">{example_text}</div>' if example_text else ''}
            </div>
            """
            focus_items.append(focus_item_html)

        return "\n".join(focus_items)
        """Build word grid section HTML.

        Args:
            vocabulary_cards: List of VocabularyCard objects

        Returns:
            HTML string for word grid section
        """
        grid_html = []

        for i, card in enumerate(vocabulary_cards[:10], 1):  # Limit to 10 words
            # Get definition (prefer zh, fallback to en)
            definition = card.definition.zh if card.definition.zh else (card.definition.en or "")

            # Get example sentence (prefer first one with translation)
            example_text = ""
            if card.example_sentences and len(card.example_sentences) > 0:
                first_example = card.example_sentences[0]
                example_en = first_example.sentence
                example_zh = first_example.translation or ""

                # Highlight the word in example
                example_en_highlighted = example_en.replace(
                    card.word, f"<strong>{card.word}</strong>"
                )

                if example_zh:
                    example_text = f"{example_en_highlighted} {example_zh}"
                else:
                    example_text = example_en_highlighted

            word_card_html = f"""
            <div class="word-card">
              <div class="word-header">
                <div class="word-number">{i}</div>
                <div class="word-text">{card.word}</div>
                <div class="word-pos">{card.part_of_speech}</div>
              </div>
              <div class="definition">{definition}</div>
              {f'<div class="example">{example_text}</div>' if example_text else ''}
            </div>
            """
            grid_html.append(word_card_html)

        return "\n".join(grid_html)

    def _build_story_panel(self, context_story: Any | None) -> tuple[str, str]:
        """Build story panel content.

        Args:
            context_story: ContextStory object or None

        Returns:
            Tuple of (story_title, story_content_with_highlights)
        """
        if not context_story:
            return "学习故事", "暂无上下文故事内容"

        story_title = context_story.title or "上下文故事"
        story_content = context_story.content

        # Remove markdown bold symbols (**)
        story_content = story_content.replace("**", "")

        # Highlight target words in story (if available)
        if context_story.target_words:
            for word in context_story.target_words[:10]:  # Limit highlights
                story_content = story_content.replace(
                    word, f"<strong>{word}</strong>"
                )

        return story_title, story_content

    def _build_detail_words(self, vocabulary_cards: list[Any]) -> str:
        """Build detailed word explanations section HTML.

        Args:
            vocabulary_cards: List of VocabularyCard objects

        Returns:
            HTML string for detailed words section
        """
        detail_html = []

        # Show first 3 words in detail
        for i, card in enumerate(vocabulary_cards[:3], 1):
            # Get phonetic (prefer US)
            phonetic = ""
            if card.phonetic:
                phonetic = card.phonetic.us or card.phonetic.uk or ""

            # Get definition
            definition = card.definition.zh if card.definition.zh else (card.definition.en or "")

            # Get example
            example_text = ""
            if card.example_sentences and len(card.example_sentences) > 0:
                first_example = card.example_sentences[0]
                example_en = first_example.sentence
                example_zh = first_example.translation or ""

                # Highlight word
                example_en_highlighted = example_en.replace(
                    card.word, f"<strong>{card.word}</strong>"
                )

                example_text = f"{example_en_highlighted}"
                if example_zh:
                    example_text += f" {example_zh}"

            detail_item_html = f"""
            <div class="detail-item">
              <div class="detail-header">
                <div class="detail-number">{i}</div>
                <div class="detail-word">{card.word}</div>
              </div>
              {f'<div class="detail-phonetic">{phonetic}</div>' if phonetic else ''}
              <div class="detail-def">{definition}</div>
              {f'<div class="detail-example">{example_text}</div>' if example_text else ''}
            </div>
            """
            detail_html.append(detail_item_html)

        return "\n".join(detail_html)

    def _build_tags(self, statistics: dict[str, Any]) -> str:
        """Build tags string from statistics.

        Args:
            statistics: Statistics dictionary

        Returns:
            Tags string (e.g., "#vocabulary · #10words · #intermediate")
        """
        tags = ["#vocabulary"]

        # Word count
        total_words = statistics.get("total_words", 0)
        tags.append(f"#{total_words}words")

        # Difficulty
        difficulty_dist = statistics.get("difficulty_distribution", {})
        if isinstance(difficulty_dist, dict) and difficulty_dist:
            primary_diff = max(
                difficulty_dist.items(),
                key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0
            )[0]
            tags.append(f"#{primary_diff}")
        else:
            tags.append("#intermediate")

        return " · ".join(tags)

    def generate_card_html(
        self,
        output: VocabularyOutput,
        created_at: datetime | None = None,
    ) -> str:
        """
        Generate vocabulary card HTML template (v2 layout).

        Args:
            output: VocabularyOutput object
            created_at: Optional creation timestamp

        Returns:
            Complete HTML string
        """
        # Load HTML template (v2)
        template_path = Path(__file__).parent / "vocabulary_card_template_v2.html"

        try:
            template_html = template_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}")
            raise RuntimeError(f"Vocabulary card template not found at {template_path}")

        # Prepare data
        vocabulary_cards = output.vocabulary_cards[:10]  # Limit to 10

        # Hero word (first word)
        hero_word = vocabulary_cards[0].word if vocabulary_cards else "词汇卡片"

        # Word count and difficulty
        word_count = output.statistics.get("total_words", len(output.vocabulary_cards))
        difficulty_dist = output.statistics.get("difficulty_distribution", {})
        difficulty = "intermediate"
        if isinstance(difficulty_dist, dict) and difficulty_dist:
            difficulty = max(
                difficulty_dist.items(),
                key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0
            )[0]

        # Build sections
        story_title, story_content = self._build_story_panel(output.context_story)
        word_list_html = self._build_word_list(vocabulary_cards)
        word_focus_html = self._build_word_focus(vocabulary_cards)
        tags_str = self._build_tags(output.statistics)
        created_at_str = (created_at or datetime.now()).strftime("%Y-%m-%d %H:%M")

        # Replace template placeholders
        html_content = template_html.replace("{hero_word}", hero_word)
        html_content = html_content.replace("{word_count}", str(word_count))
        html_content = html_content.replace("{difficulty}", difficulty)
        html_content = html_content.replace("{story_title}", story_title)
        html_content = html_content.replace("{story_content}", story_content)
        html_content = html_content.replace("{word_list}", word_list_html)
        html_content = html_content.replace("{word_focus}", word_focus_html)
        html_content = html_content.replace("{tags}", tags_str)
        html_content = html_content.replace("{created_at}", created_at_str)

        logger.info(f"Vocabulary card HTML generated (v2): {hero_word}")
        return html_content

    async def render_html_to_image(
        self,
        html_content: str,
        output_path: Path | None,
        width: int = 1200,
        scale: float = 2.0,
    ) -> None:
        """
        Render HTML to PNG image using Playwright.

        Args:
            html_content: HTML string
            output_path: Path to save PNG image
            width: Viewport width (1200px)
            scale: Scale factor (2.0 for high resolution)

        Raises:
            ImportError: If Playwright not installed
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright not installed, PNG rendering unavailable")
            raise ImportError("Playwright is required for PNG rendering. Install: pip install playwright && playwright install chromium")

        if not output_path:
            logger.warning("No output path specified, skipping PNG rendering")
            return

        logger.info(f"Rendering vocabulary card to PNG: width={width}, scale={scale}")

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Set viewport (slightly larger than expected content height)
            await page.set_viewport_size({"width": width, "height": 1250})

            # Load HTML content
            await page.set_content(html_content, wait_until="networkidle")

            # Wait for fonts to load
            await page.wait_for_timeout(500)

            # Debug: Get actual page height
            page_height = await page.evaluate("document.documentElement.scrollHeight")
            logger.debug(f"Actual page height: {page_height}px")

            # Take screenshot
            await page.screenshot(
                path=str(output_path),
                full_page=True,
                scale="device",  # High resolution (2x on high DPI devices)
            )

            await browser.close()

        logger.info(f"Vocabulary card PNG saved to: {output_path}")