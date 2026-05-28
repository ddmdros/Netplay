# backend/src/game_pipeline.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from tools.game_tools import game_search_tool


def create_main_chain():
    system_prompt = """Você é o NetPlay, um assistente inteligente especialista em videogames e recomendações de jogos.

Para responder sobre qualquer jogo, você utiliza a sua ferramenta interna que é conectada diretamente ao banco de dados oficial da RAWG API.

Sua missão é conversar com o usuário de forma amigável e ajudá-lo a descobrir jogos, verificar faixas etárias (público recomendado), estúdios e onde baixar.

REGRAS DE OURO:
1. Se o usuário perguntar sobre jogos, lançamentos, estúdios, plataformas ou detalhes técnicos, use SEMPRE a ferramenta 'buscar_informacoes_de_jogos'.
2. Se o usuário perguntar de onde você tira as informações, diga orgulhosamente que usa dados reais e atualizados da RAWG API através do pipeline do NetPlay.
3. Nunca tente adivinhar dados de jogos da sua cabeça se não tiver certeza."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    llm_with_tools = llm.bind_tools([game_search_tool])
    return prompt | llm_with_tools, llm


def create_followup_chain(llm):
    prompt_final = ChatPromptTemplate.from_template(
        "O usuário perguntou: \"{pergunta}\"\n"
        "Abaixo estão os dados reais encontrados no banco de dados da RAWG:\n"
        "{dados}\n\n"
        "Responda ao usuário de forma natural, amigável e objetiva com base nesses dados reais."
    )
    return prompt_final | llm


def main():
    load_dotenv()
    print(" [AGENTE] Inicializando inteligência do NetPlay (Sintaxe Moderna)...\n")

    chain, llm = create_main_chain()
    followup_chain = create_followup_chain(llm)

    print(" Chat do NetPlay Iniciado! Digite sua dúvida sobre jogos (ou 'sair'):")

    while True:
        try:
            pergunta = input("\nVocê: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Encerrando o NetPlay.")
            break

        if not pergunta:
            print("Por favor, digite uma pergunta sobre jogos ou 'sair'.")
            continue

        if pergunta.lower() == 'sair':
            print("👋 Até mais! Encerrando o NetPlay.")
            break

        print(" Pensando...")
        resposta_ia = chain.invoke({"input": pergunta})

        if resposta_ia.tool_calls:
            for tool_call in resposta_ia.tool_calls:
                if tool_call["name"] == "buscar_informacoes_de_jogos":
                    termo_busca = tool_call["args"].get("search_term", "")
                    print(f" [IA chamou a RAWG]: Buscando dados de '{termo_busca}'...")
                    dados_da_rawg = game_search_tool.invoke(termo_busca)
                    print(" formatando resposta final...")
                    resposta_final = followup_chain.invoke(
                        {"pergunta": pergunta, "dados": dados_da_rawg}
                    )
                    print(f"\nNetPlay: {resposta_final.content}")
                else:
                    print(f"\nNetPlay: {resposta_ia.content}")
        else:
            print(f"\nNetPlay: {resposta_ia.content}")


if __name__ == "__main__":
    main()
