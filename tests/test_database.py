import tempfile
import unittest
from pathlib import Path

from agenda.database import Database


class DatabaseTests(unittest.TestCase):
    def test_crud_and_json_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = Database(root / "first.db")
            contest_id = db.save_contest({
                "nome": "Concurso de exemplo",
                "orgao": "Órgão de teste",
                "status": "Previsto",
                "data_prevista": "2027-05-10",
            })
            discipline_id = db.add_discipline(contest_id, "Direito Constitucional")
            db.add_topic(discipline_id, "Direitos fundamentais", "Direitos fundamentais")
            self.assertEqual(len(db.get_program(contest_id)), 1)
            self.assertEqual(len(db.get_program(contest_id)[0]["topicos"]), 1)

            backup = root / "backup.json"
            db.export_json(backup)
            restored = Database(root / "restored.db")
            restored.import_json(backup)
            records = restored.list_contests()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["nome"], "Concurso de exemplo")
            self.assertEqual(
                restored.get_program(contest_id)[0]["topicos"][0]["nome_padronizado"],
                "Direitos fundamentais",
            )

    def test_delete_cascades_to_program_content(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "test.db")
            contest_id = db.save_contest({"nome": "Concurso"})
            discipline_id = db.add_discipline(contest_id, "Português")
            db.add_topic(discipline_id, "Interpretação de texto")
            db.delete_contest(contest_id)
            self.assertEqual(db.list_contests(), [])
            self.assertEqual(db.list_disciplines(contest_id), [])


if __name__ == "__main__":
    unittest.main()
