"""
Visual Card Adapter for Vocabulary Module.

Converts VocabularyOutput data to VisualCardGenerator-compatible format.
"""

from typing import Any

from learning_assistant.modules.vocabulary.models import VocabularyOutput


def vocabulary_output_to_card_data(output: VocabularyOutput) -> dict[str, Any]:
    """
    Convert VocabularyOutput to VisualCardGenerator-compatible data format.

    This adapter transforms vocabulary learning output into a format suitable
    for generating editorial-style visual knowledge cards.

    Args:
        output: VocabularyOutput object containing vocabulary_cards, context_story, and statistics

    Returns:
        dict with keys compatible with VisualCardGenerator.generate_card_html():
            - title: Card title (e.g., "单词学习 · innovative词汇集")
            - summary: Context story content
            - key_points: Word list in brief format (word (pos): definition)
            - key_concepts: None (not used for vocabulary cards)
            - tags: Statistics tags
            - source: "Learning Assistant"
            - url: None (vocabulary learning has no URL)

    Example:
        >>> output = VocabularyOutput(...)
        >>> card_data = vocabulary_output_to_card_data(output)
        >>> generator.generate_card_html(**card_data)
    """
    # Extract vocabulary cards (limit to 10 for display)
    max_words = 10
    vocabulary_cards = output.vocabulary_cards[:max_words]

    # Convert word cards to key_points format: "word (pos): zh_definition"
    key_points = [
        f"{card.word} ({card.part_of_speech}): {card.definition.zh}"
        for card in vocabulary_cards
    ]

    # Extract context story as summary
    summary = ""
    if output.context_story:
        # Truncate long story for visual card display (150 chars max)
        story_content = output.context_story.content
        if len(story_content) > 150:
            summary = story_content[:150] + "..."
        else:
            summary = story_content

    # Extract statistics as tags
    tags = []

    # Add vocabulary tag
    tags.append("vocabulary")

    # Add word count tag
    total_words = output.statistics.get("total_words", len(vocabulary_cards))
    tags.append(f"{total_words} words")

    # Add difficulty tag (primary difficulty level)
    difficulty_dist = output.statistics.get("difficulty_distribution", {})
    if isinstance(difficulty_dist, dict):
        # Find the primary difficulty (highest percentage)
        primary_difficulty = max(
            difficulty_dist.items(),
            key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0
        )[0] if difficulty_dist else "intermediate"
        tags.append(primary_difficulty)
    else:
        tags.append("intermediate")

    # Generate title
    if vocabulary_cards:
        # Use first word as title indicator
        first_word = vocabulary_cards[0].word
        title = f"单词学习 · {first_word}词汇集"
    else:
        title = "单词学习 · 词汇卡片"

    # Return VisualCard-compatible data
    return {
        "title": title,
        "summary": summary,
        "key_points": key_points,
        "key_concepts": None,  # Not used for vocabulary cards
        "tags": tags,
        "source": "SynthesAI",
        "url": None,  # Vocabulary learning has no source URL
    }