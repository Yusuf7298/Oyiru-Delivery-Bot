import json
import os
import unittest
from utils.i18n import t

class TestI18n(unittest.TestCase):
    def setUp(self):
        self.languages = ['en', 'am', 'om']
        self.translations = {}
        for lang in self.languages:
            path = f'translations/{lang}.json'
            self.assertTrue(os.path.exists(path), f'Missing {path}')
            with open(path, 'r', encoding='utf-8-sig') as f:
                self.translations[lang] = json.load(f)

    def test_key_parity(self):
        en_keys = set(self.translations['en'].keys())
        for lang in ['am', 'om']:
            lang_keys = set(self.translations[lang].keys())
            missing = en_keys - lang_keys
            self.assertEqual(len(missing), 0, f'{lang} is missing keys: {missing}')

    def test_interpolation(self):
        name = 'Abebe'
        order_no = 'ORD-1234'
        for lang in self.languages:
            res_user = t('welcome_user', lang, name=name)
            self.assertIn(name, res_user)
            res_order = t('order_submitted', lang, order_number=order_no)
            self.assertIn(order_no, res_order)

    def test_fallback_behavior(self):
        res = t('non_existent_key_12345', 'en')
        self.assertEqual(res, 'non_existent_key_12345')

if __name__ == '__main__':
    unittest.main()
