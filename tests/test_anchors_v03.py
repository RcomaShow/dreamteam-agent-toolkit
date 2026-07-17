from pathlib import Path
import subprocess
import tempfile
import unittest

from dreamteam.anchors import SourceAnchor, make_file_anchor, verify_anchor_file


class AnchorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "x.txt").write_text("a\nb\nc\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_anchor_roundtrip_and_stale_rejection(self):
        anchor = make_file_anchor(self.root, "x.txt", 2, 3)
        self.assertEqual(SourceAnchor.decode(anchor.encode()), anchor)
        self.assertTrue(verify_anchor_file(anchor, self.root))
        (self.root / "x.txt").write_text("a\nB\nc\n", encoding="utf-8")
        self.assertFalse(verify_anchor_file(anchor, self.root))

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            SourceAnchor("../secret", 1, 1, "abcdef0", "0" * 64)
        with self.assertRaises(ValueError):
            SourceAnchor.decode("file:../secret:L1-L1@blob:abcdef0#sha256:" + "0" * 64)


if __name__ == "__main__":
    unittest.main()
