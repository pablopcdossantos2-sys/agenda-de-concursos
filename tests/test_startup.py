import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agenda.startup import disable_startup, enable_startup, startup_enabled


class StartupTests(unittest.TestCase):
    def test_enable_and_disable_creates_and_removes_vbs_script(self):
        with tempfile.TemporaryDirectory(prefix="Agenda de Concursos ") as directory:
            with patch("agenda.startup.sys.platform", "win32"), patch.dict(
                os.environ, {"APPDATA": directory}
            ):
                destination = enable_startup()
                self.assertTrue(destination.exists())
                self.assertEqual(destination.name, "Agenda de Concursos.vbs")
                script = destination.read_text(encoding="utf-8")
                self.assertIn("WshShell.Run", script)
                self.assertIn(", 0, False", script)
                self.assertTrue(startup_enabled())

                disable_startup()
                self.assertFalse(destination.exists())
                self.assertFalse(startup_enabled())

    def test_non_windows_rejects_startup_changes(self):
        with patch("agenda.startup.sys.platform", "linux"):
            with self.assertRaises(OSError):
                enable_startup()
            with self.assertRaises(OSError):
                disable_startup()


if __name__ == "__main__":
    unittest.main()
