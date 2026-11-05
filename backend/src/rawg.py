"""Cliente da API RAWG: busca jogos e monta um texto limpo para o agente usar como contexto."""
import requests
from typing import Any, Dict, List

class GameDataPipeline:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.rawg.io/api/games"

    def _get_detailed_game_info(self, game_id: int) -> Dict[str, Any]:
        """Busca detalhes profundos do jogo (como estúdio e descrição) usando o ID."""
        url = f"{self.base_url}/{game_id}"
        try:
            response = requests.get(url, params={"key": self.api_key}, timeout=8)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return {}

    def _join_names(self, items: List[Dict[str, Any]], default: str = "Não especificado") -> str:
        if not items:
            return default
        names = [item.get("name") for item in items if isinstance(item, dict) and item.get("name")]
        return ", ".join(names) if names else default

    def _normalize_text(self, value: Any, default: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return default

    def fetch_and_structure_context(self, search_term: str) -> str:
        """Busca pelo nome do jogo e cria o texto limpo para o RAG."""
        search_term = self._normalize_text(search_term, "")
        if not search_term:
            return "Nenhum termo de busca fornecido."

        params = {
            "search": search_term,
            "key": self.api_key,
            "page_size": 5,
            "ordering": "-released"
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=8)
            response.raise_for_status()
            results = response.json().get("results") or []

            if not results:
                return f"Nenhum jogo encontrado para: '{search_term}'."

            context_blocks = []
            for game in results:
                game_id = game.get("id")
                name = self._normalize_text(game.get("name"), "Desconhecido")
                genres = self._join_names(game.get("genres", []))
                stores = self._join_names(
                    [store.get("store") for store in game.get("stores", []) if isinstance(store, dict)]
                )
                rating = game.get("esrb_rating")
                publico = self._normalize_text(
                    rating.get("name") if isinstance(rating, dict) else "",
                    "Classificação Livre"
                )

                detailed = self._get_detailed_game_info(game_id) if game_id else {}
                studios = self._join_names(detailed.get("developers", []), default="Desconhecido")
                description = self._normalize_text(detailed.get("description_raw"), "Sem descrição.")
                if len(description) > 400:
                    description = description[:400].rstrip() + "..."
                release_date = self._normalize_text(game.get("released"), "Data desconhecida")

                game_text = (
                    "=== JOGO ENCONTRADO ===\n"
                    f"Nome: {name}\n"
                    f"Gênero: {genres}\n"
                    f"Data de Lançamento: {release_date}\n"
                    f"Público recomendado: {publico}\n"
                    f"Estúdio/Developer: {studios}\n"
                    f"Onde encontrar/Download: {stores}\n"
                    f"Descrição: {description}\n"
                    "=======================\n"
                )
                context_blocks.append(game_text)

            return "\n".join(context_blocks)

        except requests.exceptions.RequestException as exc:
            return f"Erro ao acessar os dados: {str(exc)}"