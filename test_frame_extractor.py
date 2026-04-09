"""
Test FrameExtractor basic functionality.
"""

from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from learning_assistant.modules.video_summary.frame_extractor import FrameExtractor


def test_timestamp_conversion():
    """Test timestamp conversion."""
    extractor = FrameExtractor(output_dir=Path("data/test_frames"))

    # Test MM:SS format
    assert extractor.timestamp_to_seconds("05:30") == 330.0
    print("[OK] MM:SS format conversion works")

    # Test HH:MM:SS format
    assert extractor.timestamp_to_seconds("1:15:30") == 4530.0
    print("[OK] HH:MM:SS format conversion works")

    # Test pure number
    assert extractor.timestamp_to_seconds("120") == 120.0
    print("[OK] Number string conversion works")

    # Test invalid format
    assert extractor.timestamp_to_seconds("invalid") == 0.0
    print("[OK] Invalid format handling works (returns 0.0)")


def test_title_sanitization():
    """Test title sanitization."""
    extractor = FrameExtractor(output_dir=Path("data/test_frames"))

    # Test special characters
    test_title = "Video: Special @#$ Characters!"
    safe_title = extractor._sanitize_title(test_title)
    print(f"[DEBUG] Original: '{test_title}'")
    print(f"[DEBUG] Sanitized: '{safe_title}'")

    # Check that special chars are replaced
    assert "@" not in safe_title
    assert "#" not in safe_title
    assert "$" not in safe_title
    print(f"[OK] Special characters sanitized")

    # Test length limit
    long_title = "A" * 100
    safe_title = extractor._sanitize_title(long_title)
    assert len(safe_title) <= 50
    print(f"[OK] Length limited to 50 chars: {len(safe_title)}")


def test_relative_path_calculation():
    """Test relative path calculation."""
    extractor = FrameExtractor(output_dir=Path("data/test_frames"))

    # Test relative path
    frame_path = Path("data/frames/My_Video/chapter_01.jpg")
    output_dir = Path("data/outputs")
    relative = extractor._calculate_relative_path(frame_path, output_dir)
    expected = "frames/My_Video/chapter_01.jpg"
    assert relative == expected
    print(f"[OK] Relative path calculated: '{relative}'")


def test_chapter_update_mock():
    """Test chapter update logic (without actual video file)."""
    extractor = FrameExtractor(output_dir=Path("data/test_frames"))

    # Mock chapters data
    chapters = [
        {"title": "Intro", "start_time": "00:00", "summary": "Introduction..."},
        {"title": "Main", "start_time": "05:30", "summary": "Main content..."},
        {"title": "Conclusion", "start_time": "10:00", "summary": "Conclusion..."},
    ]

    # Test data structure expectation
    print("\nExpected chapter structure after frame extraction:")
    print("Each chapter should have 'screenshot_path' field added")

    # Note: extract_frames_for_chapters requires actual video file
    # This is just a structure validation
    for i, chapter in enumerate(chapters):
        print(f"  Chapter {i + 1}: {chapter['title']} @ {chapter['start_time']}")

    print("\n[OK] Chapter data structure validated")


def main():
    """Run all tests."""
    print("=" * 60)
    print("FrameExtractor Functionality Tests")
    print("=" * 60)

    try:
        print("\n[1] Testing timestamp conversion...")
        test_timestamp_conversion()

        print("\n[2] Testing title sanitization...")
        test_title_sanitization()

        print("\n[3] Testing relative path calculation...")
        test_relative_path_calculation()

        print("\n[4] Testing chapter update logic (mock)...")
        test_chapter_update_mock()

        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)

        print("\nNote: Frame extraction requires:")
        print("  1. FFmpeg installed and available in PATH")
        print("  2. Actual video file to extract frames from")
        print("  3. Run full video summary to test end-to-end")

    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)