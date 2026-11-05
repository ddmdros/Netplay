"""Ferramentas da economia P2P de mídia física (Postgres + PostGIS).

As ferramentas são criadas por requisição, já presas ao usuário logado: o `user_id` vem do servidor, não do
modelo. Assim o LLM não consegue consultar dados de outra pessoa trocando o id numa chamada de ferramenta.
Só entram no agente quando DATABASE_URL está definida.
"""
import os
from contextlib import closing

from langchain_core.tools import tool

SEARCH_RADIUS_METERS = 10_000

ACCOUNT_SQL = "SELECT name, reputation, city, platforms FROM users WHERE id = %s;"

LOCAL_GAMES_SQL = """
    SELECT catalog.title, catalog.platform, inventory.condition, owner.name,
           ST_Distance(owner.location, searcher.location) AS distance
    FROM user_inventory AS inventory
    JOIN game_catalog AS catalog ON inventory.game_id = catalog.id
    JOIN users AS owner ON inventory.user_id = owner.id
    CROSS JOIN (SELECT location FROM users WHERE id = %s) AS searcher
    WHERE inventory.status = 'AVAILABLE'
      AND owner.id != %s
      AND ST_DWithin(owner.location, searcher.location, %s)
    ORDER BY distance ASC;
"""


def enabled():
    return bool(os.getenv("DATABASE_URL"))


def connect():
    import psycopg2

    return psycopg2.connect(os.environ["DATABASE_URL"])


def _query(sql, params, connect_fn):
    with closing(connect_fn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def make_database_tools(user_id: str, connect_fn=connect):
    """Ferramentas de banco presas a `user_id`."""

    @tool
    def get_account_info() -> str:
        """Dados da conta do usuário logado: nome, reputação, cidade e consoles."""
        try:
            rows = _query(ACCOUNT_SQL, (user_id,), connect_fn)
        except Exception as e:
            return f"Erro ao acessar o banco de dados: {e}"
        if not rows:
            return "Usuário não encontrado."
        name, reputation, city, platforms = rows[0]
        consoles = ", ".join(platforms) if platforms else "nenhum"
        return f"Nome: {name}\nReputação: {reputation}/5.0\nCidade: {city}\nConsoles: {consoles}"

    @tool
    def search_local_games() -> str:
        """Jogos físicos disponíveis para troca ou aluguel num raio de 10 km do usuário, sem contar os dele."""
        try:
            rows = _query(LOCAL_GAMES_SQL, (user_id, user_id, SEARCH_RADIUS_METERS), connect_fn)
        except Exception as e:
            return f"Erro na busca local: {e}"
        if not rows:
            return "Não encontramos jogos físicos disponíveis perto de você agora."
        lines = ["Jogos físicos disponíveis perto de você:"]
        for title, platform, condition, owner, distance in rows:
            lines.append(f"- {title} ({platform}) | Estado: {condition} | Dono: {owner} ({distance / 1000:.1f} km)")
        return "\n".join(lines)

    return [get_account_info, search_local_games]
