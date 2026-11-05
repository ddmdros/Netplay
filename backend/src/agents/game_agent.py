"""O agente NetPlay: um LLM com tool calling que decide quando buscar dados reais."""
import os

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage

from ..tools import database_tools
from ..tools.game_tools import game_search_tool

SYSTEM_PROMPT = """Você é o NetPlay, um assistente especialista em videogames.

Sua missão é conversar com o usuário de forma amigável e ajudá-lo a descobrir jogos, conferir a classificação
etária (público recomendado), estúdios e onde comprar ou baixar, e, quando disponível, encontrar jogos físicos
para troca ou aluguel perto dele.

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


def build_agent(user_id: str, model=None):
    """Agente para um usuário. As ferramentas de banco entram só com DATABASE_URL definida."""
    tools = [game_search_tool]
    if database_tools.enabled():
        tools += database_tools.make_database_tools(user_id)
    return create_agent(model or default_model(), tools=tools, system_prompt=SYSTEM_PROMPT)


def to_messages(history):
    """[{"role": "user"|"assistant", "content": "..."}] -> mensagens do LangChain (ignora papéis desconhecidos)."""
    kinds = {"user": HumanMessage, "assistant": AIMessage}
    return [kinds[m["role"]](m["content"]) for m in history or [] if m.get("role") in kinds and m.get("content")]


def answer(agent, question: str, history=None) -> str:
    result = agent.invoke({"messages": to_messages(history) + [HumanMessage(question)]})
    return result["messages"][-1].content
