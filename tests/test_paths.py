import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agenda.paths import app_data_dir, app_root


class PortablePathTests(unittest.TestCase):
    def test_frozen_app_keeps_database_folder_next_to_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "Portable" / "Agenda de Concursos.exe"
            executable.parent.mkdir()
            with patch("agenda.paths.sys.frozen", True, create=True), patch(
                "agenda.paths.sys.executable", str(executable)
            ):
                self.assertTrue(os.path.samefile(app_root(), executable.parent))
                data_dir = app_data_dir()
                self.assertTrue(os.path.samefile(data_dir, executable.parent / "data"))
                self.assertTrue(data_dir.is_dir())

    def test_source_root_is_repository_directory(self):
        self.assertEqual(app_root(), Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    unittest.main()
