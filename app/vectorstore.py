# app/vectorstore.py

from pathlib import Path

from langchain_chroma import Chroma

from app.documents import carregar_documentos, criar_chunks
from app.embeddings import criar_embeddings

# ============================================================
# CONFIGURAÇÕES
# ============================================================

CHROMA_DIR = Path("chroma_db")

COLLECTION_500 = "gameguide"
COLLECTION_1000 = "gameguide_1000"

BATCH_SIZE = 20


# ============================================================
# APAGAR COLLECTION
# ============================================================


def apagar_collection(collection_name):
    """
    Apaga uma collection existente do Chroma.

    Isso evita que chunks antigos permaneçam no banco
    quando a indexação for executada novamente.
    """

    embeddings = criar_embeddings()

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    try:
        vectorstore.delete_collection()

        print(f"Collection '{collection_name}' " f"apagada com sucesso.")

    except Exception:
        print(
            f"Collection '{collection_name}' " f"não existia ou não pôde ser apagada."
        )


# ============================================================
# CRIAR VECTORSTORE
# ============================================================


def criar_vectorstore(
    chunks,
    collection_name,
    recriar=False,
):
    """
    Cria uma collection no Chroma e adiciona
    os chunks em lotes.

    Se recriar=True, a collection existente é apagada
    antes da nova indexação.
    """

    if recriar:
        apagar_collection(collection_name)

    embeddings = criar_embeddings()

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    total = len(chunks)

    for i in range(
        0,
        total,
        BATCH_SIZE,
    ):
        batch = chunks[i : i + BATCH_SIZE]

        vectorstore.add_documents(batch)

        inseridos = min(
            i + BATCH_SIZE,
            total,
        )

        print(f"{collection_name} - " f"Chunks indexados: " f"{inseridos}/{total}")

    return vectorstore


# ============================================================
# CARREGAR VECTORSTORE
# ============================================================


def carregar_vectorstore(
    collection_name=COLLECTION_500,
):
    """
    Carrega uma collection existente do Chroma.
    """

    embeddings = criar_embeddings()

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    return vectorstore


# ============================================================
# EXECUÇÃO
# ============================================================


if __name__ == "__main__":

    # ========================================================
    # LOAD
    # ========================================================

    documentos = carregar_documentos()

    print(f"\nTotal de documentos/páginas: " f"{len(documentos)}")

    # ========================================================
    # CONFIGURAÇÃO 500/50
    # ========================================================

    print("\n")
    print("=" * 70)
    print("CONFIGURAÇÃO 500/50")
    print("=" * 70)

    chunks_500 = criar_chunks(
        documentos=documentos,
        chunk_size=500,
        chunk_overlap=50,
    )

    print(f"\nTotal de chunks (500/50): " f"{len(chunks_500)}")

    criar_vectorstore(
        chunks=chunks_500,
        collection_name=COLLECTION_500,
        recriar=True,
    )

    print("\nVector Store 500/50 " "criado com sucesso.")

    print(f"Collection: " f"{COLLECTION_500}")

    # ========================================================
    # CONFIGURAÇÃO 1000/100
    # ========================================================

    print("\n")
    print("=" * 70)
    print("CONFIGURAÇÃO 1000/100")
    print("=" * 70)

    chunks_1000 = criar_chunks(
        documentos=documentos,
        chunk_size=1000,
        chunk_overlap=100,
    )

    print(f"\nTotal de chunks (1000/100): " f"{len(chunks_1000)}")

    criar_vectorstore(
        chunks=chunks_1000,
        collection_name=COLLECTION_1000,
        recriar=True,
    )

    print("\nVector Store 1000/100 " "criado com sucesso.")

    print(f"Collection: " f"{COLLECTION_1000}")

    # ========================================================
    # FINALIZAÇÃO
    # ========================================================

    print("\n")
    print("=" * 70)
    print("VECTOR STORES CRIADOS COM SUCESSO")
    print("=" * 70)

    print(f"Diretório: {CHROMA_DIR}")

    print(f"500/50  -> " f"{COLLECTION_500}")

    print(f"1000/100 -> " f"{COLLECTION_1000}")
