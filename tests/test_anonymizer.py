import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('anonymizer', PROJECT / 'anonymizer.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class AnonymizerTests(unittest.TestCase):
    def test_buyer_example(self):
        text = (PROJECT / 'primery/pokupatel.txt').read_text()
        expected = text.replace('+7 913 555-28-64', '[телефон]').replace('8 (921) 777-40-12', '[телефон]').replace('marina.sokolova@yandex.example', '[почта]')
        self.assertEqual(app.mask_text(text), (expected, {'карта': 0, 'телефон': 2, 'почта': 1}))

    def test_apartment_example(self):
        text = (PROJECT / 'primery/kvartira.txt').read_text()
        expected = text.replace('4276 4400 1288 6631', '[карта]').replace('+7 903 222-11-45', '[телефон]')
        self.assertEqual(app.mask_text(text), (expected, {'карта': 1, 'телефон': 1, 'почта': 0}))

    def test_no_personal_data(self):
        text = (PROJECT / 'primery/bez_dannyh.txt').read_text()
        self.assertEqual(app.mask_text(text), (text, {'карта': 0, 'телефон': 0, 'почта': 0}))

    def test_empty_function_input(self):
        self.assertEqual(app.mask_text(''), ('', {'карта': 0, 'телефон': 0, 'почта': 0}))

    def test_email_case(self):
        for email in ('user@mail.example', 'USER@MAIL.EXAMPLE', 'User.Name+tag@Mail.Example'):
            with self.subTest(email=email):
                self.assertEqual(app.mask_text(email), ('[почта]', {'карта': 0, 'телефон': 0, 'почта': 1}))

    def test_phone_formats(self):
        for phone in ('+79135552864', '+7 (913) 555-28-64', '8 (921) 777-40-12'):
            with self.subTest(phone=phone):
                self.assertEqual(app.mask_text(phone)[0], '[телефон]')
                self.assertEqual(app.mask_text(phone)[1]['телефон'], 1)

    def test_card_separators(self):
        for card in ('4276440012886631', '4276 4400 1288 6631', '4276-4400-1288-6631'):
            with self.subTest(card=card):
                self.assertEqual(app.mask_text(card), ('[карта]', {'карта': 1, 'телефон': 0, 'почта': 0}))

    def test_card_preserves_following_space(self):
        text = 'Карта 4276 4400 1288 6631 и комментарий.'
        self.assertEqual(app.mask_text(text)[0], 'Карта [карта] и комментарий.')

    def test_card_length_boundaries(self):
        for size in (13, 19):
            self.assertEqual(app.mask_text('1' * size)[1]['карта'], 1)
        for size in (12, 20):
            self.assertEqual(app.mask_text('1' * size)[0], '1' * size)

    def test_counters_and_repeat(self):
        text = '+79135552864 user@mail.example +79135552864 user@mail.example 4276440012886631'
        result, counts = app.mask_text(text)
        self.assertEqual(counts, {'карта': 1, 'телефон': 2, 'почта': 2})
        self.assertEqual(sum(counts.values()), result.count('[телефон]') + result.count('[почта]') + result.count('[карта]'))
        self.assertEqual(app.mask_text(result), (result, {'карта': 0, 'телефон': 0, 'почта': 0}))


class ButtonHandlerTests(unittest.TestCase):
    def run_handler(self, text):
        source, result, button, status = (MagicMock() for _ in range(4))
        # Tk adds one service newline for the "end" index.
        source.get.side_effect = lambda start, end: text if end == 'end-1c' else text + '\n'
        with patch.object(app.tk, 'Label', side_effect=[MagicMock(), MagicMock(), MagicMock(), status, MagicMock()]), patch.object(app.tk, 'Button', return_value=button), patch.object(app.scrolledtext, 'ScrolledText', side_effect=[source, result]):
            app.build_app(MagicMock())
        button.config.call_args.kwargs['command']()
        output = result.insert.call_args.args[1] if result.insert.called else None
        return output, status.config.call_args.kwargs['text'], result

    def test_plain_text_preserves_edge_whitespace(self):
        text = '  Текст без личных данных.  \n\n'
        output, message, _ = self.run_handler(text)
        self.assertEqual(output, text)
        self.assertIn('текст не менялся', message)

    def test_masked_text_preserves_edge_whitespace(self):
        output, message, _ = self.run_handler(' \tuser@mail.example  \n')
        self.assertEqual(output, ' \t[почта]  \n')
        self.assertEqual(message, 'Скрыто: почта — 1.')

    def test_blank_inputs_clear_result(self):
        for text in ('', '  \t\n'):
            with self.subTest(text=text):
                output, message, result = self.run_handler(text)
                self.assertIsNone(output)
                self.assertIn('поле пустое', message)
                result.delete.assert_called_once_with('1.0', 'end')

    def test_checklist_examples_through_button(self):
        for filename, message in (
            ('pokupatel.txt', 'Скрыто: телефон — 2, почта — 1.'),
            ('kvartira.txt', 'Скрыто: телефон — 1, карта — 1.'),
            ('bez_dannyh.txt', 'Личных данных не найдено — текст не менялся.'),
        ):
            with self.subTest(filename=filename):
                text = (PROJECT / 'primery' / filename).read_text()
                output, actual_message, _ = self.run_handler(text)
                self.assertEqual(output, app.mask_text(text)[0])
                self.assertEqual(actual_message, message)

if __name__ == '__main__':
    unittest.main(verbosity=2)
