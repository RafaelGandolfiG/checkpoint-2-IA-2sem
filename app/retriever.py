from app.vectorstore import (
    carregar_vectorstore,
    COLLECTION_500,
    COLLECTION_1000,
)


def criar_retriever(
    collection_name=COLLECTION_500,
    search_type="mmr",
    k=5,
    fetch_k=20,
    game=None,
):
    """
    Cria um retriever a partir do ChromaDB.

    Permite:
    - busca por similaridade;
    - busca MMR;
    - metadata filtering pelo jogo.

    Parâmetros:
    - collection_name: nome da coleção do ChromaDB
    - search_type: "mmr" ou "similarity"
    - k: quantidade final de documentos recuperados
    - fetch_k: quantidade inicial considerada pelo MMR
    - game: filtro opcional de metadata pelo jogo
    """

    vectorstore = carregar_vectorstore(
        collection_name=collection_name,
    )

    search_kwargs = {
        "k": k,
    }

    # ============================================================
    # MMR
    # ============================================================

    if search_type == "mmr":
        search_kwargs["fetch_k"] = fetch_k

    # ============================================================
    # METADATA FILTERING
    #
    # O filtro é enviado ao ChromaDB antes da recuperação.
    # Apenas chunks pertencentes ao jogo informado podem
    # participar da busca.
    # ============================================================

    if game is not None:
        search_kwargs["filter"] = {
            "game": game,
        }

    retriever = vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs,
    )

    return retriever


def recuperar_documentos(
    pergunta,
    collection_name=COLLECTION_500,
    search_type="mmr",
    k=5,
    fetch_k=20,
    game=None,
):
    """
    Recupera os documentos mais relevantes para uma pergunta.

    Quando game é informado, utiliza metadata filtering.
    """

    retriever = criar_retriever(
        collection_name=collection_name,
        search_type=search_type,
        k=k,
        fetch_k=fetch_k,
        game=game,
    )

    documentos = retriever.invoke(pergunta)

    return documentos


def mostrar_documentos(documentos):
    """
    Exibe os documentos recuperados e seus metadados.
    """

    print(f"\nDocumentos recuperados: {len(documentos)}")

    for i, documento in enumerate(
        documentos,
        start=1,
    ):
        print("\n" + "=" * 70)
        print(f"DOCUMENTO {i}")
        print("=" * 70)

        print(documento.page_content)

        print("\nMETADADOS:")

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
        else:
            print("Página: Não informada")

        print(
            "Fonte:",
            documento.metadata.get(
                "source",
                "Não informada",
            ),
        )


def testar_metadata_filtering(
    pergunta,
    game,
):
    """
    Testa explicitamente o metadata filtering.

    O resultado deve conter apenas documentos
    cujo metadata 'game' seja igual ao jogo informado.
    """

    print("\n\n")
    print("#" * 80)
    print("TESTE DE METADATA FILTERING")
    print("#" * 80)

    print(f"\nPergunta: {pergunta}")
    print(f"Filtro aplicado: game = {game}")

    documentos = recuperar_documentos(
        pergunta=pergunta,
        collection_name=COLLECTION_500,
        search_type="mmr",
        k=5,
        fetch_k=20,
        game=game,
    )

    mostrar_documentos(documentos)

    print("\n" + "-" * 70)
    print("VALIDAÇÃO DO FILTRO")
    print("-" * 70)

    filtro_correto = True

    for documento in documentos:
        jogo_documento = documento.metadata.get("game")

        if jogo_documento != game:
            filtro_correto = False

            print(
                "ERRO:",
                jogo_documento,
                "!=",
                game,
            )

    if filtro_correto:
        print("OK - Todos os documentos recuperados " "pertencem ao jogo filtrado.")
    else:
        print("ERRO - Foram recuperados documentos " "fora do filtro informado.")


def testar_pergunta(
    pergunta,
    game,
):
    print("\n\n")
    print("#" * 80)
    print("PERGUNTA")
    print("#" * 80)

    print(pergunta)

    print(f"\nFiltro de jogo: {game}")

    # ============================================================
    # CONFIGURAÇÃO 500/50
    # ============================================================

    print("\n")
    print("=" * 70)
    print("CONFIGURAÇÃO 500/50")
    print("=" * 70)

    documentos_500 = recuperar_documentos(
        pergunta=pergunta,
        collection_name=COLLECTION_500,
        search_type="mmr",
        k=5,
        fetch_k=20,
        game=game,
    )

    mostrar_documentos(documentos_500)

    # ============================================================
    # CONFIGURAÇÃO 1000/100
    # ============================================================

    print("\n")
    print("=" * 70)
    print("CONFIGURAÇÃO 1000/100")
    print("=" * 70)

    documentos_1000 = recuperar_documentos(
        pergunta=pergunta,
        collection_name=COLLECTION_1000,
        search_type="mmr",
        k=5,
        fetch_k=20,
        game=game,
    )

    mostrar_documentos(documentos_1000)


if __name__ == "__main__":
    testes = [
        {
            "pergunta": (
                "Quais são os requisitos para jogar " "Horizon Forbidden West no PC?"
            ),
            "game": "horizon_forbidden_west",
        },
        {
            "pergunta": (
                "Quais recursos de acessibilidade existem em "
                "Star Wars Jedi: Fallen Order?"
            ),
            "game": "jedi_fallen_order",
        },
    ]

    for teste in testes:
        testar_pergunta(
            pergunta=teste["pergunta"],
            game=teste["game"],
        )

    # ============================================================
    # TESTE EXPLÍCITO DO DIFERENCIAL DE METADATA FILTERING
    # ============================================================

    testar_metadata_filtering(
        pergunta=(
            "Quais são os requisitos de sistema de " "Red Dead Redemption 2 para PC?"
        ),
        game="red_dead_redemption_2",
    )
    