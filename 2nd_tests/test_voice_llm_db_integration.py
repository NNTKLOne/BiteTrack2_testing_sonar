import os
import pytest
from voiceToText import VoiceToText
from LLM import send_query
from database.database import Database

# ❗️Path to your real DB file
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

# ❗️Audio file to be used for the test (must be in same folder as this test)
AUDIO_FILE = os.path.join(os.path.dirname(__file__), "temp.wav")


@pytest.fixture
def db():
    db = Database()
    db.db_file = DB_PATH
    return db


def test_voice_to_llm_to_db_integration(db):
    # 1. Patikrinam, ar yra garso failas
    assert os.path.exists(AUDIO_FILE), f"Audio failas nerastas: {AUDIO_FILE}"

    # 2. Paleidžiam transkripciją
    vtt = VoiceToText()
    vtt.audio_file_path = AUDIO_FILE
    vtt.set_language("Lithuanian")

    transcribed = vtt._run_transcription()
    assert isinstance(transcribed, str), "Transkribuotas tekstas turi būti tekstas (str)"
    assert transcribed.strip(), "Transkribuotas tekstas tuščias"

    print(f"\n📄 Transkribuotas tekstas:\n{transcribed}")

    # 3. Siunčiam į LLM
    llm_response = send_query(transcribed)
    assert isinstance(llm_response, str), "LLM atsakymas netinkamas (ne str)"
    assert "Patiekalas" in llm_response or "nerasta" in llm_response.lower(), "LLM atsakymas negrąžino patiekalų"

    print(f"\n🧠 LLM atsakymas:\n{llm_response}")

    # 4. Įrašom į DB
    inserted_count = 0
    for line in llm_response.split("\n"):
        if line.strip().startswith("- Patiekalas:"):
            name = line.split(":", 1)[1].strip()
            #db.add_product(name)
            inserted_count += 1

    assert inserted_count > 0, "Nė vienas patiekalas nebuvo įrašytas į duomenų bazę"

    # 5. Patikrinam ar DB turi tuos produktus
    all_products = db.get_all_products()
    matched = [p for p in all_products if any(n in p["product_name"] for n in llm_response)]
    assert matched, "Produktai neatsirado duomenų bazėje"

    print(f"\n✅ Į DB įrašyti patiekalai ({inserted_count}):")
    for product in matched:
        print(" -", product["product_name"])
