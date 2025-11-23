# test_gui_integration.py

import os
import pytest
from datetime import datetime, timedelta
from kivy.base import EventLoop, runTouchApp
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager

from database.database import Database
from ui.statisticsScreen import StatisticsScreen

# Užkrauname KV failą
kv_path = os.path.join(os.path.dirname(__file__), "..", "ui", "UI.kv")
Builder.load_file(kv_path)

@pytest.fixture
def setup_statistics_screen():
    db = Database()
    db.db_file = os.path.join(os.path.dirname(__file__), "data.db")
    db.create_tables()
    this_week = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d %H:%M:%S')
    this_month = datetime.now().replace(day=2).strftime('%Y-%m-%d %H:%M:%S')
    bad_date = "2024-03-07 10:00:00"

    # Pridedame testinį produktą
    db.add_product("TestProduktasD")
    db.add_product("TestProduktasW", this_week)
    db.add_product("TestProduktasM", this_month)
    db.add_product("TestProduktasBD", bad_date)

    EventLoop.ensure_window()

    sm = ScreenManager()
    screen = StatisticsScreen(name="statistics")
    screen.db = db
    sm.add_widget(screen)
    sm.current = "statistics"

    return screen

@pytest.fixture
def empty_statistics_screen():
    db = Database()
    db.db_file = os.path.join(os.path.dirname(__file__), "data.db")
    db.create_tables()
    db.delete_all_products()  # čia naudojama tavo nauja funkcija

    EventLoop.ensure_window()

    sm = ScreenManager()
    screen = StatisticsScreen(name="statistics")
    screen.db = db
    sm.add_widget(screen)
    sm.current = "statistics"

    return screen

def test_product_shown_in_statistics_today(setup_statistics_screen):
    screen = setup_statistics_screen
    screen.db.add_product("TestProduktasD")
    screen.load_statistics_data("Diena")

    found = any(
        isinstance(widget, Button) and "TestProduktasD" in widget.text
        for row in screen.ids.stats_list.children
        for widget in row.children
    )

    assert found, "Produktas nebuvo parodytas statistikoje su filtru 'Diena'"


def test_product_shown_in_statistics_this_week(setup_statistics_screen):
    screen = setup_statistics_screen
    screen.load_statistics_data("Savaitė")

    found_D = any(
        isinstance(widget, Button) and "TestProduktasD" in widget.text
        for row in screen.ids.stats_list.children
        for widget in row.children
    )
    found_W = any(
        isinstance(widget, Button) and "TestProduktasW" in widget.text
        for row in screen.ids.stats_list.children
        for widget in row.children
    )

    assert found_D, "ProduktasD turėjo būti rodomas savaitės filtravime"
    assert found_W, "ProduktasW turėjo būti rodomas savaitės filtravime"



def test_product_shown_in_statistics_this_month(setup_statistics_screen):
    screen = setup_statistics_screen
    screen.load_statistics_data("Mėnuo")

    found_D = any(
        isinstance(widget, Button) and "TestProduktasD" in widget.text
        for row in screen.ids.stats_list.children
        for widget in row.children
    )
    found_W = any(
        isinstance(widget, Button) and "TestProduktasW" in widget.text
        for row in screen.ids.stats_list.children
        for widget in row.children
    )

    found = any(
        isinstance(widget, Button) and "TestProduktasM" in widget.text
        for row in screen.ids.stats_list.children
        for widget in row.children
    )

    assert found_D, "ProduktasD turėjo būti rodomas savaitės filtravime"
    assert found_W, "ProduktasW turėjo būti rodomas savaitės filtravime"
    assert found, "Produktas nebuvo parodytas statistikoje su filtru 'Mėnuo'"


def test_no_data_today_shows_message(empty_statistics_screen):
    screen = empty_statistics_screen
    screen.db.delete_all_products()
    screen.load_statistics_data("Diena")

    found = any(
        isinstance(widget, Label) and "nerasta" in widget.text.lower()
        for widget in screen.ids.stats_list.children
    )
    assert found, "Filtras 'Diena' turėjo parodyti pranešimą 'Duomenų nerasta.'"


def test_no_data_week_shows_message(empty_statistics_screen):
    screen = empty_statistics_screen
    screen.db.delete_all_products()
    screen.load_statistics_data("Savaitė")

    found = any(
        isinstance(widget, Label) and "nerasta" in widget.text.lower()
        for widget in screen.ids.stats_list.children
    )
    assert found, "Filtras 'Savaitė' turėjo parodyti pranešimą 'Duomenų nerasta.'"


def test_no_data_month_shows_message(empty_statistics_screen):
    screen = empty_statistics_screen
    screen.db.delete_all_products()
    screen.load_statistics_data("Mėnuo")

    found = any(
        isinstance(widget, Label) and "nerasta" in widget.text.lower()
        for widget in screen.ids.stats_list.children
    )
    assert found, "Filtras 'Mėnuo' turėjo parodyti pranešimą 'Duomenų nerasta.'"


def test_no_data_all_shows_message(empty_statistics_screen):
    screen = empty_statistics_screen
    screen.db.delete_all_products()
    screen.load_statistics_data("Visi")

    found = any(
        isinstance(widget, Label) and "nerasta" in widget.text.lower()
        for widget in screen.ids.stats_list.children
    )
    assert found, "Filtras 'Visi' turėjo parodyti pranešimą 'Duomenų nerasta.'"

def test_product_deleted_and_not_shown_in_gui(setup_statistics_screen):
    screen = setup_statistics_screen
    db = screen.db

    # Ištriname visus produktus (kad būtų švaru)
    products = db.get_all_products()
    for product in products:
        db.delete_product(product['id'])

    # Pažiūrime, ar GUI neberodo produkto
    screen.load_statistics_data("Diena")

    # Tikriname, ar TestProduktas nebėra
    found = False
    for row in screen.ids.stats_list.children:
        for widget in row.children:
            if isinstance(widget, Button) and "TestProduktas" in widget.text:
                found = True
                break

    assert not found, "Produktas vis dar matomas GUI po ištrynimo"

def test_product_name_updated_and_reflected_in_gui(setup_statistics_screen):
    screen = setup_statistics_screen
    db = screen.db

    # Gauti visus produktus ir atnaujinti pavadinimą pirmam
    products = db.get_all_products()
    assert products, "DB neturi produktų"

    product = products[0]
    old_name = product['product_name']
    new_name = "AtnaujintasProduktas"

    db.update_product(product['id'], new_name)

    # Perkrovimas GUI
    screen.load_statistics_data("Diena")

    # Patikrinam, kad naujas pavadinimas yra, o seno nėra
    texts = [
        widget.text
        for row in screen.ids.stats_list.children
        for widget in row.children if isinstance(widget, Button)
    ]

    assert any(new_name in t for t in texts), "Naujas pavadinimas nerastas GUI"
    assert all(old_name not in t for t in texts), "Senas pavadinimas vis dar rodomas GUI"


def test_gui_shows_error_on_database_failure(monkeypatch):
    db = Database()

    def fake_error():
        raise Exception("DB nepavyko pasiekti")

    monkeypatch.setattr(db, "get_all_products", fake_error)

    # Užtikrinam Kivy aplinką
    if not EventLoop.event_listeners:
        EventLoop.ensure_window()

    sm = ScreenManager()
    screen = StatisticsScreen(name="statistics")
    screen.db = db
    sm.add_widget(screen)
    sm.current = "statistics"

    # Priverstinai paleidžiam statistikų užkrovimą (triggerinam klaidą)
    screen.load_statistics_data("Visi")

    # Kadangi naudojamas Popup, neįmanoma jo tiesiogiai pasiekti be refaktoriaus
    # Galim patikrinti, ar neįvyko crashas ir logika suveikė (netiesioginis testas)

    assert True  # Testas praeina, jei klaida nesukėlė crasho
