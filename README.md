# NetPlay

A games assistant with **tool calling**: a LangChain agent (OpenAI `gpt-4o-mini`) that decides on its own when to
fetch real game data from the [RAWG API](https://rawg.io/apidocs) (release date, studio, genre, age rating and
stores), behind a **FastAPI** API and with a chat in **React + TypeScript**.

The product idea behind it is a P2P economy for physical media: finding games near you to trade or rent. That
part (Postgres + PostGIS) already has the agent's tools, but the database schema is not in this repository yet.
It is only turned on when `DATABASE_URL` is set.

## How it works

```mermaid
sequenceDiagram
    participant U as Chat (React)
    participant A as FastAPI /api/chat
    participant G as Agent (LangChain)
    participant L as gpt-4o-mini
    participant R as RAWG API
    U->>A: question + history + user_id
    A->>G: builds the user's agent
    G->>L: messages + available tools
    L-->>G: tool call buscar_informacoes_de_jogos("...")
    G->>R: search + details of each game
    R-->>G: structured text (name, genre, studio, audience, stores)
    G->>L: tool result
    L-->>G: final answer
    G-->>A: text
    A-->>U: answer
```

- **Tool calling:** the model receives the tools' descriptions and chooses when to call them. The prompt forbids
  making up game data, and the answer comes from what RAWG returned.
- **Database tool safety:** the tools are created per request, already bound to the server-side `user_id`, and
  do not take the id as an argument, so the model cannot query another person by changing the id in a call. The
  queries are parameterized.
- **History:** the front end sends the latest messages, and the API uses the 10 most recent.

## Running it

Backend (Python 3.12+, with [uv](https://docs.astral.sh/uv/)):

```bash
cd backend
cp .env.example .env               # fill in OPENAI_API_KEY and RAWG_API_KEY
uv sync
uv run uvicorn src.main:app --reload       # API at http://127.0.0.1:8000 (docs at /docs)
uv run python -m src.cli                   # or chat from the terminal
```

Frontend (Node 22):

```bash
cd frontend
npm ci
npm run dev                        # http://localhost:5173
```

## Tests

```bash
cd backend && uv run --group dev python -m unittest discover -s tests -t . -v
cd frontend && npm run lint && npm run build
```

The backend tests run with no network and no API keys:
- RAWG is mocked, to check the structured text and the errors;
- the database is mocked, to check that the query uses the right user and that the tool does not take a `user_id`;
- a fake model that calls tools goes through the real agent (`create_agent`), from the tool call to the final
  answer;
- the API is tested with FastAPI's `TestClient`.

CI runs the tests and the front-end build on every push.

## Structure

```text
backend/src/
  main.py               FastAPI app, CORS
  api/chat_routes.py    POST /api/chat
  agents/game_agent.py  prompt, tools and create_agent
  tools/game_tools.py   RAWG tool
  tools/database_tools.py  P2P tools (optional)
  rawg.py               RAWG API client
  cli.py                terminal chat
frontend/src/           React chat
```

## History

The first version (May 2026) used `create_tool_calling_agent` and `AgentExecutor`, which were removed from the
`langchain` package in version 1.x. With current dependencies, the backend did not start. The November 2026
revision:

- migrated the agent to `create_agent`;
- fixed the imports (the route called a function that did not exist, and the agent imported the tool from the
  wrong file);
- fixed the nearby-games query, which ignored the user (it used a hard-coded id) and passed parameters the SQL
  did not have;
- bound the database tools to the user on the server;
- removed an unused duplicate prompt, the duplicate terminal script and the committed `egg-info`;
- restricted CORS and added the conversation history, the tests and CI.

## Credits

Built as a pair by Diogo Medeiros ([GitHub](https://github.com/ddmdros)) and Stephanie Pinho
([GitHub](https://github.com/stephanielumertz), [LinkedIn](https://www.linkedin.com/in/stephanielumertz/)).
The November 2026 revision (migration, fixes, tests and CI) came later.
