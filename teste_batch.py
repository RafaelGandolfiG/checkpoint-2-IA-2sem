from app.documents import carregar_documentos
from app.embeddings import criar_embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

documentos = carregar_documentos()[:10]

parent_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
)

child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
)

parents = parent_splitter.split_documents(documentos)
children = child_splitter.split_documents(parents)

textos = []

for child in children:
    textos.append(child.page_content)

embeddings = criar_embeddings()

vetores = []

batch_size = 20

print(f"\nChildren: {len(textos)}")

for i in range(0, len(textos), batch_size):
    lote = textos[i : i + batch_size]

    vetores_lote = embeddings.embed_documents(lote)

    vetores.extend(vetores_lote)

    print(f"Processados: {len(vetores)}/{len(textos)}")

print(f"\nEmbeddings criados: {len(vetores)}")
print(f"Dimensão: {len(vetores[0])}")
