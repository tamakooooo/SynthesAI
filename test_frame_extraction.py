#!/usr/bin/env python3
"""
Test frame extraction specifically.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from learning_assistant.modules.video_summary.frame_extractor import FrameExtractor

# Test with a known video file
video_path = Path("data/downloads/在香港从100万到6个亿_都能住上什么样的房子.m4a")

if not video_path.exists():
    print(f"Video not found: {video_path}")
    print("Searching for any video file in data/downloads/...")

    downloads_dir = Path("data/downloads")
    if downloads_dir.exists():
        videos = list(downloads_dir.glob("*"))
        if videos:
            video_path = videos[0]
            print(f"Using: {video_path}")
        else:
            print("No video files found")
            sys.exit(1)
    else:
        print("Downloads directory not found")
        sys.exit(1)

print(f"Testing frame extraction with: {video_path}")

# Create extractor
extractor = FrameExtractor(
    output_dir=Path("data/frames"),
    output_format="jpg",
    quality=85,
)

# Test extracting a frame at 10 seconds
print("\nExtracting frame at 10 seconds...")
frame_path = extractor.extract_frame(
    video_path=video_path,
    timestamp=10.0,
    output_filename="test_frame",
)

if frame_path:
    print(f"✓ Success! Frame saved to: {frame_path}")
    print(f"  File size: {frame_path.stat().st_size / 1024:.1f} KB")
else:
    print("✗ Failed to extract frame")
    sys.exit(1)

# Test extracting frames for chapters
print("\nTesting chapter frame extraction...")
chapters = [
    {"title": "Intro", "start_time": "00:00", "summary": "..."},
    {"title": "Middle", "start_time": "01:00", "summary": "..."},
    {"title": "End", "start_time": "02:00", "summary": "..."},
]

updated_chapters = extractor.extract_frames_for_chapters(
    video_path=video_path,
    chapters=chapters,
    video_title="Test_Video",
)

print(f"\nResults:")
for i, chapter in enumerate(updated_chapters, 1):
    screenshot = chapter.get("screenshot_path")
    if screenshot:
        print(f"  Chapter {i}: ✓ {screenshot}")
    else:
        print(f"  Chapter {i}: ✗ No screenshot")

print("\nDone!")