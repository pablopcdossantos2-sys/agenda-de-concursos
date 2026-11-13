import tempfile
import unittest
from pathlib import Path

from agenda.database import Database
from agenda.services.contest_payload import normalize_contest_payload, parse_contest_json


VALID_PAYLOAD = {
    "schema_version": 1,
    "concurso": {
        "nome": "Concurso de exemplo",
        "orgao": "Órgão de teste",
        "status": "Edital publicado",
        "data_prova": "2027-05-10",
        "prioridade": False,
        "cargos": [
            {
                "nome": "Médico",
                "nivel_escolaridade": "Superior",
                "requisitos": "Graduação em Medicina e CRM",
                "salario_inicial": "R$ 12.000,00",
                "salario_final": "",
                "beneficios": "Auxílio alimentação",
                "jornada": "20 horas semanais",
                "vagas": "3",
                "localidade": "Palmas",
                "observacoes": "Remuneração proporcional à jornada"
            }
        ],
        "disciplinas": [
            {
                "nome": "Direito Constitucional",
                "topicos": [
                    {"nome": "Direitos fundamentais", "nome_padronizado": "Direitos fundamentais"}
                ],
            }
        ],
    },
}


class ContestPayloadTests(unittest.TestCase):
    def test_normalizes_optional_fields_and_nested_program(self):
        result = normalize_contest_payload(VALID_PAYLOAD)
        contest = result["concurso"]
        self.assertEqual(contest["nome"], "Concurso de exemplo")
        self.assertEqual(contest["cargo"], "")
        self.assertEqual(contest["cargos"][0]["nome"], "Médico")
        self.assertEqual(contest["cargos"][0]["salario_inicial"], "R$ 12.000,00")
        self.assertNotIn("data_prevista", contest)
        self.assertEqual(contest["disciplinas"][0]["topicos"][0]["nome"], "Direitos fundamentais")

    def test_rejects_invalid_date_status_and_unknown_fields(self):
        invalid_date = {
            **VALID_PAYLOAD,
            "concurso": {**VALID_PAYLOAD["concurso"], "data_prova": "10/05/2027"},
        }
        with self.assertRaises(ValueError):
            normalize_contest_payload(invalid_date)

        invalid_status = {
            **VALID_PAYLOAD,
            "concurso": {**VALID_PAYLOAD["concurso"], "status": "Confirmado"},
        }
        with self.assertRaises(ValueError):
            normalize_contest_payload(invalid_status)

        unknown_field = {
            **VALID_PAYLOAD,
            "concurso": {**VALID_PAYLOAD["concurso"], "executar": "algo"},
        }
        with self.assertRaises(ValueError):
            normalize_contest_payload(unknown_field)

    def test_parser_reports_invalid_json(self):
        with self.assertRaisesRegex(ValueError, "JSON inválido"):
            parse_contest_json('{"schema_version": 1, "concurso": }')

    def test_database_import_creates_contest_and_program(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "agenda.db")
            contest_id = database.add_contest_payload(VALID_PAYLOAD)
            record = database.get_contest(contest_id)
            self.assertEqual(record["nome"], "Concurso de exemplo")
            program = database.get_program(contest_id)
            self.assertEqual(program[0]["nome"], "Direito Constitucional")
            self.assertEqual(program[0]["topicos"][0]["nome_padronizado"], "Direitos fundamentais")
            cargos = database.list_cargos(contest_id)
            self.assertEqual(cargos[0]["nome"], "Médico")
            self.assertEqual(cargos[0]["salario_inicial"], "R$ 12.000,00")


if __name__ == "__main__":
    unittest.main()
