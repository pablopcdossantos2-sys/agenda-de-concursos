import unittest

from agenda.services.similarity import compare_programs, lexical_similarity, normalize


class SimilarityTests(unittest.TestCase):
    def test_normalize_removes_accents_and_punctuation(self):
        self.assertEqual(normalize("Direito Constitucional — princípios"), "direito constitucional principios")

    def test_identical_programs_score_one_hundred(self):
        program = [{
            "nome": "Direito Constitucional",
            "topicos": [
                {"nome": "Direitos e garantias fundamentais", "nome_padronizado": ""},
                {"nome": "Controle de constitucionalidade", "nome_padronizado": ""},
            ],
        }]
        result = compare_programs(program, program)
        self.assertEqual(result["percentual"], 100.0)
        self.assertEqual(result["topicos_correspondentes"], 2)

    def test_canonical_name_matches_different_labels(self):
        left = [{
            "nome": "Direito Administrativo",
            "topicos": [{"nome": "Atos administrativos", "nome_padronizado": "Atos administrativos"}],
        }]
        right = [{
            "nome": "Direito Administrativo",
            "topicos": [{"nome": "Ato da administração pública", "nome_padronizado": "Atos administrativos"}],
        }]
        result = compare_programs(left, right)
        self.assertEqual(result["percentual"], 100.0)
        self.assertTrue(result["disciplinas"][0]["topicos"]["matches"][0]["padronizado"])

    def test_unmatched_topics_reduce_score(self):
        left = [{
            "nome": "Direito Constitucional",
            "topicos": [{"nome": "Direitos fundamentais"}, {"nome": "Organização do Estado"}],
        }]
        right = [{
            "nome": "Direito Constitucional",
            "topicos": [{"nome": "Direitos fundamentais"}],
        }]
        result = compare_programs(left, right)
        self.assertGreater(result["percentual"], 0)
        self.assertLess(result["percentual"], 100)
        self.assertEqual(result["topicos_exclusivos_a"], 1)

    def test_different_disciplines_do_not_match(self):
        left = [{"nome": "Matemática", "topicos": [{"nome": "Funções"}]}]
        right = [{"nome": "Direito Penal", "topicos": [{"nome": "Crimes contra a administração"}]}]
        result = compare_programs(left, right)
        self.assertEqual(result["percentual"], 0.0)

    def test_lexical_similarity_is_symmetric(self):
        a = "Administração pública: princípios e organização"
        b = "Princípios da organização da administração pública"
        self.assertAlmostEqual(lexical_similarity(a, b), lexical_similarity(b, a))


if __name__ == "__main__":
    unittest.main()
