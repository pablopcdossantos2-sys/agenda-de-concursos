import unittest

from agenda.services.dates import format_date_input, format_date_pt_br, parse_user_date
from agenda.services.prompts import build_extraction_prompt
from agenda.services.profile import normalize_profile


class ProfileAndDateTests(unittest.TestCase):
    def test_profile_normalization(self):
        profile = normalize_profile({
            "niveis_escolaridade": ["Superior", "Superior", "Inválido"],
            "cargos_desejados": [" Médico ", "Jornalista", "médico", ""],
            "observacoes": "Registro profissional ativo",
        })
        self.assertEqual(profile["niveis_escolaridade"], ["Superior"])
        self.assertEqual(profile["cargos_desejados"], ["Médico", "Jornalista"])
        self.assertEqual(profile["observacoes"], "Registro profissional ativo")

    def test_prompt_applies_combined_profile_filters(self):
        prompt = build_extraction_prompt({
            "niveis_escolaridade": ["Superior"],
            "cargos_desejados": ["Médico", "Jornalista"],
        })
        self.assertIn("Superior", prompt)
        self.assertIn("Médico, Jornalista", prompt)
        self.assertIn("Aplique simultaneamente os filtros", prompt)
        self.assertIn('"cargos": [', prompt)
        self.assertIn('"salario_inicial":', prompt)
        self.assertNotIn('"data_prevista":', prompt)

    def test_prompt_without_restrictions_explicitly_requests_all_positions(self):
        prompt = build_extraction_prompt({})
        self.assertIn("Extraia todos os cargos do edital", prompt)

    def test_date_input_and_display_formats(self):
        self.assertEqual(parse_user_date("12/11/2026"), "2026-11-12")
        self.assertEqual(parse_user_date("2026-11-12"), "2026-11-12")
        self.assertEqual(format_date_input("2026-11-12"), "12/11/2026")
        self.assertEqual(format_date_pt_br("2026-11-12"), "12 de Novembro de 2026")
        with self.assertRaises(ValueError):
            parse_user_date("31/02/2026")


if __name__ == "__main__":
    unittest.main()
