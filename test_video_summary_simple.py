#!/usr/bin/env python3
"""
Simple test script for video summary feature.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from learning_assistant.api import AgentAPI


async def test_video_summary():
    """Test video summary with the user's requested video."""
    api = AgentAPI()

    # User's requested video
    url = "https://www.bilibili.com/video/BV18zfCBQERe/"

    print(f"Testing video summary for: {url}")
    print("=" * 60)

    try:
        result = await api.summarize_video(url=url)

        print(f"\nSuccess!")
        print(f"Status: {result.status}")
        print(f"Title: {result.title}")
        print(f"Files: {result.files}")
        print(f"Timestamp: {result.timestamp}")

        if result.summary:
            print(f"\nSummary preview:")
            print("-" * 60)
            content = result.summary.get("content", "")
            print(content[:500] + "..." if len(content) > 500 else content)

        return True

    except Exception as e:
        print(f"\nError: {type(e).__name__}")
        print(f"Message: {e}")

        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())

        return False


if __name__ == "__main__":
    success = asyncio.run(test_video_summary())
    sys.exit(0 if success else 1)