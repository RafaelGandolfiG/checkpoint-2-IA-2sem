from sentence_transformers import CrossEncoder

MODELO_RERANKER = "cross-encoder/ms-marco-MiniLM-L-6-v2"


_reranker = None


def carregar_reranker():
    """
    Carrega o modelo de reranking apenas uma vez.
    """

    global _reranker

    if _reranker is None:
        print("Carregando modelo de reranking...")

        _reranker = CrossEncoder(
            MODELO_RERANKER,
        )

        print("Modelo de reranking carregado.")

    return _reranker


def reranquear_documentos(
    pergunta,
    documentos,
    top_n=5,
):
    """
    Reordena os documentos recuperados de acordo
    com a relevância deles para a pergunta.

    Primeiro o VectorStore recupera vários candidatos.
    Depois o CrossEncoder calcula uma pontuação
    pergunta-documento e mantém os mais relevantes.
    """

    if not documentos:
        return []

    modelo = carregar_reranker()

    pares = []

    for documento in documentos:
        pares.append(
            (
                pergunta,
                documento.page_content,
            )
        )

    scores = modelo.predict(pares)

    documentos_com_score = []

    for documento, score in zip(
        documentos,
        scores,
    ):
        documento.metadata["rerank_score"] = float(score)

        documentos_com_score.append(
            (
                float(score),
                documento,
            )
        )

    documentos_com_score.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    documentos_reranqueados = []

    for score, documento in documentos_com_score[:top_n]:
        documentos_reranqueados.append(documento)

    return documentos_reranqueados


def mostrar_ranking(documentos):
    """
    Exibe o resultado final do reranking.
    """

    print("\n" + "=" * 70)
    print("RESULTADO DO RERANKING")
    print("=" * 70)

    for i, documento in enumerate(
        documentos,
        start=1,
    ):
        score = documento.metadata.get(
            "rerank_score",
            0,
        )

        print(f"\n{i}. Score: {score:.4f}")

        print(
            "Jogo:",
            documento.metadata.get(
                "game",
                "Não informado",
            ),
        )

        print(
            "Arquivo:",
            documento.metadata.get(
                "file_name",
                "Não informado",
            ),
        )

        pagina = documento.metadata.get("page")

        if pagina is not None:
            print(f"Página: {pagina + 1}")

        print(
            "Conteúdo:",
            documento.page_content[:300],
        )


if __name__ == "__main__":
    from app.retriever import recuperar_documentos
    from app.vectorstore import COLLECTION_1000

    pergunta = "Quais são os requisitos para jogar " "Horizon Forbidden West no PC?"

    game = "horizon_forbidden_west"

    print("\nPergunta:")
    print(pergunta)

    print("\nRecuperando candidatos...")

    # Recuperamos mais documentos do que serão
    # enviados para o LLM.
    documentos = recuperar_documentos(
        pergunta=pergunta,
        collection_name=COLLECTION_1000,
        search_type="mmr",
        k=15,
        fetch_k=30,
        game=game,
    )

    print(f"Documentos antes do reranking: " f"{len(documentos)}")

    documentos_reranqueados = reranquear_documentos(
        pergunta=pergunta,
        documentos=documentos,
        top_n=5,
    )

    print(f"Documentos depois do reranking: " f"{len(documentos_reranqueados)}")

    mostrar_ranking(
        documentos_reranqueados,
    )
