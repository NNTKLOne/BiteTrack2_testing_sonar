import pytest
import os
from voiceToText import VoiceToText
from LLM import send_query
import logging

# Nutildyti nereikalingus log'us testavimo metu
for noisy_module in ['httpx', 'httpcore', 'groq']:
    logging.getLogger(noisy_module).setLevel(logging.CRITICAL)


def test_audio_transcription_and_llm_response_lt():
    # 1. Failo egzistavimo patikrinimas
    file_path = os.path.join(os.path.dirname(__file__), "audio_test.wav")
    assert os.path.isfile(file_path), f" Failas nerastas: {file_path}"

    # 2. Inicijuojam transkripcijos klasę ir nustatome lietuvių kalbą
    vtt = VoiceToText()
    vtt.audio_file_path = file_path
    vtt.set_language("Lithuanian")

    # 3. Transkribuojame
    transcribed_text = vtt._run_transcription()

    if isinstance(transcribed_text, bytes):
        pytest.fail(" Transkribavimo funkcija grąžino bytes – tikėtasi tekstas (str).")

    assert isinstance(transcribed_text, str), " Transkribavimo rezultatas netinkamas (ne str)."
    assert transcribed_text.strip(), " Transkribuotas tekstas tuščias."

    print(f"\n Transkribuotas tekstas:\n{transcribed_text}")

    # 4. Siunčiame tekstą į LLM
    llm_response = send_query(transcribed_text)

    print(f"\n LLM atsakymas:\n{llm_response}")

    # 5. Tikriname, ar atsakyme yra teisingai atrinktas tekstas
    expected_response = "Aptikti patiekalai:\n- Patiekalas: Kotletai su bulvų salotomis"
    assert llm_response.strip() == expected_response, \
        f"LLM atsakymas neatitinka. Tikėtasi:\n{expected_response}\nGauta:\n{llm_response}"


def test_llm_response_on_empty_or_invalid_audio():
    # 1. Failas – tylus 1s audio
    silent_audio_path = os.path.join(os.path.dirname(__file__), "Silent.wav")
    assert os.path.isfile(silent_audio_path), f"Tylus testinis failas nerastas: {silent_audio_path}"

    # 2. Inicijuojam VTT
    vtt = VoiceToText()
    vtt.audio_file_path = silent_audio_path
    vtt.set_language("Lithuanian")

    # 3. Transkribuojam
    transcribed = vtt._run_transcription()
    print(f"\nTranskribuotas tekstas:\n'{transcribed}'")

    # 4. Siunčiam į LLM
    llm_response = send_query(transcribed)
    print(f"\nLLM atsakymas:\n{llm_response}")

    # 5. Tikrinam – jei LLM negrąžina '- Patiekalas:', vadinasi įrašas buvo tuščias arba klaidingas
    assert "- Patiekalas:" not in llm_response, \
        "LLM neturėjo aptikti patiekalų, nes įrašas buvo tuščias arba neteisingas"

    # 6. Imituojamas klaidos pranešimas kaip per UI
    if "- Patiekalas:" not in llm_response:
        print("Klaida: transkribuotas tekstas tuščias arba neteisingas.")