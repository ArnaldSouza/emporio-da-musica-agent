from policies import POLICY_TOPICS, extract_manual_lines, get_store_policy, load_policies, split_sections

SECTIONS = split_sections(extract_manual_lines())


def test_split_sections_ignores_numbered_steps_inside_a_section():
    lines = ["Cover", "1. First", "text", "1. step inside", "2. Second"]
    assert split_sections(lines) == {1: "1. First\ntext\n1. step inside", 2: "2. Second"}


def test_manual_has_ten_sections():
    assert list(SECTIONS) == list(range(1, 11))


def test_opening_hours_section_keeps_the_hours_table():
    assert "Sábado 09:00 às 13:00" in SECTIONS[2]


def test_page_headers_and_footers_are_removed():
    for text in SECTIONS.values():
        assert "Página" not in text
        assert "Manual de Políticas e Procedimentos" not in text


def test_contacts_are_standardized():
    assert "contato@emporiodamusica.com.br" in SECTIONS[1]
    assert "empóriodamusica" not in SECTIONS[1]
    assert "3321-4500" not in SECTIONS[7]


def test_service_flow_steps_stay_in_section_seven():
    assert "Saudação" in SECTIONS[7]


POLICIES = load_policies()


def test_load_policies_has_only_customer_facing_topics():
    assert list(POLICIES) == list(POLICY_TOPICS)
    for text in POLICIES.values():
        assert not text.startswith(("7.", "10."))


def test_get_store_policy_returns_section_text():
    assert "09:00 às 18:00" in get_store_policy(POLICIES, "opening_hours")["text"]
    assert "PIX" in get_store_policy(POLICIES, "payment")["text"]


def test_get_store_policy_unknown_topic_lists_available_topics():
    result = get_store_policy(POLICIES, "recipes")
    assert "error" in result
    assert result["available_topics"] == list(POLICY_TOPICS)