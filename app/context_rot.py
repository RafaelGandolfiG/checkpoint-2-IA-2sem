# app/context_rot.py

import os
import re

import pandas as pd
import matplotlib.pyplot as plt
import tiktoken

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.chain import llm
from app.prompts import SYSTEM_PROMPT_GAMES, CONTEXT_ROT_PROMPT_GAMES

# ============================================================
# CONFIGURAÇÕES
# ============================================================

PASTA_OUTPUT = "output"


# Experimento principal exigido pelo projeto.
TURNOS_TESTE = [0, 5, 10, 15, 20]


# Teste adicional para observar contextos muito maiores.
TURNOS_STRESS = [0, 20, 50, 100, 150]


# ============================================================
# INFORMAÇÕES IMPORTANTES
# ============================================================

INFORMACOES_IMPORTANTES = """
O nome do usuário é Rafael.

A plataforma principal do usuário é PC.

O gênero favorito do usuário é RPG.

O usuário prefere jogos single-player.

O usuário gosta de jogos difíceis e desafiadores.
"""


# ============================================================
# PERGUNTA DO EXPERIMENTO
# ============================================================

PERGUNTA_TESTE = """
Com base exclusivamente no contexto fornecido, responda:

1. Qual é o nome do usuário?
2. Qual é a plataforma principal do usuário?
3. Qual é o gênero favorito do usuário?
4. O usuário prefere single-player ou multiplayer?
5. Que tipo de dificuldade o usuário prefere?
"""


# ============================================================
# TÓPICOS UTILIZADOS COMO CONTEXTO IRRELEVANTE
# ============================================================

TOPICOS = [
    (
        "Jogos de corrida possuem diferentes estilos, "
        "como arcade e simulação. Alguns priorizam física "
        "realista enquanto outros focam em acessibilidade."
    ),
    (
        "Jogos competitivos costumam utilizar sistemas "
        "de ranking para organizar jogadores de acordo "
        "com desempenho e habilidade."
    ),
    (
        "Em jogos de estratégia, administração de recursos "
        "e planejamento podem ser tão importantes quanto "
        "a velocidade das decisões."
    ),
    (
        "Jogos multiplayer podem utilizar servidores "
        "dedicados ou sistemas peer-to-peer dependendo "
        "da arquitetura escolhida."
    ),
    (
        "Diversos jogos utilizam sistemas de progressão "
        "para liberar habilidades, equipamentos ou novas "
        "áreas conforme o jogador avança."
    ),
    (
        "Em jogos de mundo aberto, exploração normalmente "
        "é um elemento importante da experiência."
    ),
    (
        "Jogos de terror podem utilizar iluminação, "
        "design de som e limitação de recursos para "
        "aumentar a tensão."
    ),
    (
        "Sistemas de crafting permitem que jogadores "
        "utilizem recursos coletados para criar novos itens."
    ),
    (
        "Jogos de ação podem utilizar diferentes sistemas "
        "de combate, incluindo ataques corpo a corpo "
        "e ataques à distância."
    ),
    (
        "Muitos jogos utilizam checkpoints para registrar "
        "o progresso do jogador durante uma fase."
    ),
    (
        "Jogos cooperativos incentivam jogadores a "
        "trabalharem juntos para atingir objetivos."
    ),
    (
        "Em jogos com árvores de habilidades, pontos "
        "podem ser distribuídos entre diferentes atributos."
    ),
    (
        "Alguns jogos utilizam geração procedural para "
        "criar mapas, itens ou eventos de forma dinâmica."
    ),
    (
        "Jogos com sistema de inventário podem limitar "
        "a quantidade ou peso dos itens carregados."
    ),
    (
        "Em jogos de plataforma, precisão dos controles "
        "pode influenciar bastante a dificuldade."
    ),
    (
        "Jogos de sobrevivência normalmente envolvem "
        "gerenciamento de recursos e exploração."
    ),
    (
        "Alguns jogos apresentam diferentes finais "
        "dependendo das escolhas realizadas pelo jogador."
    ),
    (
        "Jogos com economia interna podem utilizar moedas "
        "virtuais para aquisição de equipamentos ou itens."
    ),
    (
        "Em jogos baseados em equipes, personagens podem "
        "possuir funções como ataque, defesa ou suporte."
    ),
    (
        "Sistemas de dificuldade podem alterar atributos "
        "dos inimigos, recursos disponíveis e outros "
        "elementos da experiência."
    ),
]


# ============================================================
# TOKENIZADOR
# ============================================================


def criar_tokenizador():
    """
    Cria um tokenizador utilizado somente para estimar
    a quantidade aproximada de tokens do contexto.

    cl100k_base não é o tokenizador exato do gemma4:cloud.
    A contagem é utilizada apenas como aproximação.
    """

    return tiktoken.get_encoding("cl100k_base")


def contar_tokens(texto, tokenizador):
    """
    Retorna a quantidade aproximada de tokens.
    """

    tokens = tokenizador.encode(texto)

    return len(tokens)


# ============================================================
# CRIAÇÃO DOS TURNOS
# ============================================================


def criar_turno(numero):
    """
    Cria um turno adicional de contexto.

    Os turnos adicionam informações relacionadas a games
    que não são necessárias para responder à pergunta final.

    Algumas informações sobre outros usuários também são
    adicionadas para tornar a recuperação mais desafiadora,
    mas sem contradizer diretamente os dados do Rafael
    utilizados como resposta correta.
    """

    indice = numero % len(TOPICOS)

    topico = TOPICOS[indice]

    turno = f"""
Turno {numero + 1}:

Usuário:
Explique rapidamente algum conceito relacionado a games.

Assistente:
{topico}
"""

    # --------------------------------------------------------
    # DISTRAÇÕES SEMÂNTICAS
    # --------------------------------------------------------

    if numero % 7 == 2:

        turno += """
Informação adicional:
Bruno costuma jogar jogos multiplayer competitivos
principalmente em consoles.
"""

    if numero % 11 == 4:

        turno += """
Informação adicional:
Lucas gosta principalmente de jogos de corrida
e costuma jogar em dispositivos móveis.
"""

    if numero % 13 == 6:

        turno += """
Informação adicional:
Gabriel prefere jogos cooperativos e normalmente
joga com amigos.
"""

    if numero % 17 == 8:

        turno += """
Informação adicional:
Existe outro jogador chamado Rafael que participou
de uma partida multiplayer em um console.

Essa informação descreve apenas uma partida específica
e não representa necessariamente suas preferências gerais.
"""

    return turno


# ============================================================
# CRIAÇÃO DO CONTEXTO
# ============================================================


def criar_contexto(quantidade_turnos):
    """
    Cria o contexto utilizado no teste.

    As informações relevantes ficam no início.

    Depois são adicionados turnos progressivamente,
    aumentando o tamanho do contexto.
    """

    contexto = INFORMACOES_IMPORTANTES

    for numero in range(quantidade_turnos):

        contexto += criar_turno(numero)

    return contexto


# ============================================================
# CHAIN DO EXPERIMENTO
# ============================================================


def criar_chain_context_rot():
    """
    Cria a pipeline LCEL utilizada no teste.
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT_GAMES), ("human", CONTEXT_ROT_PROMPT_GAMES)]
    )

    chain = prompt | llm | StrOutputParser()

    return chain


# ============================================================
# AVALIAÇÃO DA RESPOSTA
# ============================================================


def avaliar_resposta(resposta):
    """
    Avalia automaticamente se as cinco informações
    principais foram recuperadas.

    Cada informação correta vale 1 ponto.

    Pontuação máxima: 5.
    """

    texto = resposta.lower()

    pontuacao = 0

    # --------------------------------------------------------
    # 1. NOME
    # --------------------------------------------------------

    if re.search(r"\brafael\b", texto):

        pontuacao += 1

    # --------------------------------------------------------
    # 2. PLATAFORMA PRINCIPAL
    # --------------------------------------------------------

    # \b verifica limite da palavra.
    #
    # Dessa forma:
    #
    # PC.
    # PC
    # plataforma principal: PC
    #
    # são reconhecidos corretamente.
    #
    # Evita procurar apenas "pc" como substring.

    if re.search(r"\bpc\b", texto):

        pontuacao += 1

    # --------------------------------------------------------
    # 3. GÊNERO FAVORITO
    # --------------------------------------------------------

    if re.search(r"\brpg\b", texto):

        pontuacao += 1

    # --------------------------------------------------------
    # 4. SINGLE-PLAYER
    # --------------------------------------------------------

    padrao_single_player = r"\bsingle[- ]player\b"

    if re.search(padrao_single_player, texto):

        pontuacao += 1

    # --------------------------------------------------------
    # 5. DIFICULDADE
    # --------------------------------------------------------

    encontrou_dificuldade = (
        "difícil" in texto
        or "difíceis" in texto
        or "desafiador" in texto
        or "desafiadores" in texto
    )

    if encontrou_dificuldade:

        pontuacao += 1

    return pontuacao


# ============================================================
# EXECUTAR UM TESTE
# ============================================================


def executar_teste(chain, quantidade_turnos, tokenizador):
    """
    Executa um teste específico com determinada
    quantidade de turnos.
    """

    print(f"Executando teste com " f"{quantidade_turnos} turnos...")

    # --------------------------------------------------------
    # CONTEXTO
    # --------------------------------------------------------

    contexto = criar_contexto(quantidade_turnos)

    # --------------------------------------------------------
    # TOKENS
    # --------------------------------------------------------

    tokens = contar_tokens(contexto, tokenizador)

    # --------------------------------------------------------
    # MODELO
    # --------------------------------------------------------

    resposta = chain.invoke({"contexto": contexto, "pergunta": PERGUNTA_TESTE})

    # --------------------------------------------------------
    # AVALIAÇÃO
    # --------------------------------------------------------

    pontuacao = avaliar_resposta(resposta)

    qualidade = (pontuacao / 5) * 100

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print(f"Tokens aproximados: " f"{tokens}")

    print(f"Pontuação: " f"{pontuacao}/5")

    print(f"Qualidade: " f"{qualidade:.0f}%")

    print("\nResposta:")

    print(resposta)

    print("\n------------------------------------------\n")

    resultado = {
        "Turnos": quantidade_turnos,
        "Tokens": tokens,
        "Pontuação": pontuacao,
        "Qualidade (%)": qualidade,
        "Resposta": resposta,
    }

    return resultado


# ============================================================
# EXECUTAR VÁRIOS TESTES
# ============================================================


def executar_testes(turnos):
    """
    Executa os testes para todas as quantidades
    de contexto informadas.
    """

    chain = criar_chain_context_rot()

    tokenizador = criar_tokenizador()

    resultados = []

    for quantidade in turnos:

        resultado = executar_teste(chain, quantidade, tokenizador)

        resultados.append(resultado)

    return resultados


# ============================================================
# ANALISAR DEGRADAÇÃO
# ============================================================


def analisar_degradacao(dataframe):
    """
    Analisa os resultados reais.

    Só considera que ocorreu degradação se a qualidade
    diminuir conforme o contexto cresce.
    """

    print("\n==========================================")

    print("        ANÁLISE DA DEGRADAÇÃO")

    print("==========================================\n")

    qualidades = dataframe["Qualidade (%)"].tolist()

    houve_degradacao = False

    for i in range(1, len(qualidades)):

        if qualidades[i] < qualidades[i - 1]:

            houve_degradacao = True

    if houve_degradacao:

        print("Foi observada degradação de qualidade " "conforme o contexto cresceu.")

        print("Em pelo menos uma das janelas, " "a pontuação diminuiu.")

    else:

        print(
            "Não foi observada degradação de qualidade "
            "nas condições deste experimento."
        )

        print(
            "O modelo conseguiu recuperar corretamente "
            "as cinco informações avaliadas."
        )


# ============================================================
# SALVAR CSV
# ============================================================


def salvar_csv(dataframe, caminho):
    """
    Salva os resultados em CSV.
    """

    os.makedirs(PASTA_OUTPUT, exist_ok=True)

    dataframe.to_csv(caminho, index=False, encoding="utf-8-sig")

    print(f"\nCSV salvo em: " f"{caminho}")


# ============================================================
# GERAR GRÁFICO
# ============================================================


def gerar_grafico(dataframe, caminho, titulo):
    """
    Gera gráfico mostrando a qualidade
    em função do tamanho do contexto.
    """

    os.makedirs(PASTA_OUTPUT, exist_ok=True)

    plt.figure(figsize=(9, 5))

    plt.plot(dataframe["Tokens"], dataframe["Qualidade (%)"], marker="o")

    for _, linha in dataframe.iterrows():

        plt.annotate(
            f'{int(linha["Turnos"])} turnos',
            (linha["Tokens"], linha["Qualidade (%)"]),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )

    plt.title(titulo)

    plt.xlabel("Tokens aproximados do contexto")

    plt.ylabel("Qualidade (%)")

    plt.ylim(0, 110)

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(caminho)

    plt.close()

    print(f"Gráfico salvo em: " f"{caminho}")


# ============================================================
# EXPERIMENTO PRINCIPAL
# ============================================================


def executar_experimento_principal():
    """
    Executa o experimento obrigatório:

    0
    5
    10
    15
    20 turnos.
    """

    print("\n==========================================")

    print("       EXPERIMENTO PRINCIPAL")

    print("==========================================\n")

    resultados = executar_testes(TURNOS_TESTE)

    dataframe = pd.DataFrame(resultados)

    colunas_exibicao = ["Turnos", "Tokens", "Pontuação", "Qualidade (%)"]

    print("\n==========================================")

    print("       RESULTADOS PRINCIPAIS")

    print("==========================================\n")

    print(dataframe[colunas_exibicao].to_string(index=False))

    analisar_degradacao(dataframe)

    caminho_csv = os.path.join(PASTA_OUTPUT, "context_rot_resultados.csv")

    caminho_grafico = os.path.join(PASTA_OUTPUT, "context_rot_grafico.png")

    salvar_csv(dataframe, caminho_csv)

    gerar_grafico(
        dataframe, caminho_grafico, ("Context Rot - " "Experimento Principal")
    )

    return dataframe


# ============================================================
# STRESS TEST
# ============================================================


def executar_stress_test():
    """
    Executa um teste adicional utilizando
    contextos significativamente maiores.

    Esse teste não substitui o experimento
    principal de 0/5/10/15/20.
    """

    print("\n==========================================")

    print("       STRESS TEST DE CONTEXTO")

    print("==========================================\n")

    resultados = executar_testes(TURNOS_STRESS)

    dataframe = pd.DataFrame(resultados)

    colunas_exibicao = ["Turnos", "Tokens", "Pontuação", "Qualidade (%)"]

    print("\n==========================================")

    print("       RESULTADOS DO STRESS TEST")

    print("==========================================\n")

    print(dataframe[colunas_exibicao].to_string(index=False))

    analisar_degradacao(dataframe)

    caminho_csv = os.path.join(PASTA_OUTPUT, "context_rot_stress.csv")

    caminho_grafico = os.path.join(PASTA_OUTPUT, "context_rot_stress.png")

    salvar_csv(dataframe, caminho_csv)

    gerar_grafico(dataframe, caminho_grafico, ("Context Rot - " "Stress Test"))

    return dataframe


# ============================================================
# EXECUÇÃO COMPLETA
# ============================================================


def executar_experimento_context_rot():
    """
    Executa o experimento principal e o
    stress test adicional.
    """

    print("\nGAMEGUIDE - CONTEXT ROT")

    print("Mesmo prompt com contextos crescentes.")

    print(
        "A qualidade somente será considerada "
        "degradada caso os resultados reais "
        "apresentem queda."
    )

    # --------------------------------------------------------
    # EXPERIMENTO PRINCIPAL
    # --------------------------------------------------------

    dataframe_principal = executar_experimento_principal()

    # --------------------------------------------------------
    # STRESS TEST
    # --------------------------------------------------------

    dataframe_stress = executar_stress_test()

    return (dataframe_principal, dataframe_stress)


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    executar_experimento_context_rot()
