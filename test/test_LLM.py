import unittest
from LLM import call_llama_api, process_response, send_query


class TestLlamaFunctions(unittest.TestCase):

    def setUp(self):
        self.output_text = ""
        self.input_text = ""

    def test_call_llama_api(self):
        query = "valgiau kebabą su česnakiniu padažu"
        response = call_llama_api(query)

        self.assertIsInstance(response, dict)

        if "text" in response:
            self.assertIn("- Patiekalas:", response["text"])
        elif "error" in response:
            self.assertIn("Klaida", response["error"])

    def test_process_response_valid(self):
        response = {
            "text": "- Patiekalas: Koldūnai su sviestu\n- Patiekalas: Kepsnys su bulvėmis"
        }
        self.output_text = process_response(response)

        self.assertIn("Aptikti patiekalai:", self.output_text)
        self.assertIn("- Patiekalas: Koldūnai su sviestu", self.output_text)
        self.assertIn("- Patiekalas: Kepsnys su bulvėmis", self.output_text)

    def test_process_response_error(self):
        response = {"error": "API klaida"}
        self.output_text = process_response(response)

        self.assertEqual(self.output_text, "API klaida")

    def test_empty_input(self):
        """kai tuscias inputas"""
        self.input_text = ""
        self.output_text = send_query(self.input_text)

        self.assertEqual(self.output_text, "Prašome įvesti tinkamą patiekalą.")

    def test_no_dishes_in_query(self):
        """kai nera patiekalu query"""
        query = "Šiandien žiūrėjau filmą ir klausiau muzikos"
        response = call_llama_api(query)

        self.assertIsInstance(response, dict)
        if "text" in response:
            self.assertNotIn("- Patiekalas:", response["text"])

    def test_multiple_dishes_in_query(self):
        """testas keliems patiekalams query"""
        query = "valgiau koldūnus su grietine ir pica su saliamiu"
        response = call_llama_api(query)

        self.assertIsInstance(response, dict)

        if "text" in response:
            self.assertIn("- Patiekalas: Koldūnai su grietine", response["text"])
            self.assertIn("- Patiekalas: Pica su saliamiu", response["text"])

    def test_invalid_api_response_format(self):
        """Netinkamam API atsakymo formato testas"""
        response = {"unexpected_key": "something_wrong"}
        self.output_text = process_response(response)

        self.assertEqual(self.output_text, "Maisto produktų nerasta.")

    def test_request_failure(self):
        """Test API request klaida"""
        response = {"error": "Klaida jungiantis: Connection error"}
        self.output_text = process_response(response)

        self.assertEqual(self.output_text, "Klaida jungiantis: Connection error")

    def test_generic_exception_handling(self):
        """Test exeption kai nepavyko prisijungti prie API"""
        response = {"error": "Klaida, jungiantis prie API: Unknown error"}
        self.output_text = process_response(response)

        self.assertEqual(self.output_text, "Klaida, jungiantis prie API: Unknown error")

    def test_empty_api_response(self):
        """Test API atsakymas tusčias"""
        response = {"text": ""}
        self.output_text = process_response(response)

        self.assertEqual(self.output_text, "Maisto produktų nerasta.")

    def test_missing_choices_key(self):
        """Test kai nėra 'choices' rakto API atsakyme (T.y. - atsakymas tusčias arba nerasta maisto produktų)"""
        response = {}
        self.output_text = process_response(response)

        self.assertEqual(self.output_text, "Maisto produktų nerasta.")

    def test_unusual_api_return_format(self):
        """jei atsakymas pateikiamas neužbaigtas LLM"""
        response = {
            "text": "- Patiekalas: \n- Patiekalas: Kepsnys su  "
        }
        self.output_text = process_response(response)

        self.assertIn("Aptikti patiekalai:", self.output_text)
        self.assertIn("- Patiekalas:", self.output_text)
        self.assertIn("Kepsnys su", self.output_text)

    def test_multiline_response(self):
        """kai daug patiekalu rasta"""
        response = {
            "text": "- Patiekalas: Pica\n- Patiekalas: Koldūnai\n- Patiekalas: Cepelinai"
        }
        self.output_text = process_response(response)

        self.assertIn("Aptikti patiekalai:", self.output_text)
        self.assertIn("Pica", self.output_text)
        self.assertIn("Koldūnai", self.output_text)
        self.assertIn("Cepelinai", self.output_text)

    def test_invalid_query_format(self):
        """kai query blogam formate"""
        query = "Valgiau,, kebaba ir ,,, makaronus.."
        response = call_llama_api(query)

        self.assertIsInstance(response, dict)

        if "text" in response:
            self.assertIn("Kebabas", response["text"])
            self.assertIn("Makaronai", response["text"])


if __name__ == "__main__":
    unittest.main()
