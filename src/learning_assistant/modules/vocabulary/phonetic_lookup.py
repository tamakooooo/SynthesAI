"""
Phonetic Lookup - Multi-layer phonetic transcription lookup.

This module provides phonetic transcription lookup with a three-layer
fallback mechanism:
1. Local dictionary (fast, free)
2. Free Dictionary API (online, free)
3. LLM generation (fallback, accurate)
"""

from pathlib import Path
from typing import Optional

import aiohttp
from loguru import logger

from learning_assistant.modules.vocabulary.models import Phonetic


class PhoneticLookup:
    """
    Phonetic lookup with multi-layer fallback.

    Provides phonetic transcriptions through:
    1. Local JSON dictionary (offline, fast)
    2. Free Dictionary API (online, free)
    3. LLM generation (fallback, accurate)

    Attributes:
        local_dict_path: Path to local dictionary JSON file
        api_url: Free Dictionary API base URL
        llm_service: LLM service for fallback generation
        local_dictionary: Loaded local dictionary data
    """

    def __init__(
        self,
        local_dict_path: Optional[Path] = None,
        api_url: str = "https://api.dictionaryapi.dev/api/v2/entries/en/",
        llm_service: Optional[any] = None,
    ):
        """
        Initialize phonetic lookup.

        Args:
            local_dict_path: Path to local dictionary JSON file
            api_url: Free Dictionary API base URL
            llm_service: LLM service instance for fallback
        """
        self.local_dict_path = local_dict_path
        self.api_url = api_url
        self.llm_service = llm_service

        # Load local dictionary
        self.local_dictionary: dict[str, Phonetic] = {}
        if local_dict_path and local_dict_path.exists():
            self._load_local_dictionary()

        logger.info(
            f"PhoneticLookup initialized (local_dict: {local_dict_path}, api: {api_url})"
        )

    def _load_local_dictionary(self) -> None:
        """
        Load local dictionary from JSON file.

        Expected format:
        {
            "word": {"us": "/.../", "uk": "/.../"},
            ...
        }
        """
        import json

        try:
            with open(self.local_dict_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for word, phonetic_data in data.items():
                self.local_dictionary[word.lower()] = Phonetic(
                    us=phonetic_data.get("us"),
                    uk=phonetic_data.get("uk"),
                )

            logger.info(
                f"Loaded {len(self.local_dictionary)} words from local dictionary"
            )

        except Exception as e:
            logger.error(f"Failed to load local dictionary: {e}")
            self.local_dictionary = {}

    async def lookup(self, word: str) -> Phonetic:
        """
        Look up phonetic transcription for a word.

        Uses three-layer fallback:
        1. Local dictionary (offline, fast)
        2. Free Dictionary API (online, free)
        3. LLM generation (fallback, accurate)

        Args:
            word: The word to look up

        Returns:
            Phonetic object with US and UK transcriptions
        """
        word = word.lower().strip()

        # Layer 1: Local dictionary
        phonetic = self._lookup_local(word)
        if phonetic and (phonetic.us or phonetic.uk):
            logger.debug(f"Phonetic found in local dictionary: {word}")
            return phonetic

        # Layer 2: Free Dictionary API
        phonetic = await self._lookup_api(word)
        if phonetic and (phonetic.us or phonetic.uk):
            logger.debug(f"Phonetic found via API: {word}")
            return phonetic

        # Layer 3: LLM generation
        if self.llm_service:
            phonetic = await self._lookup_llm(word)
            if phonetic:
                logger.debug(f"Phonetic generated via LLM: {word}")
                return phonetic

        # Return empty phonetic if all methods fail
        logger.warning(f"Phonetic lookup failed for: {word}")
        return Phonetic(us=None, uk=None)

    def _lookup_local(self, word: str) -> Optional[Phonetic]:
        """
        Look up word in local dictionary.

        Args:
            word: The word to look up

        Returns:
            Phonetic object or None if not found
        """
        return self.local_dictionary.get(word.lower())

    async def _lookup_api(self, word: str) -> Optional[Phonetic]:
        """
        Look up word using Free Dictionary API.

        API documentation: https://dictionaryapi.dev/

        Args:
            word: The word to look up

        Returns:
            Phonetic object or None if not found
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}{word}"
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Parse phonetic data
                        if data and len(data) > 0:
                            entry = data[0]
                            phonetics_list = entry.get("phonetics", [])

                            us_phonetic = None
                            uk_phonetic = None

                            # Try to find US and UK phonetics
                            for phonetic_item in phonetics_list:
                                text = phonetic_item.get("text", "")
                                if not text:
                                    continue

                                # Check audio URL for region
                                audio = phonetic_item.get("audio", "")
                                if "us" in audio.lower():
                                    us_phonetic = text
                                elif "uk" in audio.lower():
                                    uk_phonetic = text
                                else:
                                    # Default to US if no region specified
                                    if not us_phonetic:
                                        us_phonetic = text

                            # If no specific UK phonetic found, use the same as US
                            if not uk_phonetic:
                                uk_phonetic = us_phonetic

                            return Phonetic(us=us_phonetic, uk=uk_phonetic)

        except aiohttp.ClientError as e:
            logger.warning(f"API lookup failed for '{word}': {e}")

        except Exception as e:
            logger.error(f"Unexpected error during API lookup for '{word}': {e}")

        return None

    async def _lookup_llm(self, word: str) -> Optional[Phonetic]:
        """
        Generate phonetic transcription using LLM.

        Args:
            word: The word to look up

        Returns:
            Phonetic object or None if generation fails
        """
        if not self.llm_service:
            return None

        try:
            # Create prompt for phonetic generation
            prompt = f"""Generate IPA phonetic transcriptions for the English word "{word}".

Return ONLY a JSON object with this exact format:
{{"us": "/American phonetic/", "uk": "/British phonetic/"}}

Example for "hello":
{{"us": "/həˈloʊ/", "uk": "/həˈləʊ/"}}

Word: {word}"""

            # Call LLM
            response = self.llm_service.call(
                prompt=prompt,
                model=self.llm_service.model,
                temperature=0.1,  # Low temperature for accuracy
                max_tokens=100,
            )

            # Parse response
            import json

            content = response.content.strip()

            # Extract JSON from response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            data = json.loads(json_str)

            return Phonetic(
                us=data.get("us"),
                uk=data.get("uk"),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for phonetic: {e}")

        except Exception as e:
            logger.error(f"LLM phonetic generation failed for '{word}': {e}")

        return None

    def add_to_local_dictionary(self, word: str, phonetic: Phonetic) -> None:
        """
        Add word to local dictionary cache.

        Args:
            word: The word
            phonetic: Phonetic transcription
        """
        self.local_dictionary[word.lower()] = phonetic

        # Optionally save to file
        if self.local_dict_path:
            self._save_local_dictionary()

    def _save_local_dictionary(self) -> None:
        """Save local dictionary to JSON file."""
        import json

        if not self.local_dict_path:
            return

        try:
            # Create parent directory if needed
            self.local_dict_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to serializable format
            data = {
                word: {"us": p.us, "uk": p.uk}
                for word, p in self.local_dictionary.items()
            }

            with open(self.local_dict_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(data)} words to local dictionary")

        except Exception as e:
            logger.error(f"Failed to save local dictionary: {e}")


# Convenience function for synchronous usage
def lookup_phonetic_sync(
    word: str,
    local_dict_path: Optional[Path] = None,
    api_url: str = "https://api.dictionaryapi.dev/api/v2/entries/en/",
) -> Phonetic:
    """
    Synchronous phonetic lookup.

    Args:
        word: The word to look up
        local_dict_path: Path to local dictionary
        api_url: API URL

    Returns:
        Phonetic object
    """
    import asyncio

    lookup = PhoneticLookup(local_dict_path=local_dict_path, api_url=api_url)
    return asyncio.run(lookup.lookup(word))
