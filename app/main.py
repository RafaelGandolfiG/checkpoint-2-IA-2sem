# app/main.py

import traceback
import gradio as gr

from app.chain import llm_chat, analisar_consulta
from app.memory_manager import criar_chat_com_memoria, enviar_mensagem, limpar_memoria
from app.prompts import SYSTEM_PROMPT_GAMES

# ============================================================
# CRIAÇÃO DO CHAT COM MEMÓRIA
# ============================================================

chat, memoria = criar_chat_com_memoria(llm=llm_chat, system_prompt=SYSTEM_PROMPT_GAMES)


# ============================================================
# MENSAGEM PARA ASSUNTOS FORA DO DOMÍNIO
# ============================================================

MENSAGEM_FORA_DOMINIO = (
    "Minha especialidade é games. "
    "Posso ajudar com jogos, consoles, plataformas, "
    "mecânicas, estratégias, recomendações, comparações "
    "e assuntos relacionados."
)


# ============================================================
# VERIFICAR CONTEXTO PESSOAL PERMITIDO
# ============================================================


def eh_contexto_pessoal(mensagem):
    """
    Identifica mensagens pessoais simples que podem ser
    úteis para personalizar futuras conversas sobre games.

    Exemplo:
    "Meu nome é Rafael."

    Essas mensagens podem ser armazenadas na memória,
    mesmo não sendo diretamente uma pergunta sobre games.
    """

    texto = mensagem.lower().strip()

    prefixos_permitidos = [
        "meu nome é ",
        "meu nome e ",
        "me chamo ",
        "pode me chamar de ",
    ]

    for prefixo in prefixos_permitidos:

        if texto.startswith(prefixo):
            return True

    return False


# ============================================================
# FUNÇÃO PRINCIPAL DO CHATBOT
# ============================================================


def responder(mensagem, _historico):

    try:

        # ----------------------------------------------------
        # VALIDAR MENSAGEM
        # ----------------------------------------------------

        if not mensagem:

            return "Digite uma mensagem para conversar " "com o GameGuide."

        mensagem = mensagem.strip()

        if not mensagem:

            return "Digite uma mensagem para conversar " "com o GameGuide."

        # ----------------------------------------------------
        # ANÁLISE ESTRUTURADA
        # ----------------------------------------------------

        analise = analisar_consulta(mensagem)

        print("\n==========================================")

        print("       ANÁLISE DA CONSULTA")

        print("==========================================")

        print(f"Dentro do domínio: " f"{analise.dentro_dominio}")

        print(f"Assunto: " f"{analise.assunto}")

        print(f"Tipo: " f"{analise.tipo_consulta}")

        print(f"Jogo mencionado: " f"{analise.jogo_mencionado}")

        print(
            f"Precisa de contexto adicional: " f"{analise.precisa_contexto_adicional}"
        )

        print(f"Resumo: " f"{analise.resumo}")

        print("==========================================\n")

        # ----------------------------------------------------
        # CONTEXTO PESSOAL
        # ----------------------------------------------------

        contexto_pessoal = eh_contexto_pessoal(mensagem)

        # ----------------------------------------------------
        # FORA DO DOMÍNIO
        # ----------------------------------------------------

        if not analise.dentro_dominio and not contexto_pessoal:

            return MENSAGEM_FORA_DOMINIO

        # ----------------------------------------------------
        # CHAT COM MEMÓRIA
        # ----------------------------------------------------

        resposta = enviar_mensagem(chat, mensagem)

        return resposta

    # ========================================================
    # TRATAMENTO DE ERROS
    # ========================================================

    except Exception as erro:

        print("\n==========================================")

        print("            ERRO NO CHAT")

        print("==========================================\n")

        print(f"Tipo do erro: " f"{type(erro).__name__}")

        print(f"Mensagem: " f"{erro}")

        print("\nTraceback completo:\n")

        traceback.print_exc()

        print("\n==========================================\n")

        return "Ocorreu um problema ao gerar a resposta. " "Tente novamente."


# ============================================================
# LIMPAR CONVERSA
# ============================================================


def limpar_conversa():

    try:

        limpar_memoria(memoria)

        print("\nMemória do GameGuide limpa.")

    except Exception:

        print("\nErro ao limpar a memória.")

        traceback.print_exc()


# ============================================================
# INTERFACE GRADIO
# ============================================================

interface = gr.ChatInterface(
    fn=responder,
    title="GameGuide",
    description=(
        "Assistente virtual profissional " "especializado no universo de games."
    ),
    examples=[
        "O que é um RPG?",
        "Me recomende um RPG difícil para PC.",
        ("Elden Ring ou Dark Souls 3, " "qual é mais difícil?"),
        (
            "Quais são as principais diferenças "
            "entre jogos single-player e multiplayer?"
        ),
    ],
)


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    print("\n==========================================")

    print("            GAMEGUIDE")

    print("==========================================")

    print("Iniciando interface...")

    print("Pressione CTRL + C para encerrar.")

    print("==========================================\n")

    interface.launch()
