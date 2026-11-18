import runpy
import unittest
from pathlib import Path
from xml.etree import ElementTree


render_manifest = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "packaging" / "build_msix.py")
)["render_manifest"]


class MsixManifestTests(unittest.TestCase):
    def test_manifest_contains_supplied_identity_and_opt_in_startup(self):
        xml = render_manifest("123.Agenda", "CN=Agenda", "Pesquisa & Concursos", "1.2.3.0")
        root = ElementTree.fromstring(xml)
        identity = root.find("{*}Identity")
        self.assertEqual(identity.attrib["Name"], "123.Agenda")
        self.assertEqual(identity.attrib["Publisher"], "CN=Agenda")
        self.assertEqual(identity.attrib["Version"], "1.2.3.0")
        self.assertEqual(root.findtext("./{*}Properties/{*}PublisherDisplayName"), "Pesquisa & Concursos")
        self.assertEqual(root.find(".//{*}StartupTask").attrib["Enabled"], "false")

    def test_rejects_invalid_store_versions(self):
        for version in ("0.9.0.0", "1.2.3.4", "1.2.3", "1.65536.0.0"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                render_manifest("123.Agenda", "CN=Agenda", "Agenda", version)
