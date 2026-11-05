"""Conversa com o agente pelo terminal: python -m src.cli (na pasta backend/)."""
from dotenv import load_dotenv

from .agents import game_agent


def main():
    load_dotenv()
    agent = game_agent.build_agent()
    history = []
    print("NetPlay no terminal. Digite sua dúvida sobre jogos (ou 'sair').")
    while True:
        try:
            q = input("\nVocê: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if q.lower() == "sair":
            break
        if q:
            reply = game_agent.answer(agent, q, history)
            print(f"\nNetPlay: {reply}")
            history = (history + [{"role": "user", "content": q}, {"role": "assistant", "content": reply}])[-10:]


if __name__ == "__main__":
    main()
