"""Ferramenta do agente: dados reais de jogos pela API RAWG."""
import os

from langchain_core.tools import tool

from ..rawg import GameDataPipeline

_pipeline = None


def get_pipeline() -> GameDataPipeline:
    global _pipeline
    if _pipeline is None:
        key = os.getenv("RAWG_API_KEY")
        if not key:
            raise RuntimeError("RAWG_API_KEY não está definida. Veja o .env.example.")
        _pipeline = GameDataPipeline(api_key=key)
    return _pipeline


@tool("buscar_informacoes_de_jogos")
def game_search_tool(search_term: str) -> str:
    """Busca informações de jogos: nome, data de lançamento, gênero, estúdio, descrição, público recomendado
    (classificação etária) e lojas onde comprar ou baixar."""
    if not isinstance(search_term, str) or not search_term.strip():
        return "Termo de busca inválido. Informe o nome de um jogo ou assunto de jogos."
    return get_pipeline().fetch_and_structure_context(search_term.strip())
