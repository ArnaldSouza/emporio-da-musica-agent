from datetime import date, datetime

from business_rules import CAMPO_GRANDE_TZ
from prompts import build_system_prompt, format_opening_hours


def test_opening_hours_show_campo_grande_and_brasilia_times():
    hours = format_opening_hours(date(2026, 3, 25))
    assert "Segunda a sexta: 09h00 às 18h00 (horário de MS) / 10h00 às 19h00 (horário de Brasília)" in hours
    assert "Sábado: 09h00 às 13h00 (horário de MS) / 10h00 às 14h00 (horário de Brasília)" in hours
    assert "Domingo e feriados: fechado" in hours


def test_system_prompt_says_store_is_open_during_business_hours():
    prompt = build_system_prompt(datetime(2026, 3, 25, 10, 0, tzinfo=CAMPO_GRANDE_TZ))
    assert "The store is OPEN" in prompt
    assert "quarta-feira, 25/03/2026 10:00" in prompt


def test_system_prompt_says_store_is_closed_on_sunday():
    prompt = build_system_prompt(datetime(2026, 3, 29, 10, 0, tzinfo=CAMPO_GRANDE_TZ))
    assert "The store is CLOSED" in prompt


def test_system_prompt_defines_persona_and_contacts():
    prompt = build_system_prompt(datetime(2026, 3, 25, 10, 0, tzinfo=CAMPO_GRANDE_TZ))
    assert "You are Clave" in prompt
    assert "(67) 3341-4444" in prompt