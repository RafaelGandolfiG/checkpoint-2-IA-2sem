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
    Identifica mensagens em que o usuário fornece
    informações pessoais úteis para personalizar
    futuras conversas sobre games.
    """

    texto = mensagem.lower().strip()

    prefixos_permitidos = [
        # ====================================================
        # NOME
        # ====================================================
        "meu nome é ",
        "meu nome e ",
        "me chamo ",
        "eu me chamo ",
        "pode me chamar de ",
        "pode chamar de ",
        "me chama de ",
        "me chame de ",
        "quero ser chamado de ",
        "gosto de ser chamado de ",
        "eu sou ",
        "sou ",
        # ====================================================
        # JOGOS QUE GOSTA
        # ====================================================
        "eu gosto de ",
        "gosto de ",
        "eu gosto muito de ",
        "gosto muito de ",
        "eu curto ",
        "curto ",
        "eu curto muito ",
        "curto muito ",
        "eu adoro ",
        "adoro ",
        "eu amo ",
        "amo ",
        "sou fã de ",
        "sou fa de ",
        "eu sou fã de ",
        "eu sou fa de ",
        "um jogo que eu gosto é ",
        "um jogo que eu gosto e ",
        "um jogo que gosto é ",
        "um jogo que gosto e ",
        "meu jogo favorito é ",
        "meu jogo favorito e ",
        "o meu jogo favorito é ",
        "o meu jogo favorito e ",
        "meu game favorito é ",
        "meu game favorito e ",
        "meus jogos favoritos são ",
        "meus jogos favoritos sao ",
        "os jogos que eu gosto são ",
        "os jogos que eu gosto sao ",
        "os jogos que mais gosto são ",
        "os jogos que mais gosto sao ",
        # ====================================================
        # PREFERÊNCIA
        # ====================================================
        "eu prefiro ",
        "prefiro ",
        "eu tenho preferência por ",
        "eu tenho preferencia por ",
        "tenho preferência por ",
        "tenho preferencia por ",
        "minha preferência é ",
        "minha preferencia é ",
        "minha preferencia e ",
        "a minha preferência é ",
        "a minha preferencia é ",
        "a minha preferencia e ",
        "eu tenho preferência por jogos ",
        "eu tenho preferencia por jogos ",
        "tenho preferência por jogos ",
        "tenho preferencia por jogos ",
        # ====================================================
        # GÊNERO DE JOGO
        # ====================================================
        "meu gênero favorito é ",
        "meu genero favorito é ",
        "meu genero favorito e ",
        "o meu gênero favorito é ",
        "o meu genero favorito é ",
        "o meu genero favorito e ",
        "meu gênero preferido é ",
        "meu genero preferido é ",
        "meu genero preferido e ",
        "meu tipo de jogo favorito é ",
        "meu tipo de jogo favorito e ",
        "meu tipo de jogo preferido é ",
        "meu tipo de jogo preferido e ",
        "eu gosto do gênero ",
        "eu gosto do genero ",
        "gosto do gênero ",
        "gosto do genero ",
        "eu prefiro o gênero ",
        "eu prefiro o genero ",
        "prefiro o gênero ",
        "prefiro o genero ",
        "eu gosto de jogos de ",
        "gosto de jogos de ",
        "eu prefiro jogos de ",
        "prefiro jogos de ",
        # ====================================================
        # PLATAFORMA
        # ====================================================
        "eu jogo no ",
        "jogo no ",
        "eu jogo na ",
        "jogo na ",
        "eu jogo em ",
        "jogo em ",
        "eu costumo jogar no ",
        "costumo jogar no ",
        "eu costumo jogar na ",
        "costumo jogar na ",
        "eu costumo jogar em ",
        "costumo jogar em ",
        "minha plataforma é ",
        "minha plataforma e ",
        "minha plataforma principal é ",
        "minha plataforma principal e ",
        "a minha plataforma é ",
        "a minha plataforma e ",
        "a minha plataforma principal é ",
        "a minha plataforma principal e ",
        "minha plataforma favorita é ",
        "minha plataforma favorita e ",
        "minha plataforma preferida é ",
        "minha plataforma preferida e ",
        "eu uso pc ",
        "uso pc ",
        "eu uso playstation ",
        "uso playstation ",
        "eu uso xbox ",
        "uso xbox ",
        "eu tenho um pc ",
        "tenho um pc ",
        "eu tenho um playstation ",
        "tenho um playstation ",
        "eu tenho um xbox ",
        "tenho um xbox ",
        # ====================================================
        # DIFICULDADE
        # ====================================================
        "eu gosto de jogos difíceis",
        "eu gosto de jogos dificeis",
        "gosto de jogos difíceis",
        "gosto de jogos dificeis",
        "eu prefiro jogos difíceis",
        "eu prefiro jogos dificeis",
        "prefiro jogos difíceis",
        "prefiro jogos dificeis",
        "eu gosto de jogos fáceis",
        "eu gosto de jogos faceis",
        "gosto de jogos fáceis",
        "gosto de jogos faceis",
        "eu prefiro jogos fáceis",
        "eu prefiro jogos faceis",
        "prefiro jogos fáceis",
        "prefiro jogos faceis",
        "eu gosto de jogos desafiadores",
        "gosto de jogos desafiadores",
        "eu prefiro jogos desafiadores",
        "prefiro jogos desafiadores",
        "eu gosto de dificuldade alta",
        "gosto de dificuldade alta",
        "eu prefiro dificuldade alta",
        "prefiro dificuldade alta",
        "eu gosto de dificuldade baixa",
        "gosto de dificuldade baixa",
        "eu prefiro dificuldade baixa",
        "prefiro dificuldade baixa",
        "minha dificuldade favorita é ",
        "minha dificuldade favorita e ",
        "minha dificuldade preferida é ",
        "minha dificuldade preferida e ",
        # ====================================================
        # SINGLE-PLAYER / MULTIPLAYER
        # ====================================================
        "eu gosto de single-player",
        "eu gosto de single player",
        "gosto de single-player",
        "gosto de single player",
        "eu prefiro single-player",
        "eu prefiro single player",
        "prefiro single-player",
        "prefiro single player",
        "eu gosto de multiplayer",
        "gosto de multiplayer",
        "eu prefiro multiplayer",
        "prefiro multiplayer",
        "eu gosto de jogar sozinho",
        "gosto de jogar sozinho",
        "eu prefiro jogar sozinho",
        "prefiro jogar sozinho",
        "eu gosto de jogar com amigos",
        "gosto de jogar com amigos",
        "eu prefiro jogar com amigos",
        "prefiro jogar com amigos",
        "eu gosto de jogar online",
        "gosto de jogar online",
        "eu prefiro jogar online",
        "prefiro jogar online",
        # ====================================================
        # ESTILO DE JOGO
        # ====================================================
        "meu estilo de jogo é ",
        "meu estilo de jogo e ",
        "o meu estilo de jogo é ",
        "o meu estilo de jogo e ",
        "meu estilo favorito é ",
        "meu estilo favorito e ",
        "meu estilo preferido é ",
        "meu estilo preferido e ",
        "eu gosto de explorar ",
        "gosto de explorar ",
        "eu gosto de exploração ",
        "eu gosto de exploracao ",
        "gosto de exploração ",
        "gosto de exploracao ",
        "eu gosto de combate ",
        "gosto de combate ",
        "eu gosto de história ",
        "eu gosto de historia ",
        "gosto de história ",
        "gosto de historia ",
        "eu gosto de jogos com história ",
        "eu gosto de jogos com historia ",
        "gosto de jogos com história ",
        "gosto de jogos com historia ",
        "eu gosto de mundo aberto ",
        "gosto de mundo aberto ",
        "eu prefiro mundo aberto ",
        "prefiro mundo aberto ",
        "eu gosto de jogos lineares ",
        "gosto de jogos lineares ",
        "eu prefiro jogos lineares ",
        "prefiro jogos lineares ",
        # ====================================================
        # NÃO GOSTA
        # ====================================================
        "eu não gosto de ",
        "eu nao gosto de ",
        "não gosto de ",
        "nao gosto de ",
        "eu não curto ",
        "eu nao curto ",
        "não curto ",
        "nao curto ",
        "eu odeio ",
        "odeio ",
        "não sou fã de ",
        "nao sou fã de ",
        "não sou fa de ",
        "nao sou fa de ",
        "eu não sou fã de ",
        "eu nao sou fã de ",
        "eu não sou fa de ",
        "eu nao sou fa de ",
        "eu evito ",
        "evito ",
        # ====================================================
        # CARACTERÍSTICAS QUE PROCURA
        # ====================================================
        "eu gosto quando o jogo ",
        "gosto quando o jogo ",
        "eu prefiro quando o jogo ",
        "prefiro quando o jogo ",
        "eu gosto de jogos que ",
        "gosto de jogos que ",
        "eu prefiro jogos que ",
        "prefiro jogos que ",
        "eu gosto de jogos com ",
        "gosto de jogos com ",
        "eu prefiro jogos com ",
        "prefiro jogos com ",
        "para mim um bom jogo ",
        "pra mim um bom jogo ",
        "para mim o mais importante é ",
        "para mim o mais importante e ",
        "pra mim o mais importante é ",
        "pra mim o mais importante e ",
        # ====================================================
        # INFORMAÇÕES SOBRE O JOGADOR
        # ====================================================
        "eu sou jogador de ",
        "sou jogador de ",
        "eu sou jogador casual",
        "sou jogador casual",
        "eu sou jogador competitivo",
        "sou jogador competitivo",
        "eu jogo bastante ",
        "jogo bastante ",
        "eu jogo muito ",
        "jogo muito ",
        "eu jogo pouco ",
        "jogo pouco ",
        "normalmente eu jogo ",
        "normalmente jogo ",
        "geralmente eu jogo ",
        "geralmente jogo ",
        "costumo jogar ",
        "eu costumo jogar ",
        # ====================================================
        # FRASES DE MEMÓRIA EXPLÍCITA
        # ====================================================
        "lembre que ",
        "lembra que ",
        "lembre-se que ",
        "lembre-se de que ",
        "quero que você lembre que ",
        "quero que voce lembre que ",
        "quero que você se lembre que ",
        "quero que voce se lembre que ",
        "guarde que ",
        "guarda que ",
        "anote que ",
        "anota que ",
        "para você saber ",
        "para voce saber ",
        "pra você saber ",
        "pra voce saber ",
        "só para você saber ",
        "so para voce saber ",
        "só pra você saber ",
        "so pra voce saber ",
        "uma coisa sobre mim é ",
        "uma coisa sobre mim e ",
        "sobre mim ",
    ]

    for prefixo in prefixos_permitidos:
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

    Essas perguntas utilizam o chat com memória
    em vez do RAG.
    """

    texto = mensagem.lower().strip()

    expressoes = [
        # ====================================================
        # NOME / IDENTIDADE
        # ====================================================
        "qual é meu nome",
        "qual e meu nome",
        "qual é o meu nome",
        "qual e o meu nome",
        "como eu me chamo",
        "como me chamo",
        "quem sou eu",
        "quem eu sou",
        "você sabe meu nome",
        "voce sabe meu nome",
        "você sabe o meu nome",
        "voce sabe o meu nome",
        "você lembra meu nome",
        "voce lembra meu nome",
        "você lembra o meu nome",
        "voce lembra o meu nome",
        "lembra meu nome",
        "lembra o meu nome",
        "você lembra como eu me chamo",
        "voce lembra como eu me chamo",
        "me diga meu nome",
        "me diga o meu nome",
        "fala meu nome",
        "fale meu nome",
        # ====================================================
        # GOSTOS
        # ====================================================
        "o que eu gosto",
        "do que eu gosto",
        "que jogo eu gosto",
        "qual jogo eu gosto",
        "quais jogos eu gosto",
        "que jogos eu gosto",
        "que tipo de jogo eu gosto",
        "qual tipo de jogo eu gosto",
        "quais tipos de jogos eu gosto",
        "qual gênero eu gosto",
        "qual genero eu gosto",
        "quais gêneros eu gosto",
        "quais generos eu gosto",
        "você sabe do que eu gosto",
        "voce sabe do que eu gosto",
        "você lembra do que eu gosto",
        "voce lembra do que eu gosto",
        "lembra do que eu gosto",
        "lembra que jogo eu gosto",
        "lembra quais jogos eu gosto",
        "me diga do que eu gosto",
        "me diga quais jogos eu gosto",
        # ====================================================
        # PREFERÊNCIAS
        # ====================================================
        "o que eu prefiro",
        "qual jogo eu prefiro",
        "que jogo eu prefiro",
        "quais jogos eu prefiro",
        "que jogos eu prefiro",
        "qual tipo de jogo eu prefiro",
        "que tipo de jogo eu prefiro",
        "qual gênero eu prefiro",
        "qual genero eu prefiro",
        "quais são minhas preferências",
        "quais sao minhas preferencias",
        "quais são as minhas preferências",
        "quais sao as minhas preferencias",
        "qual é minha preferência",
        "qual e minha preferencia",
        "qual é a minha preferência",
        "qual e a minha preferencia",
        "você sabe minhas preferências",
        "voce sabe minhas preferencias",
        "você lembra minhas preferências",
        "voce lembra minhas preferencias",
        "lembra das minhas preferências",
        "lembra das minhas preferencias",
        "me diga minhas preferências",
        "me diga minhas preferencias",
        # ====================================================
        # PLATAFORMA
        # ====================================================
        "qual minha plataforma",
        "qual é minha plataforma",
        "qual e minha plataforma",
        "qual é a minha plataforma",
        "qual e a minha plataforma",
        "em qual plataforma eu jogo",
        "em que plataforma eu jogo",
        "qual plataforma eu uso",
        "que plataforma eu uso",
        "onde eu jogo",
        "eu jogo onde",
        "você sabe onde eu jogo",
        "voce sabe onde eu jogo",
        "você lembra onde eu jogo",
        "voce lembra onde eu jogo",
        "lembra onde eu jogo",
        "você sabe minha plataforma",
        "voce sabe minha plataforma",
        "você lembra minha plataforma",
        "voce lembra minha plataforma",
        # ====================================================
        # DIFICULDADE
        # ====================================================
        "qual dificuldade eu gosto",
        "que dificuldade eu gosto",
        "eu gosto de jogos difíceis",
        "eu gosto de jogos dificeis",
        "eu prefiro jogos difíceis",
        "eu prefiro jogos dificeis",
        "eu gosto de jogos fáceis",
        "eu gosto de jogos faceis",
        "eu prefiro jogos fáceis",
        "eu prefiro jogos faceis",
        "que nível de dificuldade eu gosto",
        "que nivel de dificuldade eu gosto",
        "qual nível de dificuldade eu gosto",
        "qual nivel de dificuldade eu gosto",
        "você lembra da dificuldade que eu gosto",
        "voce lembra da dificuldade que eu gosto",
        # ====================================================
        # ESTILO DE JOGO
        # ====================================================
        "qual estilo de jogo eu gosto",
        "que estilo de jogo eu gosto",
        "qual é meu estilo de jogo",
        "qual e meu estilo de jogo",
        "qual é o meu estilo de jogo",
        "qual e o meu estilo de jogo",
        "eu prefiro single-player",
        "eu prefiro single player",
        "eu prefiro multiplayer",
        "prefiro jogar sozinho",
        "prefiro jogar com outras pessoas",
        "você lembra do meu estilo de jogo",
        "voce lembra do meu estilo de jogo",
        # ====================================================
        # INFORMAÇÕES ANTERIORES
        # ====================================================
        "o que eu te falei",
        "o que eu disse",
        "o que eu falei",
        "o que eu te disse",
        "o que eu disse antes",
        "o que eu falei antes",
        "o que eu te falei antes",
        "o que eu te disse antes",
        "o que você sabe sobre mim",
        "o que voce sabe sobre mim",
        "o que você lembra sobre mim",
        "o que voce lembra sobre mim",
        "você lembra de mim",
        "voce lembra de mim",
        "lembra de mim",
        "lembra o que eu disse",
        "lembra o que eu falei",
        # ====================================================
        # RECOMENDAÇÕES BASEADAS NA MEMÓRIA
        # ====================================================
        "considerando minhas preferências",
        "considerando minhas preferencias",
        "considerando as minhas preferências",
        "considerando as minhas preferencias",
        "baseado nas minhas preferências",
        "baseado nas minhas preferencias",
        "baseado nas minhas preferências pessoais",
        "baseado nas minhas preferencias pessoais",
        "com base nas minhas preferências",
        "com base nas minhas preferencias",
        "de acordo com minhas preferências",
        "de acordo com minhas preferencias",
        "de acordo com as minhas preferências",
        "de acordo com as minhas preferencias",
        "baseado no que eu gosto",
        "com base no que eu gosto",
        "considerando o que eu gosto",
        "de acordo com o que eu gosto",
        "pensando no que eu gosto",
        "baseado no que eu prefiro",
        "com base no que eu prefiro",
        "considerando o que eu prefiro",
        "baseado no que eu te falei",
        "baseado no que eu disse",
        "com base no que eu te falei",
        "com base no que eu disse",
        "usando minhas preferências",
        "usando minhas preferencias",
        "use minhas preferências",
        "use minhas preferencias",
        # ====================================================
        # RECOMENDAÇÕES PESSOAIS
        # ====================================================
        "me recomende baseado no que eu gosto",
        "me recomende algo baseado no que eu gosto",
        "me recomende um jogo baseado no que eu gosto",
        "me recomenda baseado no que eu gosto",
        "me recomenda um jogo baseado no que eu gosto",
        "me recomende baseado nas minhas preferências",
        "me recomende baseado nas minhas preferencias",
        "me recomende um jogo baseado nas minhas preferências",
        "me recomende um jogo baseado nas minhas preferencias",
        "qual jogo você me recomenda baseado no que eu gosto",
        "qual jogo voce me recomenda baseado no que eu gosto",
        "qual jogo você recomenda para mim",
        "qual jogo voce recomenda para mim",
        "o que você me recomenda",
        "o que voce me recomenda",
        "o que você recomenda para mim",
        "o que voce recomenda para mim",
        # ====================================================
        # COMPARAÇÃO COM PREFERÊNCIAS
        # ====================================================
        "qual combina mais comigo",
        "qual jogo combina mais comigo",
        "que jogo combina mais comigo",
        "qual seria melhor para mim",
        "qual jogo seria melhor para mim",
        "qual é melhor para mim",
        "qual e melhor para mim",
        "qual você acha que eu gostaria mais",
        "qual voce acha que eu gostaria mais",
        "qual eu gostaria mais",
        "qual deles eu gostaria mais",
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
    # CORRESPONDÊNCIA EXATA
    # --------------------------------------------------------

    if nome in JOGOS_RAG:
        return JOGOS_RAG[nome]

    # --------------------------------------------------------
    # CORRESPONDÊNCIA PARCIAL
    # --------------------------------------------------------
    #
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

    # --------------------------------------------------------
    # PRECISA EXISTIR UM JOGO
    # --------------------------------------------------------

    if analise.jogo_mencionado is None:
        return False

    # --------------------------------------------------------
    # O JOGO PRECISA ESTAR NA BASE
    # --------------------------------------------------------

    game = identificar_game_rag(analise.jogo_mencionado)

    if game is None:
        return False

    # --------------------------------------------------------
    # TIPOS QUE NORMALMENTE SE BENEFICIAM DOS DOCUMENTOS
    # --------------------------------------------------------

    tipos_rag = [
        "informacao",
        "estrategia",
    ]

    if analise.tipo_consulta in tipos_rag:
        return True

    # --------------------------------------------------------
    # COMPARAÇÕES
    # --------------------------------------------------------
    #
    # Comparações também podem utilizar documentos
    # quando existe um jogo conhecido na base.
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
    - recuperação de informações da memória;
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
    """
    Função principal responsável pelo roteamento
    das mensagens do GameGuide.

    Ordem utilizada:

    1. valida a mensagem;
    2. realiza análise estruturada;
    3. identifica contexto pessoal;
    4. identifica consultas sobre memória;
    5. bloqueia assuntos fora de games;
    6. utiliza RAG quando apropriado;
    7. utiliza chat geral para os demais casos.
    """

    try:

        # ====================================================
        # 1. VALIDAR MENSAGEM
        # ====================================================

        if not mensagem:
            return "Digite uma mensagem para " "conversar com o GameGuide."

        mensagem = mensagem.strip()

        if not mensagem:
            return "Digite uma mensagem para " "conversar com o GameGuide."

        # ====================================================
        # 2. ANÁLISE ESTRUTURADA
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
        # 3. IDENTIFICAR TIPOS ESPECIAIS
        # ====================================================

        contexto_pessoal = eh_contexto_pessoal(mensagem)

        consulta_memoria = eh_consulta_memoria(mensagem)

        # ====================================================
        # 4. CONTEXTO PESSOAL
        # ====================================================
        #
        # Essa verificação ocorre antes do domínio porque:
        #
        # "Meu nome é Rafael."
        #
        # não é uma pergunta sobre games, mas é uma
        # informação válida para a memória.
        # ====================================================

        if contexto_pessoal:

            print("Contexto pessoal detectado.")

            return responder_chat(mensagem)

        # ====================================================
        # 5. CONSULTA SOBRE MEMÓRIA
        # ====================================================
        #
        # Também precisa ocorrer antes da verificação
        # de domínio.
        #
        # Exemplo:
        #
        # "Qual é o meu nome?"
        #
        # A análise pode considerar isso fora do domínio
        # de games, mas o chatbot deve consultar a memória.
        # ====================================================

        if consulta_memoria:

            print("Consulta de memória detectada.")

            return responder_chat(mensagem)

        # ====================================================
        # 6. FORA DO DOMÍNIO
        # ====================================================

        if not analise.dentro_dominio:

            print("Consulta fora do domínio.")

            return MENSAGEM_FORA_DOMINIO

        # ====================================================
        # 7. VERIFICAR RAG
        # ====================================================

        if deve_usar_rag(analise):

            game = identificar_game_rag(analise.jogo_mencionado)

            return responder_rag(
                mensagem=mensagem,
                game=game,
            )

        # ====================================================
        # 8. CHAT GERAL DE GAMES
        # ====================================================
        #
        # Se chegou até aqui:
        #
        # - está dentro do domínio de games;
        # - não precisa obrigatoriamente do RAG;
        # - não é uma consulta pessoal especial.
        #
        # Exemplos:
        #
        # "O que é um RPG?"
        #
        # "Me recomende um RPG difícil."
        #
        # "Como funciona Minecraft?"
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
    """
    Limpa a memória conversacional do GameGuide.
    """

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
