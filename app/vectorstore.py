from pathlib import Path

from langchain_chroma import Chroma

from app.documents import carregar_documentos, criar_chunks
from app.embeddings import criar_embeddings

CHROMA_DIR = Path("chroma_db")

COLLECTION_500 = "gameguide"
COLLECTION_1000 = "gameguide_1000"

BATCH_SIZE = 20


def criar_vectorstore(chunks, collection_name):
    embeddings = criar_embeddings()

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    total = len(chunks)

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]

        vectorstore.add_documents(batch)

        inseridos = min(i + BATCH_SIZE, total)

        print(f"{collection_name} - " f"Chunks indexados: {inseridos}/{total}")

    return vectorstore


def carregar_vectorstore(collection_name=COLLECTION_500):
    embeddings = criar_embeddings()

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    return vectorstore


if __name__ == "__main__":
    # LOAD
    documentos = carregar_documentos()

    # ============================================================
    # CONFIGURAÇÃO 1000/100
    # ============================================================

    chunks_1000 = criar_chunks(
        documentos,
        chunk_size=1000,
        chunk_overlap=100,
    )

    print(f"\nTotal de chunks (1000/100): " f"{len(chunks_1000)}")

    # EMBED + STORE
    criar_vectorstore(
        chunks=chunks_1000,
        collection_name=COLLECTION_1000,
    )

    print("\nVector Store 1000/100 criado com sucesso.")
    print(f"Diretório: {CHROMA_DIR}")
    print(f"Collection: {COLLECTION_1000}")
