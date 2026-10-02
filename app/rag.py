import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser

from app.prompts import PROMPT_RAG
from app.retriever import recuperar_documentos
from app.parent_retriever import recuperar_documentos_parent
from app.vectorstore import (
    COLLECTION_500,
    COLLECTION_1000,
)

load_dotenv()


OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma4:cloud",
)


# ============================================================
# LLM
# ============================================================


def criar_llm():
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_HOST,
        temperature=0,
        client_kwargs={"headers": {"Authorization": f"Bearer {OLLAMA_API_KEY}"}},
    )

    return llm


# ============================================================
# FORMATAÇÃO DO CONTEXTO
# ============================================================


def formatar_contexto(documentos):
    partes = []

    for documento in documentos:
        jogo = documento.metadata.get(
            "game",
            "desconhecido",
        )

        arquivo = documento.metadata.get(
            "file_name",
            "desconhecido",
        )

        pagina = documento.metadata.get("page")

        if pagina is not None:
            pagina = pagina + 1
        else:
            pagina = "desconhecida"

        parte = (
            f"JOGO: {jogo}\n"
            f"ARQUIVO: {arquivo}\n"
            f"PÁGINA: {pagina}\n"
            f"CONTEÚDO:\n"
            f"{documento.page_content}"
        )

        partes.append(parte)

    return "\n\n---\n\n".join(partes)


# ============================================================
# FONTES
# ============================================================


def coletar_fontes(documentos):
    fontes = []

    for documento in documentos:
        source = documento.metadata.get(
            "source",
            "Fonte desconhecida",
        )

        pagina = documento.metadata.get("page")

        if pagina is not None:
            pagina = pagina + 1
        else:
            pagina = "desconhecida"

        fonte = {
            "source": source,
            "page": pagina,
        }

        if fonte not in fontes:
            fontes.append(fonte)

    return fontes


# ============================================================
# GERAÇÃO DA RESPOSTA
# ============================================================


def gerar_resposta(
    consulta,
    documentos,
):
    contexto = formatar_contexto(documentos)

    llm = criar_llm()

    chain_rag = PROMPT_RAG | llm | StrOutputParser()

    resposta = chain_rag.invoke(
        {
            "contexto": contexto,
            "pergunta": consulta,
        }
    )

    fontes = coletar_fontes(documentos)

    return {
        "resposta": resposta,
        "fontes": fontes,
        "documentos": documentos,
    }


# ============================================================
# VECTORSTORE
#
# Usado para os experimentos:
#
# 500/50
# 1000/100
# ============================================================


def buscar_vectorstore(
    consulta,
    collection_name=COLLECTION_500,
    game=None,
):
    documentos = recuperar_documentos(
        pergunta=consulta,
        collection_name=collection_name,
        search_type="mmr",
        k=5,
        fetch_k=20,
        game=game,
    )

    return gerar_resposta(
        consulta=consulta,
        documentos=documentos,
    )


# ============================================================
# PARENT RETRIEVER
#
# Mantido para comparação com as outras configurações.
# ============================================================


def buscar_parent(
    consulta,
    game=None,
):
    documentos = recuperar_documentos_parent(
        pergunta=consulta,
        game=game,
    )

    return gerar_resposta(
        consulta=consulta,
        documentos=documentos,
    )


# ============================================================
# RAG FINAL
#
# A avaliação com RAGAS apresentou desempenho muito próximo
# entre o Parent Retriever e a configuração 1000/100.
#
# Resultados:
#
# Parent Retriever:
# Faithfulness      = 0.9867
# Answer Relevancy  = 0.7865
# Score geral       = 0.8866
#
# 1000/100:
# Faithfulness      = 0.9818
# Answer Relevancy  = 0.7859
# Score geral       = 0.8838
#
# 500/50:
# Faithfulness      = 0.8000
# Answer Relevancy  = 0.7415
# Score geral       = 0.7708
#
# Apesar de o Parent Retriever apresentar o maior score geral,
# a diferença para 1000/100 foi de apenas 0.0028.
#
# A configuração 1000/100 foi mantida como pipeline final por
# apresentar desempenho praticamente equivalente com uma
# arquitetura mais simples para a aplicação.
# ============================================================

def buscar(
    consulta,
    game=None,
):
    return buscar_vectorstore(
        consulta=consulta,
        collection_name=COLLECTION_1000,
        game=game,
    )


# ============================================================
# EXIBIÇÃO DOS RESULTADOS
# ============================================================


def mostrar_resultado(
    titulo,
    resultado,
):
    print("\n")
    print("=" * 70)
    print(titulo)
    print("=" * 70)

    print("\nRESPOSTA:")
    print(resultado["resposta"])

    print("\nFONTES:")

    for fonte in resultado["fontes"]:
        print(f"- {fonte['source']} " f"- página {fonte['page']}")


# ============================================================
# TESTES
# ============================================================


if __name__ == "__main__":
    pergunta = "Como funciona o combate em " "God of War Ragnarök?"

    game = "god_of_war_ragnarok"

    print("\nPERGUNTA:")
    print(pergunta)

    print(f"\nFiltro de jogo: {game}")

    # ========================================================
    # CONFIGURAÇÃO 500/50
    # ========================================================

    resultado_500 = buscar_vectorstore(
        consulta=pergunta,
        collection_name=COLLECTION_500,
        game=game,
    )

    mostrar_resultado(
        titulo="CONFIGURAÇÃO 500/50",
        resultado=resultado_500,
    )

    # ========================================================
    # CONFIGURAÇÃO 1000/100
    # ========================================================

    resultado_1000 = buscar_vectorstore(
        consulta=pergunta,
        collection_name=COLLECTION_1000,
        game=game,
    )

    mostrar_resultado(
        titulo="CONFIGURAÇÃO 1000/100",
        resultado=resultado_1000,
    )

    # ========================================================
    # PARENT RETRIEVER
    # ========================================================

    resultado_parent = buscar_parent(
        consulta=pergunta,
        game=game,
    )

    mostrar_resultado(
        titulo="CONFIGURAÇÃO PARENT RETRIEVER",
        resultado=resultado_parent,
    )

    # ========================================================
    # CONFIGURAÇÃO FINAL
    #
    # Usa automaticamente a configuração vencedora:
    # 1000/100
    # ========================================================

    resultado_final = buscar(
        consulta=pergunta,
        game=game,
    )

    mostrar_resultado(
        titulo="RAG FINAL - 1000/100",
        resultado=resultado_final,
    )
