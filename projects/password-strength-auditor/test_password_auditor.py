import unittest
from password_auditor import evaluate

class PasswordAuditorTests(unittest.TestCase):
    def test_weak_password(self):
        result = evaluate('password')
        self.assertEqual(result['rating'], 'weak')
        self.assertIn('common password', result['reasons'])

    def test_strong_password(self):
        result = evaluate('M0on!River!2026')
        self.assertEqual(result['rating'], 'strong')

if __name__ == '__main__':
    unittest.main()
