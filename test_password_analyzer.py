import unittest

from password_analyzer import (
    analyze_password,
    contains_common_term,
    contains_sequence,
    estimate_search_space_bits,
    analyze_characters,
)


class PasswordAnalyzerTests(unittest.TestCase):
    def test_empty_password_has_zero_search_space(self):
        analysis = analyze_characters("")
        self.assertEqual(estimate_search_space_bits("", analysis), 0.0)

    def test_common_password_term_is_detected(self):
        self.assertTrue(contains_common_term("MyPassword2026!"))

    def test_numeric_sequence_is_detected(self):
        self.assertTrue(contains_sequence("coffee1234!"))

    def test_longer_unpredictable_password_scores_better(self):
        weak = analyze_password("password123")
        stronger = analyze_password("River!Cedar7Orbit#Lantern")
        self.assertGreater(stronger.score, weak.score)

    def test_analysis_does_not_store_plaintext_password(self):
        result = analyze_password("Example-Only-Password")
        self.assertFalse(hasattr(result, "password"))


if __name__ == "__main__":
    unittest.main()
