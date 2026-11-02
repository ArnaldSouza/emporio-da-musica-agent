"""Command-line chat with Clave, the Empório da Música virtual assistant.

Run: python main.py               (normal chat)
     python main.py --show-tools  (also prints which tools the agent called on each turn)
"""

import sys
from datetime import datetime

from openai import APIError

from agent import answer, create_llm_client, load_store
from business_rules import CAMPO_GRANDE_TZ

MAX_HISTORY_MESSAGES = 20  # keeps requests small; older messages are dropped
EXIT_COMMANDS = {"sair", "exit", "quit"}
SHOW_TOOLS_FLAG = "--show-tools"
GREETING = "Olá! Eu sou a Clave, assistente virtual da Empório da Música. Como posso ajudar?"
ERROR_REPLY = "Tive um problema técnico para responder agora. Pode tentar de novo em instantes?"
GOODBYE = "Até mais! Obrigada por falar com a Empório da Música."


def trim_history(history: list[dict]) -> list[dict]:
    """Keep only the most recent messages, always starting at a customer message.

    Starting at a customer message avoids separating a tool call from its result.
    """
    if len(history) <= MAX_HISTORY_MESSAGES:
        return history
    first_kept = len(history) - MAX_HISTORY_MESSAGES
    user_indexes = [index for index, message in enumerate(history) if message["role"] == "user"]
    # If no customer message is recent enough, keep the whole last turn
    start = next((index for index in user_indexes if index >= first_kept), user_indexes[-1])
    return history[start:]


def describe_tool_calls(messages: list[dict]) -> list[str]:
    """Return one readable line per tool call found in the messages of a turn."""
    lines = []
    for message in messages:
        for tool_call in message.get("tool_calls", []):
            function = tool_call["function"]
            lines.append(f"[tool] {function['name']} {function['arguments']}")
    return lines


def main(show_tools: bool = False) -> None:
    """Run the customer service chat in the terminal."""
    try:
        client, model = create_llm_client()
        store = load_store()
    except (RuntimeError, FileNotFoundError) as error:
        print(f"Setup error: {error}")
        return

    history: list[dict] = []
    print(f"Clave: {GREETING}  (digite 'sair' para encerrar)")
    while True:
        try:
            user_message = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_message:
            continue
        if user_message.casefold() in EXIT_COMMANDS:
            break

        turn_start = len(history)
        history.append({"role": "user", "content": user_message})
        try:
            reply = answer(client, model, history, store, datetime.now(CAMPO_GRANDE_TZ))
        except APIError as error:
            # Rate limit, network or provider error: undo this turn and let the customer try again
            del history[turn_start:]
            print(f"\nClave: {ERROR_REPLY}  [{error.__class__.__name__}]")
            continue
        if show_tools:
            for line in describe_tool_calls(history[turn_start:]):
                print(f"  {line}")
        print(f"\nClave: {reply}")
        history = trim_history(history)

    print(f"\nClave: {GOODBYE}")


if __name__ == "__main__":
    main(show_tools=SHOW_TOOLS_FLAG in sys.argv[1:])