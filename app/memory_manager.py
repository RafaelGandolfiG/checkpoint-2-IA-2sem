# app/memory_manager.py

from langchain_classic.chains import ConversationChain
from langchain_classic.memory import ConversationTokenBufferMemory
from langchain_core.prompts import PromptTemplate

from app.prompts import MEMORY_PROMPT_GAMES

# ============================================================
# CONFIGURAÇÃO DA MEMÓRIA
# ============================================================

# O CKP exige um limite entre 800 e 1500 tokens.
# Escolhemos 1000 tokens para equilibrar:
# - quantidade de contexto;
# - custo de tokens;
# - informações recentes relevantes.

MAX_TOKENS_MEMORIA = 1000


# ============================================================
# CRIAR MEMÓRIA
# ============================================================


def criar_memoria(llm):
    """
    Cria a memória utilizada pelo chatbot.

    Foi escolhida ConversationTokenBufferMemory porque
    mantém as mensagens recentes da conversa e controla
    o crescimento do histórico através de um limite
    de tokens.
    """

    memoria = ConversationTokenBufferMemory(
        llm=llm,
        memory_key="history",
        max_token_limit=MAX_TOKENS_MEMORIA,
        return_messages=False,
    )

    return memoria


# ============================================================
# CRIAR PROMPT DA CONVERSATIONCHAIN
# ============================================================


def criar_prompt_memoria(system_prompt):
    """
    Cria o PromptTemplate utilizado pela ConversationChain.

    O histórico da memória é inserido automaticamente
    através da variável {history}.

    A mensagem atual do usuário é inserida através
    da variável {input}.
    """

    prompt = PromptTemplate(
        input_variables=["history", "input"],
        partial_variables={"system_prompt": system_prompt},
        template=MEMORY_PROMPT_GAMES,
    )

    return prompt


# ============================================================
# CRIAR CHAT COM MEMÓRIA
# ============================================================


def criar_chat_com_memoria(llm, system_prompt):
    """
    Cria a ConversationChain responsável pelo chat principal.

    Retorna:
    - chat: ConversationChain;
    - memoria: ConversationTokenBufferMemory.

    Retornamos os dois objetos para permitir que outros
    módulos possam consultar, testar ou limpar a memória.
    """

    memoria = criar_memoria(llm)

    prompt = criar_prompt_memoria(system_prompt)

    chat = ConversationChain(llm=llm, memory=memoria, prompt=prompt, verbose=False)

    return chat, memoria


# ============================================================
# ENVIAR MENSAGEM
# ============================================================


def enviar_mensagem(chat, mensagem):
    """
    Envia uma mensagem para a ConversationChain.

    A própria ConversationChain:
    1. recupera o histórico;
    2. adiciona o histórico ao prompt;
    3. envia para o modelo;
    4. recebe a resposta;
    5. salva a nova interação na memória.
    """

    resposta = chat.predict(input=mensagem)

    return resposta


# ============================================================
# OBTER HISTÓRICO
# ============================================================


def obter_historico(memoria):
    """
    Retorna o conteúdo atualmente armazenado
    na memória da conversa.
    """

    estado_memoria = memoria.load_memory_variables({})

    historico = estado_memoria.get("history", "")

    return historico


# ============================================================
# MOSTRAR HISTÓRICO
# ============================================================


def mostrar_historico(memoria):
    """
    Exibe o histórico atual da memória.

    Útil principalmente para testes e demonstração
    do funcionamento da memória.
    """

    historico = obter_historico(memoria)

    print("\n=== HISTÓRICO DA MEMÓRIA ===\n")

    if historico:
        print(historico)

    else:
        print("A memória está vazia.")


# ============================================================
# LIMPAR MEMÓRIA
# ============================================================


def limpar_memoria(memoria):
    """
    Remove todas as mensagens armazenadas
    na memória atual.
    """

    memoria.clear()


# ============================================================
# TESTAR MEMÓRIA
# ============================================================


def testar_memoria(chat, memoria):
    """
    Demonstra que o chatbot consegue manter informações
    durante pelo menos 5 turnos de conversa.

    O teste utiliza informações relevantes ao domínio
    de games, permitindo verificar se o modelo consegue
    recuperar preferências informadas anteriormente.
    """

    perguntas = [
        "Meu nome é Rafael.",
        "Eu jogo principalmente no PC.",
        "Meu gênero favorito é RPG.",
        "Eu prefiro jogos single-player.",
        "Eu gosto de jogos difíceis e desafiadores.",
        (
            "Com base no que eu falei anteriormente, "
            "qual é minha plataforma principal, "
            "meu gênero favorito e qual estilo de jogo "
            "eu prefiro?"
        ),
    ]

    print("\n=== TESTE DA MEMÓRIA ===\n")

    for numero, pergunta in enumerate(perguntas, start=1):

        print(f"Turno {numero}")

        print(f"Usuário: {pergunta}")

        resposta = enviar_mensagem(chat, pergunta)

        print(f"GameGuide: {resposta}\n")

    mostrar_historico(memoria)
