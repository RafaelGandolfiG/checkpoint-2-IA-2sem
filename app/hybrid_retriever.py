from rank_bm25 import BM25Okapi

from app.documents import (
    carregar_documentos,
    criar_chunks,
)

from app.retriever import recuperar_documentos
from app.reranker import reranquear_documentos
from app.vectorstore import COLLECTION_1000

# ============================================================
# QUERY EXPANSION
# ============================================================


def expandir_pergunta(pergunta):
    """
    Expande a consulta com termos relacionados.

    Isso ajuda o BM25 porque ele trabalha principalmente
    com correspondência lexical.

    Exemplo:

    "requisitos para jogar no PC"

    também passa a considerar:

    "especificações", "GPU", "CPU", "RAM", etc.
    """

    pergunta_expandida = pergunta.lower()

    palavras_requisitos = [
        "requisito",
        "requisitos",
        "rodar",
        "jogar",
        "sistema",
        "pc",
    ]

    termos_requisitos = [
        "requisito",
        "requisitos",
        "sistema",
        "especificação",
        "especificações",
        "pc",
        "gpu",
        "cpu",
        "ram",
        "armazenamento",
        "windows",
    ]

    if any(palavra in pergunta_expandida for palavra in palavras_requisitos):
        pergunta_expandida += " " + " ".join(termos_requisitos)

    return pergunta_expandida


# ============================================================
# TOKENIZAÇÃO
# ============================================================


def tokenizar(texto):
    """
    Tokenização simples utilizada pelo BM25.
    """

    texto = (
        texto.lower()
        .replace(":", " ")
        .replace(",", " ")
        .replace(".", " ")
        .replace("?", " ")
        .replace("!", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace("/", " ")
        .replace("\\", " ")
    )

    return texto.split()


# ============================================================
# REMOÇÃO DE DOCUMENTOS DUPLICADOS
# ============================================================


def remover_duplicados(documentos):
    """
    Remove documentos repetidos.

    A identificação é feita principalmente pela fonte,
    página e jogo, evitando manter o mesmo trecho recuperado
    pelo VectorStore e pelo BM25.
    """

    documentos_unicos = []
    vistos = set()

    for documento in documentos:
        source = documento.metadata.get("source")
        pagina = documento.metadata.get("page")
        game = documento.metadata.get("game")

        # Se houver metadados suficientes, utilizamos
        # fonte + página + jogo para identificar duplicatas.
        if source is not None and pagina is not None:
            chave = (
                source,
                pagina,
                game,
            )

        # Fallback caso os metadados estejam incompletos.
        else:
            chave = (
                documento.page_content.strip(),
                game,
            )

        if chave not in vistos:
            vistos.add(chave)
            documentos_unicos.append(documento)

    return documentos_unicos


# ============================================================
# BM25
# ============================================================


def recuperar_bm25(
    pergunta,
    game=None,
    k=15,
):
    """
    Recupera documentos utilizando BM25.

    Etapas:

    1. Carrega os documentos.
    2. Cria chunks 1000/100.
    3. Filtra pelo jogo.
    4. Expande a pergunta.
    5. Executa BM25.
    6. Retorna os melhores documentos.
    """

    documentos = carregar_documentos()

    # ========================================================
    # CHUNKING
    # ========================================================

    chunks = criar_chunks(
        documentos=documentos,
        chunk_size=1000,
        chunk_overlap=100,
    )

    # ========================================================
    # FILTRO PELO JOGO
    # ========================================================

    if game is not None:
        chunks = [
            documento for documento in chunks if documento.metadata.get("game") == game
        ]

    if not chunks:
        return []

    # ========================================================
    # CORPUS BM25
    # ========================================================

    corpus_tokenizado = [tokenizar(documento.page_content) for documento in chunks]

    bm25 = BM25Okapi(corpus_tokenizado)

    # ========================================================
    # QUERY EXPANSION
    # ========================================================

    pergunta_expandida = expandir_pergunta(pergunta)

    print(
        "Consulta BM25 expandida:",
        pergunta_expandida,
    )

    pergunta_tokenizada = tokenizar(pergunta_expandida)

    # ========================================================
    # SCORES
    # ========================================================

    scores = bm25.get_scores(pergunta_tokenizada)

    documentos_com_score = list(
        zip(
            chunks,
            scores,
        )
    )

    documentos_com_score.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    # ========================================================
    # TOP K
    # ========================================================

    documentos_recuperados = []

    for documento, score in documentos_com_score[:k]:
        documento.metadata["bm25_score"] = float(score)

        documentos_recuperados.append(documento)

    return documentos_recuperados


# ============================================================
# HYBRID RETRIEVER
# ============================================================


def recuperar_documentos_hybrid(
    pergunta,
    game=None,
    k_vector=15,
    k_bm25=15,
    k_final=5,
):
    """
    Recuperação híbrida.

    Pipeline:

    Pergunta
        ↓
    Vector Search
        +
    BM25 com Query Expansion
        ↓
    União dos candidatos
        ↓
    Remoção de duplicados
        ↓
    Cross-Encoder Reranker
        ↓
    Top K final
    """

    print("\nRecuperação híbrida iniciada...")

    # ========================================================
    # VECTOR SEARCH
    # ========================================================

    print("Executando busca vetorial...")

    documentos_vector = recuperar_documentos(
        pergunta=pergunta,
        collection_name=COLLECTION_1000,
        search_type="mmr",
        k=k_vector,
        fetch_k=40,
        game=game,
    )

    print(
        "Documentos da busca vetorial:",
        len(documentos_vector),
    )

    # ========================================================
    # BM25
    # ========================================================

    print("Executando BM25...")

    documentos_bm25 = recuperar_bm25(
        pergunta=pergunta,
        game=game,
        k=k_bm25,
    )

    print(
        "Documentos do BM25:",
        len(documentos_bm25),
    )

    # ========================================================
    # COMBINAÇÃO
    # ========================================================

    candidatos = documentos_vector + documentos_bm25

    print(
        "Candidatos antes de remover duplicados:",
        len(candidatos),
    )

    candidatos = remover_duplicados(candidatos)

    print(
        "Candidatos após remover duplicados:",
        len(candidatos),
    )

    # ========================================================
    # RERANKING
    # ========================================================

    print("Executando reranking...")

    documentos_finais = reranquear_documentos(
        pergunta=pergunta,
        documentos=candidatos,
        top_n=k_final,
    )

    print(
        "Documentos finais:",
        len(documentos_finais),
    )

    return documentos_finais


# ============================================================
# EXIBIÇÃO
# ============================================================


def mostrar_documentos(documentos):
    """
    Exibe os documentos finais recuperados.
    """

    print("\n")

    print("=" * 70)

    print("RESULTADO HYBRID RETRIEVER")

    print("=" * 70)

    for i, documento in enumerate(
        documentos,
        start=1,
    ):
        print("\n" + "-" * 70)

        print(f"DOCUMENTO {i}")

        print("-" * 70)

        print(
            "Score reranker:",
            documento.metadata.get(
                "rerank_score",
                "Não informado",
            ),
        )

        print(
            "Score BM25:",
            documento.metadata.get(
                "bm25_score",
                "Não informado",
            ),
        )

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
            print(
                "Página:",
                pagina + 1,
            )

        else:
            print("Página: Não informada")

        print("\nConteúdo:")

        print(documento.page_content[:1000])


# ============================================================
# TESTE
# ============================================================


if __name__ == "__main__":
    pergunta = "Quais são os requisitos para jogar " "Horizon Forbidden West no PC?"

    game = "horizon_forbidden_west"

    print("\nPergunta:")
    print(pergunta)

    print("\nJogo:")
    print(game)

    documentos = recuperar_documentos_hybrid(
        pergunta=pergunta,
        game=game,
        k_vector=15,
        k_bm25=15,
        k_final=5,
    )

    mostrar_documentos(documentos)
