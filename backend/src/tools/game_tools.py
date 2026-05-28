# backend/src/tools/game_tools.py
import os
from dotenv import load_dotenv
from langchain.tools import tool
from dados import GameDataPipeline

pipeline = None


def get_pipeline() -> GameDataPipeline:
    global pipeline
    if pipeline is None:
        load_dotenv()
        rawg_api_key = os.getenv("RAWG_API_KEY")
        if not rawg_api_key:
            raise RuntimeError(
                "RAWG_API_KEY não está definido. Verifique o arquivo .env ou a variável de ambiente."
            )
        pipeline = GameDataPipeline(api_key=rawg_api_key)
    return pipeline


@tool("buscar_informacoes_de_jogos")
def game_search_tool(search_term: str) -> str:
    """Útil quando você precisa saber informações de jogos como nome, data de lançamento, gênero, estúdio desenvolvedor, descrição, público recomendado e lojas de download."""
    if not isinstance(search_term, str) or not search_term.strip():
        return "Termo de busca inválido. Informe o nome de um jogo ou assunto de jogos."
    return get_pipeline().fetch_and_structure_context(search_term.strip())