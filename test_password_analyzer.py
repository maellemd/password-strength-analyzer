import unittest
from unittest.mock import patch
from getpass import GetPassWarning
from password_analyzer import analyze_password, analyze_characters, calculate_entropy, main


class AnalyzerTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(analyze_password('')['score'], 0)

    def test_common(self):
        self.assertLess(analyze_password('Password123!')['score'], 20)

    def test_repeated_block(self):
        self.assertLess(analyze_password('Password123!' * 2)['score'], 20)

    def test_repeated_character(self):
        self.assertLess(analyze_password('A' * 20 + 'a1!')['score'], 60)

    def test_sequence(self):
        self.assertTrue(analyze_password('987654')['patterns']['sequential'])

    def test_unicode(self):
        chars = analyze_characters('é١')
        self.assertTrue(chars['has_lowercase'])
        self.assertTrue(chars['has_digit'])
        self.assertFalse(chars['has_symbol'])
        self.assertIsNone(calculate_entropy('é١'))

    def test_entropy(self):
        self.assertEqual(calculate_entropy('hello'), 23.5)

    def test_long_lowercase(self):
        self.assertGreaterEqual(analyze_password('moss lantern velvet otter')['score'], 80)

    def test_space(self):
        self.assertTrue(analyze_characters(' ')['has_space'])
        self.assertFalse(analyze_characters(' ')['has_symbol'])

    def test_bounds(self):
        for password in ('a', '123456', 'X!z7' * 20, 'moss lantern velvet otter'):
            self.assertTrue(0 <= analyze_password(password)['score'] <= 100)

    def test_no_password_in_result(self):
        password = 'fictional-example-47!'
        self.assertNotIn(password, repr(analyze_password(password)))

    @patch('password_analyzer.getpass', side_effect=KeyboardInterrupt)
    def test_exit(self, mocked):
        with patch('builtins.print'):
            main()
        mocked.assert_called_once()

    @patch('password_analyzer.getpass', side_effect=GetPassWarning)
    def test_hidden_input_failure(self, mocked):
        with patch('builtins.print'):
            main()
        mocked.assert_called_once()


if __name__ == '__main__':
    unittest.main()
