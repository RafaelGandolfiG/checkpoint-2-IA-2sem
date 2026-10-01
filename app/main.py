# app/main.py

import traceback

import gradio as gr

from app.chain import (
    llm_chat,
    analisar_consulta,
)

from app.memory_manager import (
    criar_chat_com_memoria,
    enviar_mensagem,
    limpar_memoria,
)

from app.prompts import SYSTEM_PROMPT_GAMES

from app.rag import buscar

# ============================================================
# CRIAÇÃO DO CHAT COM MEMÓRIA
# ============================================================

chat, memoria = criar_chat_com_memoria(
    llm=llm_chat,
    system_prompt=SYSTEM_PROMPT_GAMES,
)


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
# JOGOS PRESENTES NA BASE RAG
# ============================================================

JOGOS_RAG = {
    "god of war ragnarök": "god_of_war_ragnarok",
    "god of war ragnarok": "god_of_war_ragnarok",
    "god of war": "god_of_war_2018",
    "star wars jedi: fallen order": "jedi_fallen_order",
    "star wars jedi fallen order": "jedi_fallen_order",
    "jedi: fallen order": "jedi_fallen_order",
    "jedi fallen order": "jedi_fallen_order",
    "red dead redemption 2": "red_dead_redemption_2",
    "red dead redemption ii": "red_dead_redemption_2",
    "horizon forbidden west": "horizon_forbidden_west",
    "cyberpunk 2077": "cyber_punk_2077",
    "resident evil hd": "resident_evil_hd",
}


# ============================================================
# CONTEXTO PESSOAL
# ============================================================


def eh_contexto_pessoal(mensagem):
    """
    Detecta mensagens nas quais o usuário fornece
    informações pessoais úteis para a memória.

    Exemplos:

    Meu nome é Rafael.
    Eu prefiro RPG.
    Gosto de jogos difíceis.
    Minha plataforma é PC.
    """

    texto = mensagem.lower().strip()

    prefixos = [
        "meu nome é ",
        "meu nome e ",
        "me chamo ",
        "pode me chamar de ",
        "eu gosto de ",
        "eu gosto mais de ",
        "gosto de ",
        "eu prefiro ",
        "prefiro ",
        "minha plataforma é ",
        "minha plataforma e ",
        "eu jogo no ",
        "jogo no ",
        "meu gênero favorito é ",
        "meu genero favorito é ",
        "meu gênero favorito e ",
        "meu genero favorito e ",
    ]

    for prefixo in prefixos:

        if texto.startswith(prefixo):
            return True

    return False


# ============================================================
# CONSULTA SOBRE MEMÓRIA
# ============================================================


def eh_consulta_memoria(mensagem):
    """
    Detecta perguntas relacionadas a informações
    fornecidas anteriormente pelo usuário.

    Essas perguntas devem utilizar o chat com memória
    e não o RAG.
    """

    texto = mensagem.lower().strip()

    expressoes = [
        "qual é meu nome",
        "qual e meu nome",
        "como eu me chamo",
        "você lembra meu nome",
        "voce lembra meu nome",
        "lembra meu nome",
        "o que eu gosto",
        "do que eu gosto",
        "o que eu prefiro",
        "qual jogo eu prefiro",
        "qual tipo de jogo eu gosto",
        "qual tipo de jogo eu prefiro",
        "quais são minhas preferências",
        "quais sao minhas preferencias",
        "qual é minha preferência",
        "qual e minha preferencia",
        "qual minha plataforma",
        "em qual plataforma eu jogo",
        "considerando minhas preferências",
        "considerando minhas preferencias",
        "baseado nas minhas preferências",
        "baseado nas minhas preferencias",
        "com base nas minhas preferências",
        "com base nas minhas preferencias",
    ]

    for expressao in expressoes:

        if expressao in texto:
            return True

    return False


# ============================================================
# IDENTIFICAR JOGO DA BASE RAG
# ============================================================


def identificar_game_rag(nome_jogo):
    """
    Converte o nome identificado pela análise estruturada
    para o identificador utilizado nos metadados do RAG.

    Exemplo:

    God of War Ragnarök
            ↓
    god_of_war_ragnarok
    """

    if not nome_jogo:
        return None

    nome = nome_jogo.lower().strip()

    # --------------------------------------------------------
    # Correspondência exata primeiro
    # --------------------------------------------------------

    if nome in JOGOS_RAG:
        return JOGOS_RAG[nome]

    # --------------------------------------------------------
    # Correspondência parcial
    # --------------------------------------------------------

    # Ordenamos do maior nome para o menor.
    #
    # Isso evita que:
    #
    # "God of War Ragnarök"
    #
    # seja identificado primeiro simplesmente como
    # "God of War".
    # --------------------------------------------------------

    jogos_ordenados = sorted(
        JOGOS_RAG.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for nome_base, game in jogos_ordenados:

        if nome_base in nome:
            return game

    return None


# ============================================================
# DECIDIR SE DEVE USAR RAG
# ============================================================


def deve_usar_rag(analise):
    """
    Decide se a consulta deve utilizar recuperação
    de documentos.

    O RAG é utilizado quando:

    1. existe um jogo identificado;
    2. esse jogo existe na base documental;
    3. a consulta é adequada para busca documental.

    Recomendações gerais e consultas pessoais são
    tratadas pelo chat com memória.
    """

    if analise.jogo_mencionado is None:
        return False

    game = identificar_game_rag(analise.jogo_mencionado)

    if game is None:
        return False

    # --------------------------------------------------------
    # Tipos que normalmente se beneficiam dos documentos
    # --------------------------------------------------------

    tipos_rag = [
        "informacao",
        "estrategia",
    ]

    if analise.tipo_consulta in tipos_rag:
        return True

    # --------------------------------------------------------
    # Comparações também podem utilizar documentos
    # se houver um jogo conhecido na base.
    # --------------------------------------------------------

    if analise.tipo_consulta == "comparacao":
        return True

    return False


# ============================================================
# FORMATAR RESPOSTA DO RAG
# ============================================================


def formatar_resposta_rag(resultado):
    """
    Converte a resposta do pipeline RAG para o formato
    apresentado na interface.

    Adiciona as fontes recuperadas ao final.
    """

    resposta = resultado["resposta"]

    fontes = resultado.get(
        "fontes",
        [],
    )

    if not fontes:
        return resposta

    resposta += "\n\n### Fontes\n"

    for fonte in fontes:

        source = fonte.get(
            "source",
            "Fonte desconhecida",
        )

        pagina = fonte.get(
            "page",
            "desconhecida",
        )

        resposta += f"\n- {source} " f"— página {pagina}"

    return resposta


# ============================================================
# CHAT CONVERSACIONAL
# ============================================================


def responder_chat(mensagem):
    """
    Envia a mensagem para o modelo conversacional
    com memória.

    Utilizado para:

    - recomendações;
    - preferências;
    - perguntas pessoais;
    - conhecimento geral de games;
    - jogos não presentes nos PDFs.
    """

    print("\nConsulta enviada para " "CHAT + MEMÓRIA...")

    resposta = enviar_mensagem(
        chat,
        mensagem,
    )

    return resposta


# ============================================================
# RAG
# ============================================================


def responder_rag(
    mensagem,
    game,
):
    """
    Executa o pipeline RAG final.

    Atualmente o pipeline final utiliza a configuração
    1000/100 selecionada após a avaliação com RAGAS.
    """

    print("\nConsulta enviada para " "PIPELINE RAG...")

    print(f"Filtro do jogo: {game}")

    resultado = buscar(
        consulta=mensagem,
        game=game,
    )

    return formatar_resposta_rag(resultado)


# ============================================================
# FUNÇÃO PRINCIPAL DO CHATBOT
# ============================================================


def responder(
    mensagem,
    _historico,
):

    try:

        # ====================================================
        # VALIDAR MENSAGEM
        # ====================================================

        if not mensagem:

            return "Digite uma mensagem para " "conversar com o GameGuide."

        mensagem = mensagem.strip()

        if not mensagem:

            return "Digite uma mensagem para " "conversar com o GameGuide."

        # ====================================================
        # ANÁLISE ESTRUTURADA
        # ====================================================

        analise = analisar_consulta(mensagem)

        print("\n==========================================")

        print("       ANÁLISE DA CONSULTA")

        print("==========================================")

        print(f"Dentro do domínio: " f"{analise.dentro_dominio}")

        print(f"Assunto: " f"{analise.assunto}")

        print(f"Tipo: " f"{analise.tipo_consulta}")

        print(f"Jogo mencionado: " f"{analise.jogo_mencionado}")

        print("Precisa de contexto adicional: " f"{analise.precisa_contexto_adicional}")

        print(f"Resumo: " f"{analise.resumo}")

        print("==========================================\n")

        # ====================================================
        # IDENTIFICAR TIPOS ESPECIAIS
        # ====================================================

        contexto_pessoal = eh_contexto_pessoal(mensagem)

        consulta_memoria = eh_consulta_memoria(mensagem)

        # ====================================================
        # 1. CONTEXTO PESSOAL
        # ====================================================

        if contexto_pessoal:

            print("Contexto pessoal detectado.")

            return responder_chat(mensagem)

        # ====================================================
        # 2. CONSULTA SOBRE MEMÓRIA
        # ====================================================

        if consulta_memoria:

            print("Consulta de memória detectada.")

            return responder_chat(mensagem)

        # ====================================================
        # 3. FORA DO DOMÍNIO
        # ====================================================

        if not analise.dentro_dominio:

            print("Consulta fora do domínio.")

            return MENSAGEM_FORA_DOMINIO

        # ====================================================
        # 4. VERIFICAR RAG
        # ====================================================

        if deve_usar_rag(analise):

            game = identificar_game_rag(analise.jogo_mencionado)

            return responder_rag(
                mensagem=mensagem,
                game=game,
            )

        # ====================================================
        # 5. CHAT GERAL DE GAMES
        # ====================================================

        return responder_chat(mensagem)

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
    title="GameGuide — DocMind RAG",
    description=(
        "Assistente virtual especializado em games "
        "com recuperação de documentos, RAG e memória "
        "conversacional."
    ),
    examples=[
        ("Como funciona o combate em " "God of War Ragnarök?"),
        ("Quais são os requisitos de sistema de " "Red Dead Redemption 2 para PC?"),
        (
            "Quais recursos de acessibilidade existem "
            "em Star Wars Jedi: Fallen Order?"
        ),
        ("O que é a expansão Burning Shores de " "Horizon Forbidden West?"),
        ("Me recomende um RPG difícil para PC."),
        ("O que é um RPG?"),
    ],
)


# ============================================================
# EXECUÇÃO
# ============================================================


if __name__ == "__main__":

    print("\n==========================================")

    print("        GAMEGUIDE — DOCMIND RAG")

    print("==========================================")

    print("Iniciando interface...")

    print("Pipeline RAG final: 1000/100")

    print("Chat geral: LLM + memória")

    print("Pressione CTRL + C para encerrar.")

    print("==========================================\n")

    interface.launch()
