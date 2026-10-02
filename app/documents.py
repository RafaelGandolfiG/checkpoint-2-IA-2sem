# app/documents.py

from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================
# CONFIGURAÇÕES
# ============================================================

DATA_DIR = Path("data")


# ============================================================
# IDENTIFICAR JOGO PELO DIRETÓRIO
# ============================================================


def identificar_jogo(caminho):
    """
    Identifica o jogo a partir da pasta em que o PDF está.

    Exemplo:

    data/horizon_forbidden_west/arquivo.pdf

    retorna:

    horizon_forbidden_west
    """

    try:
        caminho_relativo = caminho.relative_to(DATA_DIR)

        return caminho_relativo.parts[0]

    except (ValueError, IndexError):
        return "desconhecido"


# ============================================================
# CARREGAR DOCUMENTOS
# ============================================================


def carregar_documentos():
    """
    Carrega todos os arquivos PDF existentes dentro
    do diretório data e de seus subdiretórios.

    Cada página carregada recebe metadados adicionais:

    - game
    - file_name
    - source

    O número da página já é fornecido pelo PyMuPDFLoader.
    """

    documentos = []

    arquivos_pdf = list(DATA_DIR.rglob("*.pdf"))

    print(f"PDFs encontrados: {len(arquivos_pdf)}")

    for caminho_pdf in arquivos_pdf:

        print(f"Carregando: {caminho_pdf}")

        jogo = identificar_jogo(caminho_pdf)

        loader = PyMuPDFLoader(str(caminho_pdf))

        paginas = loader.load()

        for pagina in paginas:

            # Ignora páginas completamente vazias.
            if not pagina.page_content.strip():
                continue

            pagina.metadata["game"] = jogo

            pagina.metadata["file_name"] = caminho_pdf.name

            pagina.metadata["source"] = str(caminho_pdf)

            documentos.append(pagina)

    return documentos


# ============================================================
# CRIAR CHUNKS
# ============================================================


def criar_chunks(
    documentos,
    chunk_size=500,
    chunk_overlap=50,
):
    """
    Divide os documentos em chunks utilizando
    RecursiveCharacterTextSplitter.

    Parâmetros:

    documentos:
        lista de documentos carregados.

    chunk_size:
        tamanho máximo aproximado de cada chunk.

    chunk_overlap:
        quantidade de caracteres compartilhados entre
        chunks consecutivos.

    separators:
        define a prioridade utilizada pelo splitter
        para encontrar pontos adequados de divisão.

        A ordem utilizada é:

        1. "\\n\\n" -> parágrafos
        2. "\\n"   -> quebras de linha
        3. ". "    -> final de frases
        4. " "     -> palavras
        5. ""      -> caracteres, como último recurso

    Dessa forma, o splitter tenta preservar primeiro
    estruturas semanticamente maiores antes de realizar
    cortes menores no texto.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = splitter.split_documents(documentos)

    return chunks


# ============================================================
# EXIBIR EXEMPLOS DE CHUNKS
# ============================================================


def mostrar_chunks(
    chunks,
    quantidade=5,
):
    """
    Exibe alguns chunks para facilitar a validação
    do processo de divisão dos documentos.
    """

    print(f"\nTotal de chunks: {len(chunks)}")

    limite = min(
        quantidade,
        len(chunks),
    )

    for i in range(limite):

        chunk = chunks[i]

        print("\n" + "=" * 70)

        print(f"CHUNK {i + 1}")

        print("=" * 70)

        print(chunk.page_content)

        print("\nMETADADOS:")

        print(
            "Jogo:",
            chunk.metadata.get(
                "game",
                "Não informado",
            ),
        )

        print(
            "Arquivo:",
            chunk.metadata.get(
                "file_name",
                "Não informado",
            ),
        )

        pagina = chunk.metadata.get("page")

        if pagina is not None:
            print(f"Página: {pagina + 1}")

        else:
            print("Página: Não informada")

        print(
            "Fonte:",
            chunk.metadata.get(
                "source",
                "Não informada",
            ),
        )


# ============================================================
# TESTE
# ============================================================


if __name__ == "__main__":

    # ========================================================
    # LOAD
    # ========================================================

    documentos = carregar_documentos()

    print(f"\nTotal de documentos/páginas carregados: " f"{len(documentos)}")

    # ========================================================
    # CONFIGURAÇÃO 500/50
    # ========================================================

    chunks_500 = criar_chunks(
        documentos=documentos,
        chunk_size=500,
        chunk_overlap=50,
    )

    print("\n")
    print("=" * 70)
    print("CONFIGURAÇÃO 500/50")
    print("=" * 70)

    mostrar_chunks(
        chunks=chunks_500,
        quantidade=5,
    )

    # ========================================================
    # CONFIGURAÇÃO 1000/100
    # ========================================================

    chunks_1000 = criar_chunks(
        documentos=documentos,
        chunk_size=1000,
        chunk_overlap=100,
    )

    print("\n")
    print("=" * 70)
    print("CONFIGURAÇÃO 1000/100")
    print("=" * 70)

    mostrar_chunks(
        chunks=chunks_1000,
        quantidade=5,
    )
