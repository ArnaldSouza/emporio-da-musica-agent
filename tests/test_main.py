from main import MAX_HISTORY_MESSAGES, describe_tool_calls, trim_history


def make_turn(number):
    """Return the messages of one turn that used a tool (test helper)."""
    return [
        {"role": "user", "content": f"question {number}"},
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": f"call_{number}",
                    "type": "function",
                    "function": {"name": "get_store_policy", "arguments": '{"topic": "opening_hours"}'},
                }
            ],
        },
        {"role": "tool", "tool_call_id": f"call_{number}", "content": "{}"},
        {"role": "assistant", "content": f"answer {number}"},
    ]


def test_short_history_is_kept_unchanged():
    history = make_turn(1)
    assert trim_history(history) == history


def test_long_history_keeps_recent_messages_starting_at_a_customer_message():
    history = [message for number in range(15) for message in make_turn(number)]
    trimmed = trim_history(history)
    assert len(trimmed) <= MAX_HISTORY_MESSAGES
    assert trimmed[0]["role"] == "user"
    assert trimmed[-1] == history[-1]


def test_single_long_turn_is_kept_whole():
    tool_messages = [{"role": "tool", "content": "{}"}] * (MAX_HISTORY_MESSAGES + 5)
    history = make_turn(1) + [{"role": "user", "content": "last question"}] + tool_messages
    trimmed = trim_history(history)
    assert trimmed[0] == {"role": "user", "content": "last question"}


def test_describe_tool_calls_lists_each_call_with_its_arguments():
    lines = describe_tool_calls(make_turn(1))
    assert lines == ['[tool] get_store_policy {"topic": "opening_hours"}']


def test_describe_tool_calls_without_tools_is_empty():
    messages = [{"role": "user", "content": "Oi"}, {"role": "assistant", "content": "Olá!"}]
    assert describe_tool_calls(messages) == []