from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = Path("data")


def descobrir_pdfs(data_dir=DATA_DIR):
    """
    Procura todos os arquivos PDF dentro da pasta data
    e de suas subpastas.
    """
    pdfs = list(data_dir.rglob("*.pdf"))

    return pdfs


def obter_nome_jogo(caminho_pdf):
    """
    Obtém o nome do jogo a partir da pasta onde
    o PDF está armazenado.

    Exemplo:
    data/god_of_war_ragnarok/arquivo.pdf

    Retorna:
    god_of_war_ragnarok
    """
    return caminho_pdf.parent.name


def carregar_documentos(data_dir=DATA_DIR):
    """
    Carrega todos os PDFs encontrados dentro da pasta data.

    Cada página válida é transformada em um Document.

    Páginas sem conteúdo textual são ignoradas.
    """

    pdfs = descobrir_pdfs(data_dir)

    print(f"PDFs encontrados: {len(pdfs)}")

    documentos = []

    for caminho_pdf in pdfs:
        print(f"Carregando: {caminho_pdf}")

        loader = PyPDFLoader(str(caminho_pdf))

        paginas = loader.load()

        jogo = obter_nome_jogo(caminho_pdf)

        for pagina in paginas:
            # Remove espaços antes e depois do conteúdo
            conteudo = pagina.page_content.strip()

            # Ignora páginas completamente vazias
            if not conteudo:
                continue

            # Mantém o conteúdo já limpo
            pagina.page_content = conteudo

            # Adiciona metadados utilizados pelo RAG
            pagina.metadata["game"] = jogo
            pagina.metadata["file_name"] = caminho_pdf.name
            pagina.metadata["source"] = str(caminho_pdf)

            documentos.append(pagina)

    return documentos


def criar_chunks(
    documentos,
    chunk_size=500,
    chunk_overlap=50,
):
    """
    Divide os documentos em chunks.

    Parâmetros:
    documentos:
        Lista de documentos carregados.

    chunk_size:
        Tamanho máximo de cada chunk.

    chunk_overlap:
        Quantidade de caracteres compartilhados
        entre chunks consecutivos.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = splitter.split_documents(documentos)

    return chunks


def mostrar_resumo(documentos):
    """
    Mostra informações básicas dos documentos carregados.
    """

    documentos_vazios = 0

    for documento in documentos:
        if not documento.page_content.strip():
            documentos_vazios += 1

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)

    print(f"Total de documentos válidos: {len(documentos)}")
    print(f"Documentos vazios: {documentos_vazios}")

    if documentos:
        documento = documentos[0]

        print("\n" + "=" * 70)
        print("EXEMPLO DE DOCUMENTO")
        print("=" * 70)

        print("\nCONTEÚDO:")
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


if __name__ == "__main__":
    documentos = carregar_documentos()

    mostrar_resumo(documentos)
