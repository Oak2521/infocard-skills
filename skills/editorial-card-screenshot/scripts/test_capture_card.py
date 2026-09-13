import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import capture_card


class CaptureTests(unittest.TestCase):
    def test_explicit_missing_browser_fails_without_fallback(self):
        with patch("capture_card.shutil.which", return_value=None) as which:
            with self.assertRaises(FileNotFoundError):
                capture_card.find_browser({"CHROME_BIN": "missing-browser", "PATH": ""})
            self.assertEqual(which.call_count, 1)

    def test_path_discovery(self):
        with patch("capture_card.shutil.which", side_effect=lambda name, **kw: "/usr/bin/chromium" if name == "chromium" else None):
            self.assertEqual(capture_card.find_browser({"PATH": "/usr/bin"}), "/usr/bin/chromium")

    def test_windows_known_location(self):
        with tempfile.TemporaryDirectory() as directory:
            exe = Path(directory) / "Microsoft/Edge/Application/msedge.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"test")
            with patch("capture_card.shutil.which", return_value=None), patch("capture_card.os.access", return_value=True):
                self.assertEqual(capture_card.find_browser({"PROGRAMFILES": directory, "PATH": ""}), str(exe))

    def test_capture_preserves_spaces_and_encodes_file_url(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "card # one.html"
            output = Path(directory) / "result one.png"
            source.write_text("<h1>Card</h1>")
            def render(argv, **kwargs):
                self.assertIn("--window-size=1500,2000", argv)
                self.assertIn("%23", argv[-1])
                self.assertTrue(argv[-1].endswith("#ratio=3:4"))
                output.write_bytes(b"png")
            with patch("capture_card.find_browser", return_value="browser path"), patch("capture_card.subprocess.run", side_effect=render):
                self.assertEqual(capture_card.capture(source, output, "3:4"), output.resolve())

    def test_successful_exit_without_output_is_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "card.html"
            source.write_text("<h1>Card</h1>")
            with patch("capture_card.find_browser", return_value="browser"), patch("capture_card.subprocess.run"):
                with self.assertRaises(RuntimeError):
                    capture_card.capture(source, Path(directory) / "missing.png", "1:1")


if __name__ == "__main__":
    unittest.main()
