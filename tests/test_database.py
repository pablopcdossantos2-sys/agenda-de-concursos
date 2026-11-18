import json
import sqlite3
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
                "data_prova": "2027-05-10",
            })
            discipline_id = db.add_discipline(contest_id, "Direito Constitucional")
            db.add_topic(discipline_id, "Direitos fundamentais", "Direitos fundamentais")
            db.replace_cargos(contest_id, [{
                "nome": "Médico",
                "nivel_escolaridade": "Superior",
                "requisitos": "Graduação em Medicina e CRM",
                "salario_inicial": "R$ 12.000,00",
                "jornada": "20 horas",
            }])
            db.save_user_profile({
                "niveis_escolaridade": ["Superior"],
                "cargos_desejados": ["Médico"],
                "observacoes": "CRM ativo",
            })
            self.assertEqual(db.list_contests("Médico")[0]["id"], contest_id)
            self.assertEqual(len(db.get_program(contest_id)), 1)
            self.assertEqual(len(db.get_program(contest_id)[0]["topicos"]), 1)

            backup = root / "backup.json"
            db.export_json(backup)
            restored = Database(root / "restored.db")
            restored.import_json(backup)
            records = restored.list_contests()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["nome"], "Concurso de exemplo")
            self.assertEqual(records[0]["data_prova"], "2027-05-10")
            self.assertEqual(
                restored.get_program(contest_id)[0]["topicos"][0]["nome_padronizado"],
                "Direitos fundamentais",
            )
            restored_cargos = restored.list_cargos(contest_id)
            self.assertEqual(restored_cargos[0]["nome"], "Médico")
            self.assertEqual(restored_cargos[0]["salario_inicial"], "R$ 12.000,00")
            self.assertEqual(restored.get_user_profile()["cargos_desejados"], ["Médico"])
            exported = json.loads(backup.read_text(encoding="utf-8"))
            self.assertNotIn("data_prevista", exported["concursos"][0])

    def test_manual_save_with_cargos_rolls_back_on_invalid_cargo(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "test.db")
            with self.assertRaises(ValueError):
                db.save_contest({"nome": "Cadastro incompleto", "cargos": [{"nome": ""}]})
            self.assertEqual(db.list_contests(), [])

            contest_id = db.save_contest({"nome": "Original", "cargos": [{"nome": "Analista"}]})
            with self.assertRaises(ValueError):
                db.save_contest({"nome": "Editado", "cargos": [{"nome": ""}]}, contest_id)
            self.assertEqual(db.get_contest(contest_id)["nome"], "Original")
            self.assertEqual([cargo["nome"] for cargo in db.list_cargos(contest_id)], ["Analista"])

    def test_search_is_accent_insensitive_and_treats_punctuation_literally(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "test.db")
            undated = db.save_contest({"nome": "Seleção 100%", "data_prova": ""})
            dated = db.save_contest({
                "nome": "Concurso com data",
                "data_prova": "2027-05-10",
                "cargos": [{"nome": "MÉDICO"}],
            })
            with db._connect() as connection:
                connection.execute("UPDATE concursos SET data_prova = '' WHERE id = ?", (undated,))
            self.assertEqual([row["id"] for row in db.list_contests()], [dated, undated])
            self.assertEqual([row["id"] for row in db.list_contests("selecao")], [undated])
            self.assertEqual([row["id"] for row in db.list_contests("medico")], [dated])
            self.assertEqual([row["id"] for row in db.list_contests("%")], [undated])

    def test_incomplete_or_inconsistent_backup_keeps_current_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = Database(root / "test.db")
            contest_id = db.save_contest({"nome": "Original"})
            db.set_setting("theme", "escuro")
            backup = root / "backup.json"
            backup.write_text('{"schema_version": 1}', encoding="utf-8")
            with self.assertRaises(ValueError):
                db.import_json(backup)
            payload = {
                "schema_version": 1,
                "concursos": [{"id": 1, "nome": "Outro"}],
                "disciplinas": [{"id": 1, "concurso_id": 999, "nome": "Sem concurso"}],
                "topicos": [],
            }
            backup.write_text(json.dumps(payload), encoding="utf-8-sig")
            with self.assertRaises(sqlite3.IntegrityError):
                db.import_json(backup)
            self.assertEqual(db.get_contest(contest_id)["nome"], "Original")
            self.assertEqual(db.get_setting("theme"), "escuro")

    def test_export_cannot_replace_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = Database(root / "test.db")
            contest_id = db.save_contest({"nome": "Original"})
            for path in (db.path, root / "test.db-wal", root / "test.db-shm"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    db.export_json(path)
            self.assertEqual(db.get_contest(contest_id)["nome"], "Original")

    def test_delete_cascades_to_program_content(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "test.db")
            contest_id = db.save_contest({"nome": "Concurso"})
            discipline_id = db.add_discipline(contest_id, "Português")
            db.add_topic(discipline_id, "Interpretação de texto")
            db.delete_contest(contest_id)
            self.assertEqual(db.list_contests(), [])
            self.assertEqual(db.list_disciplines(contest_id), [])

    def test_cargo_interest_survives_edit_backup_and_legacy_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = Database(root / "original.db")
            contest_id = db.save_contest({"nome": "Prefeitura"})
            db.replace_cargos(contest_id, [{"nome": "Médico", "salario_inicial": "R$ 12.000,00"}])
            with db._connect() as connection:
                connection.execute("ALTER TABLE cargos DROP COLUMN interesse")

            db = Database(db.path)
            cargo = db.list_cargos(contest_id)[0]
            self.assertEqual(cargo["interesse"], 0)
            db.save_cargo(contest_id, {**cargo, "interesse": True}, cargo["id"])
            del cargo["interesse"]
            db.save_cargo(contest_id, cargo, cargo["id"])
            self.assertEqual(db.list_cargos(contest_id)[0]["interesse"], 1)

            path = root / "backup.json"
            db.export_json(path)
            restored = Database(root / "restored.db")
            restored.import_json(path)
            self.assertEqual(restored.list_cargos(contest_id)[0]["interesse"], 1)
            self.assertEqual(restored.list_cargos(contest_id)[0]["salario_inicial"], "R$ 12.000,00")

            legacy = json.loads(path.read_text(encoding="utf-8"))
            del legacy["cargos"][0]["interesse"]
            path.write_text(json.dumps(legacy), encoding="utf-8")
            restored.import_json(path)
            self.assertEqual(restored.list_cargos(contest_id)[0]["interesse"], 0)


if __name__ == "__main__":
    unittest.main()
