import os
import pickle
import shutil

from langchain_chroma import Chroma
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import LocalFileStore
from langchain_classic.storage.encoder_backed import EncoderBackedStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.documents import carregar_documentos
from app.embeddings import criar_embeddings

# ============================================================
# CONFIGURAÇÕES
# ============================================================

PARENT_COLLECTION = "gameguide_parent"

PARENT_DB_DIR = "chroma_parent_db"
PARENT_DOCSTORE_DIR = "parent_docstore"

PARENT_CHUNK_SIZE = 1000
PARENT_CHUNK_OVERLAP = 100

CHILD_CHUNK_SIZE = 200
CHILD_CHUNK_OVERLAP = 20

DOCUMENT_BATCH_SIZE = 10


# ============================================================
# DOCSTORE PERSISTENTE
# ============================================================


def criar_docstore():
    """
    Cria um armazenamento persistente para os documentos-pai.

    O LocalFileStore trabalha com bytes.
    Por isso usamos EncoderBackedStore para converter:
        Document -> bytes
        bytes -> Document
    """

    os.makedirs(
        PARENT_DOCSTORE_DIR,
        exist_ok=True,
    )

    file_store = LocalFileStore(
        PARENT_DOCSTORE_DIR,
    )

    docstore = EncoderBackedStore(
        store=file_store,
        key_encoder=lambda key: key,
        value_serializer=pickle.dumps,
        value_deserializer=pickle.loads,
    )

    return docstore


# ============================================================
# VECTOR STORE
# ============================================================


def criar_vectorstore():
    embeddings = criar_embeddings()

    vectorstore = Chroma(
        collection_name=PARENT_COLLECTION,
        embedding_function=embeddings,
        persist_directory=PARENT_DB_DIR,
    )

    return vectorstore


# ============================================================
# SPLITTERS
# ============================================================


def criar_splitters():
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=PARENT_CHUNK_SIZE,
        chunk_overlap=PARENT_CHUNK_OVERLAP,
    )

    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHILD_CHUNK_SIZE,
        chunk_overlap=CHILD_CHUNK_OVERLAP,
    )

    return parent_splitter, child_splitter


# ============================================================
# CRIAR PARENT DOCUMENT RETRIEVER
# ============================================================


def criar_parent_retriever(documentos):
    print("\nCriando ParentDocumentRetriever...")

    print(f"Parent chunk: {PARENT_CHUNK_SIZE}")
    print(f"Parent overlap: {PARENT_CHUNK_OVERLAP}")

    print(f"Child chunk: {CHILD_CHUNK_SIZE}")
    print(f"Child overlap: {CHILD_CHUNK_OVERLAP}")

    print(f"Document batch: {DOCUMENT_BATCH_SIZE}")

    vectorstore = criar_vectorstore()

    docstore = criar_docstore()

    parent_splitter, child_splitter = criar_splitters()

    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )

    total = len(documentos)

    for inicio in range(
        0,
        total,
        DOCUMENT_BATCH_SIZE,
    ):
        fim = min(
            inicio + DOCUMENT_BATCH_SIZE,
            total,
        )

        lote = documentos[inicio:fim]

        # Segurança extra:
        # ignora documentos vazios caso algum passe pelo loader.
        lote = [documento for documento in lote if documento.page_content.strip()]

        if not lote:
            continue

        retriever.add_documents(lote)

        print("Parent Retriever - " f"Documentos indexados: {fim}/{total}")

    print("\nParent Retriever criado com sucesso.")

    print(f"Vector Store: {PARENT_DB_DIR}")
    print(f"Docstore: {PARENT_DOCSTORE_DIR}")
    print(f"Collection: {PARENT_COLLECTION}")

    return retriever


# ============================================================
# CARREGAR PARENT RETRIEVER EXISTENTE
# ============================================================


def carregar_parent_retriever():
    vectorstore = criar_vectorstore()

    docstore = criar_docstore()

    parent_splitter, child_splitter = criar_splitters()

    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )

    return retriever


# ============================================================
# VERIFICAR SE O BANCO JÁ EXISTE
# ============================================================


def parent_retriever_existe():
    if not os.path.isdir(PARENT_DB_DIR):
        return False

    if not os.path.isdir(PARENT_DOCSTORE_DIR):
        return False

    # Verifica se existem arquivos dentro do docstore.
    try:
        arquivos_docstore = os.listdir(PARENT_DOCSTORE_DIR)
    except OSError:
        return False

    if len(arquivos_docstore) == 0:
        return False

    # Verifica se o Chroma realmente possui documentos.
    try:
        vectorstore = criar_vectorstore()

        quantidade = vectorstore._collection.count()

        if quantidade == 0:
            return False

    except Exception:
        return False

    return True


# ============================================================
# OBTER RETRIEVER
# ============================================================


def obter_parent_retriever():
    if parent_retriever_existe():
        print("\nParent Retriever encontrado.")

        print("Carregando banco existente...")

        retriever = carregar_parent_retriever()

        print("Parent Retriever carregado " "com sucesso.")

        return retriever

    print("\nParent Retriever ainda não existe.")

    print("Criando banco pela primeira vez...")

    documentos = carregar_documentos()

    print(f"\nDocumentos carregados: " f"{len(documentos)}")

    retriever = criar_parent_retriever(documentos)

    return retriever


# ============================================================
# RECUPERAÇÃO
# ============================================================


def recuperar_documentos_parent(
    pergunta,
    game=None,
    k=5,
):
    retriever = obter_parent_retriever()

    search_kwargs = {
        "k": k,
    }

    if game is not None:
        search_kwargs["filter"] = {
            "game": game,
        }

    retriever.search_kwargs = search_kwargs

    documentos = retriever.invoke(pergunta)

    return documentos


# ============================================================
# MOSTRAR DOCUMENTOS
# ============================================================


def mostrar_documentos(documentos):
    print(f"\nDocumentos recuperados: " f"{len(documentos)}")

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


# ============================================================
# TESTE
# ============================================================


def testar_pergunta(
    pergunta,
    game=None,
):
    print("\n\n")

    print("#" * 80)

    print("PERGUNTA")

    print("#" * 80)

    print(pergunta)

    if game is not None:
        print(f"\nFiltro de jogo: {game}")

    documentos = recuperar_documentos_parent(
        pergunta=pergunta,
        game=game,
        k=5,
    )

    mostrar_documentos(documentos)


# ============================================================
# LIMPAR BANCO
# ============================================================


def limpar_parent_retriever():
    """
    Remove o banco vetorial e o docstore.
    Útil caso seja necessário reconstruir tudo.
    """

    if os.path.isdir(PARENT_DB_DIR):
        shutil.rmtree(PARENT_DB_DIR)

        print(f"Removido: " f"{PARENT_DB_DIR}")

    if os.path.isdir(PARENT_DOCSTORE_DIR):
        shutil.rmtree(PARENT_DOCSTORE_DIR)

        print(f"Removido: " f"{PARENT_DOCSTORE_DIR}")


# ============================================================
# MAIN
# ============================================================


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
                "Quais recursos de acessibilidade "
                "existem em Star Wars Jedi: "
                "Fallen Order?"
            ),
            "game": "jedi_fallen_order",
        },
    ]

    for teste in testes:
        testar_pergunta(
            pergunta=teste["pergunta"],
            game=teste["game"],
        )
