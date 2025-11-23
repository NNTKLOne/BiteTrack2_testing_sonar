import unittest
from unittest.mock import patch, MagicMock, mock_open, ANY
from voiceToText import VoiceToText
from pathlib import Path

TEMP_WAV_PATH = Path(__file__).parent / 'temp.wav'


class TestVoiceToText(unittest.TestCase):

    def setUp(self):
        self.vtt = VoiceToText()
        self.vtt.audio_file_path = TEMP_WAV_PATH

    def test_init(self):
        # Tikrina, ar klasė inicializuojasi teisingai
        self.assertFalse(self.vtt.is_recording)
        self.assertEqual(self.vtt.language_code, 'en')
        self.assertEqual(self.vtt.audio_file_path, TEMP_WAV_PATH)

    def test_set_language(self):
        # Tikrina kalbos kodo nustatymą
        self.vtt.set_language('English')
        self.assertEqual(self.vtt.language_code, 'en')

        self.vtt.set_language('Lithuanian')
        self.assertEqual(self.vtt.language_code, 'lt')

        self.vtt.set_language('Spanish')  # Nežinoma kalba grįš į 'en'
        self.assertEqual(self.vtt.language_code, 'en')

    @patch('builtins.open', new_callable=mock_open)
    def test_run_transcription(self, mock_file):
        # Sukuria fiktyvų klientą
        mock_client = MagicMock()
        mock_transcription = MagicMock()
        mock_transcription.text = "Testinė transkripcija"
        mock_client.audio.transcriptions.create.return_value = mock_transcription

        self.vtt.client = mock_client

        # Testuoja transkripciją
        result = self.vtt._run_transcription()

        mock_client.audio.transcriptions.create.assert_called_once_with(
            file=(TEMP_WAV_PATH, ANY),
            model="whisper-large-v3-turbo",
            language='en',
            response_format="verbose_json"
        )
        self.assertEqual(result, "Testinė transkripcija")

    @patch('wave.open')
    def test_is_audio_file_empty(self, mock_wave):
        # Simuliuoja tuščią failą
        mock_wave_read = MagicMock()
        mock_wave.return_value.__enter__.return_value = mock_wave_read
        mock_wave_read.getnframes.return_value = 0

        self.assertTrue(self.vtt._is_audio_file_empty(TEMP_WAV_PATH))

        # Simuliuoja failą su turiniu
        mock_wave_read.getnframes.return_value = 100
        self.assertFalse(self.vtt._is_audio_file_empty(TEMP_WAV_PATH))

    @patch('wave.open')
    def test_transcription_fails_on_empty_file(self, mock_wave):
        # Simuliuoja tuščią failą
        mock_wave_read = MagicMock()
        mock_wave.return_value.__enter__.return_value = mock_wave_read
        mock_wave_read.getnframes.return_value = 0

        # Sukuria fiktyvų klientą, kuris grąžina tuščią tekstą
        mock_client = MagicMock()
        mock_transcription = MagicMock()
        mock_transcription.text = ""  # Simulate empty transcription
        mock_client.audio.transcriptions.create.return_value = mock_transcription

        self.vtt.client = mock_client

        result = self.vtt._run_transcription()
        self.assertEqual(result, "")

    @patch('builtins.open', new_callable=MagicMock)
    def test_transcription_fails_on_invalid_response(self, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = b"mock audio data"

        # Make the transcription response None (invalid response)
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = None

        self.vtt.client = mock_client

        result = self.vtt._run_transcription()
        self.assertEqual(result, "Klaida transkribuojant: Netikėta klaida: <class 'NoneType'>")


if __name__ == '__main__':
    unittest.main()
