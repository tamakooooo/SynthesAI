"""
Tests for Vocabulary Learning Module - Phonetic Lookup.

Tests the three-layer phonetic lookup system:
1. Local dictionary
2. Free Dictionary API
3. LLM fallback
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, mock_open
import aiohttp

from learning_assistant.modules.vocabulary.phonetic_lookup import PhoneticLookup
from learning_assistant.modules.vocabulary.models import Phonetic


class TestPhoneticLookupInit:
    """Test PhoneticLookup initialization."""

    def test_init_without_local_dict(self):
        """Test initialization without local dictionary."""
        lookup = PhoneticLookup()

        assert lookup.local_dict_path is None
        assert lookup.api_url == "https://api.dictionaryapi.dev/api/v2/entries/en/"
        assert lookup.llm_service is None
        assert lookup.local_dictionary == {}

    def test_init_with_custom_api_url(self):
        """Test initialization with custom API URL."""
        custom_url = "https://custom.api.com/"
        lookup = PhoneticLookup(api_url=custom_url)

        assert lookup.api_url == custom_url

    def test_init_with_llm_service(self):
        """Test initialization with LLM service."""
        mock_llm = Mock()
        lookup = PhoneticLookup(llm_service=mock_llm)

        assert lookup.llm_service == mock_llm

    def test_init_with_nonexistent_local_dict(self, tmp_path):
        """Test initialization with non-existent local dictionary file."""
        non_existent = tmp_path / "non_existent.json"
        lookup = PhoneticLookup(local_dict_path=non_existent)

        # Should not load anything
        assert lookup.local_dictionary == {}

    def test_init_with_valid_local_dict(self, tmp_path):
        """Test initialization with valid local dictionary file."""
        # Create test dictionary
        dict_data = {
            "test": {"us": "/test/", "uk": "/test/uk/"},
            "hello": {"us": "/həˈloʊ/", "uk": "/həˈləʊ/"}
        }
        dict_file = tmp_path / "test_dict.json"
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")

        lookup = PhoneticLookup(local_dict_path=dict_file)

        # Should load dictionary
        assert len(lookup.local_dictionary) == 2
        assert "test" in lookup.local_dictionary
        assert lookup.local_dictionary["test"].us == "/test/"


class TestPhoneticLookupLocal:
    """Test local dictionary lookup."""

    def test_lookup_local_word_exists(self, tmp_path):
        """Test looking up word that exists in local dictionary."""
        dict_data = {
            "transform": {"us": "/trænsˈfɔrm/", "uk": "/trænsˈfɔːm/"}
        }
        dict_file = tmp_path / "dict.json"
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")

        lookup = PhoneticLookup(local_dict_path=dict_file)
        result = lookup._lookup_local("transform")

        assert result is not None
        assert result.us == "/trænsˈfɔrm/"
        assert result.uk == "/trænsˈfɔːm/"

    def test_lookup_local_word_not_exists(self, tmp_path):
        """Test looking up word that doesn't exist in local dictionary."""
        dict_data = {"test": {"us": "/test/", "uk": None}}
        dict_file = tmp_path / "dict.json"
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")

        lookup = PhoneticLookup(local_dict_path=dict_file)
        result = lookup._lookup_local("nonexistent")

        assert result is None

    def test_lookup_local_case_insensitive(self, tmp_path):
        """Test that local lookup is case-insensitive."""
        dict_data = {
            "Transform": {"us": "/trænsˈfɔrm/", "uk": None}
        }
        dict_file = tmp_path / "dict.json"
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")

        lookup = PhoneticLookup(local_dict_path=dict_file)

        # Should find word regardless of case
        result = lookup._lookup_local("TRANSFORM")
        assert result is not None
        assert result.us == "/trænsˈfɔrm/"


class TestPhoneticLookupAPI:
    """Test Free Dictionary API lookup."""

    @pytest.mark.asyncio
    async def test_lookup_api_success(self):
        """Test successful API lookup."""
        lookup = PhoneticLookup()

        # Mock API response
        mock_response_data = [
            {
                "word": "transform",
                "phonetics": [
                    {
                        "text": "/trænsˈfɔrm/",
                        "audio": "https://api.com/us.mp3"
                    },
                    {
                        "text": "/trænsˈfɔːm/",
                        "audio": "https://api.com/uk.mp3"
                    }
                ]
            }
        ]

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch("aiohttp.ClientSession") as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await lookup._lookup_api("transform")

                # Should extract phonetics from API response
                assert result is not None

    @pytest.mark.asyncio
    async def test_lookup_api_not_found(self):
        """Test API lookup when word not found (404)."""
        lookup = PhoneticLookup()

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response

            with patch("aiohttp.ClientSession") as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await lookup._lookup_api("nonexistentword123")

                # Should return None for 404
                assert result is None

    @pytest.mark.asyncio
    async def test_lookup_api_error(self):
        """Test API lookup when request fails."""
        lookup = PhoneticLookup()

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Connection failed")

            with patch("aiohttp.ClientSession") as mock_session:
                mock_session.return_value.__aenter__.return_value.get = mock_get

                result = await lookup._lookup_api("test")

                # Should return None on error
                assert result is None


class TestPhoneticLookupLLM:
    """Test LLM fallback lookup."""

    @pytest.mark.asyncio
    async def test_lookup_llm_success(self):
        """Test successful LLM phonetic generation."""
        mock_llm = AsyncMock()
        mock_llm.call.return_value = '''
        {
            "us": "/trænsˈfɔrm/",
            "uk": "/trænsˈfɔːm/"
        }
        '''

        lookup = PhoneticLookup(llm_service=mock_llm)
        result = await lookup._lookup_llm("transform")

        assert result is not None
        assert result.us == "/trænsˈfɔrm/"
        assert result.uk == "/trænsˈfɔːm/"

    @pytest.mark.asyncio
    async def test_lookup_llm_no_service(self):
        """Test LLM lookup when no LLM service available."""
        lookup = PhoneticLookup(llm_service=None)
        result = await lookup._lookup_llm("test")

        # Should return None when no LLM service
        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_llm_invalid_json(self):
        """Test LLM lookup when LLM returns invalid JSON."""
        mock_llm = AsyncMock()
        mock_llm.call.return_value = "Not a valid JSON"

        lookup = PhoneticLookup(llm_service=mock_llm)
        result = await lookup._lookup_llm("test")

        # Should return None on JSON parse error
        assert result is None


class TestPhoneticLookupFull:
    """Test full three-layer lookup."""

    @pytest.mark.asyncio
    async def test_lookup_local_found(self, tmp_path):
        """Test lookup stops at local dictionary when found."""
        dict_data = {"test": {"us": "/test/", "uk": None}}
        dict_file = tmp_path / "dict.json"
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")

        lookup = PhoneticLookup(local_dict_path=dict_file)

        # Mock API and LLM to track calls
        with patch.object(lookup, '_lookup_api') as mock_api:
            with patch.object(lookup, '_lookup_llm') as mock_llm:
                result = await lookup.lookup("test")

                # Should find in local dict
                assert result is not None
                assert result.us == "/test/"

                # Should not call API or LLM
                mock_api.assert_not_called()
                mock_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_lookup_api_found(self, tmp_path):
        """Test lookup uses API when local dictionary fails."""
        dict_data = {}  # Empty local dict
        dict_file = tmp_path / "dict.json"
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")

        lookup = PhoneticLookup(local_dict_path=dict_file)

        # Mock API to return result
        api_result = Phonetic(us="/api/", uk=None)
        with patch.object(lookup, '_lookup_api', return_value=api_result):
            with patch.object(lookup, '_lookup_llm') as mock_llm:
                result = await lookup.lookup("test")

                # Should find via API
                assert result is not None
                assert result.us == "/api/"

                # Should not call LLM
                mock_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_lookup_llm_fallback(self, tmp_path):
        """Test lookup falls back to LLM when both local and API fail."""
        dict_data = {}  # Empty local dict
        dict_file = tmp_path / "dict.json"
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")

        mock_llm = AsyncMock()
        lookup = PhoneticLookup(
            local_dict_path=dict_file,
            llm_service=mock_llm
        )

        # Mock API to return None (not found)
        llm_result = Phonetic(us="/llm/", uk=None)
        with patch.object(lookup, '_lookup_api', return_value=None):
            with patch.object(lookup, '_lookup_llm', return_value=llm_result):
                result = await lookup.lookup("test")

                # Should fall back to LLM
                assert result is not None
                assert result.us == "/llm/"

    @pytest.mark.asyncio
    async def test_lookup_all_fail(self, tmp_path):
        """Test lookup returns None when all layers fail."""
        dict_data = {}
        dict_file = tmp_path / "dict.json"
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")

        lookup = PhoneticLookup(local_dict_path=dict_file)

        # Mock all layers to fail
        with patch.object(lookup, '_lookup_api', return_value=None):
            with patch.object(lookup, '_lookup_llm', return_value=None):
                result = await lookup.lookup("nonexistent")

                # Should return None when all fail
                assert result is None


class TestPhoneticLookupEdgeCases:
    """Test edge cases and error handling."""

    def test_load_local_dict_malformed_json(self, tmp_path):
        """Test handling malformed JSON in local dictionary."""
        dict_file = tmp_path / "malformed.json"
        dict_file.write_text("{ invalid json }", encoding="utf-8")

        # Should not crash, just log error and continue
        lookup = PhoneticLookup(local_dict_path=dict_file)
        assert lookup.local_dictionary == {}

    def test_load_local_dict_missing_fields(self, tmp_path):
        """Test handling entries with missing phonetic fields."""
        dict_data = {
            "test": {},  # No 'us' or 'uk' fields
            "hello": {"us": "/həˈloʊ/"}  # Missing 'uk'
        }
        dict_file = tmp_path / "dict.json"
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")

        lookup = PhoneticLookup(local_dict_path=dict_file)

        # Should load with None for missing fields
        assert len(lookup.local_dictionary) == 2

    @pytest.mark.asyncio
    async def test_concurrent_lookups(self):
        """Test handling multiple concurrent lookups."""
        lookup = PhoneticLookup()

        # Mock API to simulate slow response
        async def slow_api_lookup(word):
            await asyncio.sleep(0.1)
            return Phonetic(us="/api/", uk=None)

        with patch.object(lookup, '_lookup_api', side_effect=slow_api_lookup):
            # Make multiple concurrent lookups
            tasks = [lookup.lookup(f"word{i}") for i in range(5)]
            results = await asyncio.gather(*tasks)

            # All should complete successfully
            assert len(results) == 5
            assert all(r is not None for r in results)