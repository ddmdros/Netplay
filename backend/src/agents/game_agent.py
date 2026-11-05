"""O agente NetPlay: um LLM com tool calling que decide quando buscar dados reais."""
import os

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage

from ..tools.game_tools import game_search_tool

SYSTEM_PROMPT = """Você é o NetPlay, um assistente especialista em videogames.

Sua missão é conversar com o usuário de forma amigável e ajudá-lo a descobrir jogos, conferir a classificação
etária (público recomendado), estúdios e onde comprar ou baixar.

Regras:
1. Para qualquer dado de jogo (lançamento, estúdio, gênero, classificação, lojas), use a ferramenta
   'buscar_informacoes_de_jogos'. Nunca invente dados de jogos.
2. Para recomendações por faixa etária, busque os jogos e filtre pelo campo «Público recomendado».
3. Se não houver ferramenta para o que o usuário pediu, diga isso com clareza.
4. Use linguagem inclusiva e termos do mundo dos games."""

MODEL = os.getenv("NETPLAY_MODEL", "gpt-4o-mini")


def default_model():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=MODEL, temperature=0.2)


def build_agent(model=None):
    """Agente com uma ferramenta: a busca de jogos na API RAWG."""
    return create_agent(model or default_model(), tools=[game_search_tool], system_prompt=SYSTEM_PROMPT)


def to_messages(history):
    """[{"role": "user"|"assistant", "content": "..."}] -> mensagens do LangChain (ignora papéis desconhecidos)."""
    kinds = {"user": HumanMessage, "assistant": AIMessage}
    return [kinds[m["role"]](m["content"]) for m in history or [] if m.get("role") in kinds and m.get("content")]


def answer(agent, question: str, history=None) -> str:
    result = agent.invoke({"messages": to_messages(history) + [HumanMessage(question)]})
    return result["messages"][-1].content
