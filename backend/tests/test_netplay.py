"""Backend do NetPlay sem rede: RAWG simulada e um modelo falso que chama ferramentas."""
import os, unittest
from unittest import mock

from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

from src import rawg
from src.agents import game_agent
from src.tools import game_tools

class FakeToolModel(GenericFakeChatModel):
    """Modelo falso que aceita bind_tools e devolve as mensagens dadas, em ordem."""

    def bind_tools(self, tools, **kwargs):
        return self


def fake_response(json_data):
    r = mock.Mock()
    r.json.return_value = json_data
    r.raise_for_status.return_value = None
    return r


GAME = {"id": 1, "name": "Jogo Fictício", "released": "2024-05-01", "genres": [{"name": "RPG"}],
        "stores": [{"store": {"name": "Loja X"}}], "esrb_rating": {"name": "Teen"}}
DETAIL = {"developers": [{"name": "Estúdio Y"}], "description_raw": "Uma aventura. " * 50}


class RawgTest(unittest.TestCase):
    def test_structured_context(self):
        with mock.patch.object(rawg.requests, "get", side_effect=[fake_response({"results": [GAME]}),
                                                                   fake_response(DETAIL)]) as get:
            text = rawg.GameDataPipeline("k").fetch_and_structure_context("  fictício ")
        self.assertIn("Nome: Jogo Fictício", text)
        self.assertIn("Público recomendado: Teen", text)
        self.assertIn("Estúdio/Developer: Estúdio Y", text)
        self.assertIn("Onde encontrar/Download: Loja X", text)
        self.assertTrue(text.split("Descrição: ")[1].startswith("Uma aventura.") and "..." in text)
        self.assertEqual(get.call_args_list[0].kwargs["params"]["search"], "fictício")

    def test_no_results_and_errors(self):
        with mock.patch.object(rawg.requests, "get", return_value=fake_response({"results": []})):
            self.assertIn("Nenhum jogo encontrado", rawg.GameDataPipeline("k").fetch_and_structure_context("x"))
        with mock.patch.object(rawg.requests, "get", side_effect=rawg.requests.exceptions.Timeout("lento")):
            self.assertIn("Erro ao acessar", rawg.GameDataPipeline("k").fetch_and_structure_context("x"))

    def test_tool_requires_key(self):
        game_tools._pipeline = None
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                game_tools.game_search_tool.invoke("zelda")
        self.assertIn("inválido", game_tools.game_search_tool.invoke("   "))


class AgentTest(unittest.TestCase):
    def test_agent_calls_rawg_then_answers(self):
        model = FakeToolModel(messages=iter([
            AIMessage("", tool_calls=[{"name": "buscar_informacoes_de_jogos", "args": {"search_term": "fictício"},
                                       "id": "call_1"}]),
            AIMessage("Jogo Fictício é um RPG para maiores de 13 anos."),
        ]))
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(game_tools, "get_pipeline") as gp:
            gp.return_value.fetch_and_structure_context.return_value = "Nome: Jogo Fictício"
            agent = game_agent.build_agent(model=model)
            result = agent.invoke({"messages": game_agent.to_messages([]) + [("user", "Me fala do Jogo Fictício")]})
        tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
        self.assertEqual(tool_msgs[0].content, "Nome: Jogo Fictício")
        self.assertEqual(result["messages"][-1].content, "Jogo Fictício é um RPG para maiores de 13 anos.")

    def test_agent_has_only_the_rawg_tool(self):
        captured = {}

        def fake_create_agent(model, tools, system_prompt):
            captured["tools"] = [t.name for t in tools]

        with mock.patch.object(game_agent, "create_agent", side_effect=fake_create_agent):
            game_agent.build_agent(model=object())
        self.assertEqual(captured["tools"], ["buscar_informacoes_de_jogos"])

    def test_history_conversion(self):
        msgs = game_agent.to_messages([{"role": "user", "content": "oi"}, {"role": "assistant", "content": "olá"},
                                       {"role": "system", "content": "ignore"}, {"role": "user", "content": ""}])
        self.assertEqual([m.type for m in msgs], ["human", "ai"])


class ApiTest(unittest.TestCase):
    def setUp(self):
        from src.main import app
        self.client = TestClient(app)

    def test_root(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_chat_passes_question_and_history(self):
        with mock.patch.object(game_agent, "build_agent") as build, \
             mock.patch.object(game_agent, "answer", return_value="resposta") as ans:
            r = self.client.post("/api/chat", json={"input": "oi", "history": [{"role": "user", "content": "antes"}]})
        self.assertEqual(r.json(), {"response": "resposta"})
        build.assert_called_once_with()
        self.assertEqual(ans.call_args.args[1:], ("oi", [{"role": "user", "content": "antes"}]))

    def test_validation_and_agent_errors(self):
        self.assertEqual(self.client.post("/api/chat", json={"input": ""}).status_code, 422)
        with mock.patch.object(game_agent, "build_agent", side_effect=RuntimeError("sem chave")):
            r = self.client.post("/api/chat", json={"input": "oi"})
        self.assertEqual(r.status_code, 500)
        self.assertIn("sem chave", r.json()["detail"])


if __name__ == "__main__":
    unittest.main()
