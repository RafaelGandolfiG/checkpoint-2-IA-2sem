# app/meta_prompting.py

import os

import tiktoken

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.chain import criar_llm

from app.prompts import (
    SYSTEM_PROMPT_GAMES,
    META_PROMPT_GAMES,
)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

PASTA_OUTPUT = "output"


ARQUIVO_ORIGINAL = os.path.join(PASTA_OUTPUT, "system_prompt_original.txt")


ARQUIVO_MELHORADO = os.path.join(PASTA_OUTPUT, "system_prompt_melhorado.txt")


ARQUIVO_COMPARACAO = os.path.join(PASTA_OUTPUT, "meta_prompting_comparacao.txt")


# ============================================================
# TOKENIZAÇÃO
# ============================================================


def criar_tokenizador():
    """
    Cria o tokenizador utilizado para estimar
    a quantidade de tokens dos prompts.
    """

    tokenizador = tiktoken.get_encoding("cl100k_base")

    return tokenizador


def contar_tokens(texto, tokenizador):
    """
    Conta aproximadamente a quantidade
    de tokens existente em um texto.
    """

    tokens = tokenizador.encode(texto)

    return len(tokens)


# ============================================================
# CHAIN DE META PROMPTING
# ============================================================


def criar_chain_meta_prompting():
    """
    Cria uma pipeline LCEL utilizando o próprio
    gemma4:cloud para melhorar o System Prompt.

    É utilizado num_predict maior porque o System Prompt
    original possui milhares de tokens e a nova versão
    precisa ser gerada completamente.
    """

    llm = criar_llm(temperatura=0.2, num_predict=4096)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Você é um especialista em "
                    "Prompt Engineering e "
                    "Context Engineering."
                ),
            ),
            ("human", META_PROMPT_GAMES),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    return chain


# ============================================================
# MELHORAR SYSTEM PROMPT
# ============================================================


def melhorar_system_prompt():
    """
    Envia o System Prompt original ao próprio modelo
    e solicita uma versão otimizada.
    """

    chain = criar_chain_meta_prompting()

    prompt_melhorado = chain.invoke({"system_prompt_original": SYSTEM_PROMPT_GAMES})

    return prompt_melhorado.strip()


# ============================================================
# VERIFICAÇÃO BÁSICA DO RESULTADO
# ============================================================


def verificar_prompt_melhorado(prompt_melhorado):
    """
    Faz verificações simples para detectar respostas
    claramente incompletas.

    Essa função não decide se o prompt é melhor.
    Ela apenas verifica se elementos fundamentais
    continuam presentes.
    """

    verificacoes = {
        "identidade": "<identidade>" in prompt_melhorado
        and "</identidade>" in prompt_melhorado,
        "dominio": "<dominio>" in prompt_melhorado and "</dominio>" in prompt_melhorado,
        "contexto": "<contexto>" in prompt_melhorado
        and "</contexto>" in prompt_melhorado,
        "confiabilidade": "<confiabilidade>" in prompt_melhorado
        and "</confiabilidade>" in prompt_melhorado,
        "prompt_injection": (
            "<guardrail_prompt_injection>" in prompt_melhorado
            and "</guardrail_prompt_injection>" in prompt_melhorado
        ),
        "jailbreak": (
            "<guardrail_jailbreak>" in prompt_melhorado
            and "</guardrail_jailbreak>" in prompt_melhorado
        ),
        "prompt_leaking": (
            "<guardrail_prompt_leaking>" in prompt_melhorado
            and "</guardrail_prompt_leaking>" in prompt_melhorado
        ),
        "privacidade": "<privacidade>" in prompt_melhorado
        and "</privacidade>" in prompt_melhorado,
        "formato_resposta": (
            "<formato_resposta>" in prompt_melhorado
            and "</formato_resposta>" in prompt_melhorado
        ),
        "prioridades": "<prioridades>" in prompt_melhorado
        and "</prioridades>" in prompt_melhorado,
    }

    return verificacoes


# ============================================================
# SALVAR PROMPTS
# ============================================================


def salvar_prompts(prompt_original, prompt_melhorado):
    """
    Salva o antes e depois para documentação
    do experimento de Meta Prompting.
    """

    os.makedirs(PASTA_OUTPUT, exist_ok=True)

    with open(ARQUIVO_ORIGINAL, "w", encoding="utf-8") as arquivo:

        arquivo.write(prompt_original)

    with open(ARQUIVO_MELHORADO, "w", encoding="utf-8") as arquivo:

        arquivo.write(prompt_melhorado)


# ============================================================
# SALVAR COMPARAÇÃO
# ============================================================


def salvar_comparacao(tokens_original, tokens_melhorado, verificacoes):
    """
    Salva um relatório resumido da comparação.
    """

    diferenca = tokens_melhorado - tokens_original

    percentual = (diferenca / tokens_original) * 100

    with open(ARQUIVO_COMPARACAO, "w", encoding="utf-8") as arquivo:

        arquivo.write("META PROMPTING - COMPARAÇÃO\n")

        arquivo.write("===========================\n\n")

        arquivo.write(f"Tokens do prompt original: " f"{tokens_original}\n")

        arquivo.write(f"Tokens do prompt melhorado: " f"{tokens_melhorado}\n")

        arquivo.write(f"Diferença: " f"{diferenca:+d} tokens\n")

        arquivo.write(f"Variação percentual: " f"{percentual:+.2f}%\n\n")

        arquivo.write("VERIFICAÇÃO DAS SEÇÕES\n")

        arquivo.write("======================\n\n")

        for nome, resultado in verificacoes.items():

            status = "OK" if resultado else "AUSENTE"

            arquivo.write(f"{nome}: {status}\n")


# ============================================================
# MOSTRAR COMPARAÇÃO
# ============================================================


def mostrar_comparacao(prompt_original, prompt_melhorado, verificacoes):
    """
    Mostra o antes/depois e as métricas
    do experimento.
    """

    tokenizador = criar_tokenizador()

    tokens_original = contar_tokens(prompt_original, tokenizador)

    tokens_melhorado = contar_tokens(prompt_melhorado, tokenizador)

    diferenca = tokens_melhorado - tokens_original

    percentual = (diferenca / tokens_original) * 100

    print("\n==========================================")

    print("             META PROMPTING")

    print("==========================================\n")

    print("SYSTEM PROMPT ORIGINAL")

    print("------------------------------------------\n")

    print(prompt_original)

    print("\n==========================================\n")

    print("SYSTEM PROMPT MELHORADO")

    print("------------------------------------------\n")

    print(prompt_melhorado)

    print("\n==========================================")

    print("              COMPARAÇÃO")

    print("==========================================\n")

    print(f"Tokens do prompt original: " f"{tokens_original}")

    print(f"Tokens do prompt melhorado: " f"{tokens_melhorado}")

    print(f"Diferença de tokens: " f"{diferenca:+d}")

    print(f"Variação percentual: " f"{percentual:+.2f}%")

    print("\n==========================================")

    print("       VERIFICAÇÃO DAS SEÇÕES")

    print("==========================================\n")

    for nome, resultado in verificacoes.items():

        if resultado:

            print(f"[OK] {nome}")

        else:

            print(f"[AUSENTE] {nome}")

    todas_presentes = all(verificacoes.values())

    print("\n==========================================")

    if todas_presentes:

        print("O prompt melhorado passou na " "verificação estrutural básica.")

    else:

        print("ATENÇÃO: o prompt melhorado perdeu " "uma ou mais seções importantes.")

        print(
            "Não utilize automaticamente essa versão " "como System Prompt principal."
        )

    print("==========================================")

    return (tokens_original, tokens_melhorado)


# ============================================================
# EXECUÇÃO COMPLETA
# ============================================================


def executar_meta_prompting():
    """
    Executa todo o experimento de Meta Prompting.
    """

    print("\nExecutando Meta Prompting...")

    # --------------------------------------------------------
    # PROMPT ORIGINAL
    # --------------------------------------------------------

    prompt_original = SYSTEM_PROMPT_GAMES

    # --------------------------------------------------------
    # PROMPT MELHORADO PELO MODELO
    # --------------------------------------------------------

    prompt_melhorado = melhorar_system_prompt()

    # --------------------------------------------------------
    # VERIFICAÇÃO
    # --------------------------------------------------------

    verificacoes = verificar_prompt_melhorado(prompt_melhorado)

    # --------------------------------------------------------
    # SALVAR PROMPTS
    # --------------------------------------------------------

    salvar_prompts(prompt_original, prompt_melhorado)

    # --------------------------------------------------------
    # MOSTRAR RESULTADOS
    # --------------------------------------------------------

    tokens_original, tokens_melhorado = mostrar_comparacao(
        prompt_original, prompt_melhorado, verificacoes
    )

    # --------------------------------------------------------
    # SALVAR RELATÓRIO
    # --------------------------------------------------------

    salvar_comparacao(tokens_original, tokens_melhorado, verificacoes)

    print("\nArquivos gerados:")

    print(ARQUIVO_ORIGINAL)

    print(ARQUIVO_MELHORADO)

    print(ARQUIVO_COMPARACAO)

    return prompt_melhorado


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    executar_meta_prompting()
