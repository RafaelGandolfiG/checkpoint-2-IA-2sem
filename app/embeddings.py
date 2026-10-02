import os

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings

load_dotenv()


OLLAMA_LOCAL_HOST = os.getenv(
    "OLLAMA_LOCAL_HOST",
    "http://localhost:11434/",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "nomic-embed-text",
)

EMBEDDING_BATCH_SIZE = 20


class OllamaEmbeddingsBatch:
    def __init__(
        self,
        model,
        base_url,
        batch_size=EMBEDDING_BATCH_SIZE,
    ):
        self.embeddings = OllamaEmbeddings(
            model=model,
            base_url=base_url,
        )

        self.batch_size = batch_size

    def embed_query(self, text):
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts):
        vetores = []

        total = len(texts)

        for inicio in range(
            0,
            total,
            self.batch_size,
        ):
            fim = min(
                inicio + self.batch_size,
                total,
            )

            lote = texts[inicio:fim]

            vetores_lote = self.embeddings.embed_documents(lote)

            vetores.extend(vetores_lote)

        return vetores


def criar_embeddings():
    embeddings = OllamaEmbeddingsBatch(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_LOCAL_HOST,
        batch_size=EMBEDDING_BATCH_SIZE,
    )

    return embeddings


if __name__ == "__main__":
    embeddings = criar_embeddings()

    texto_teste = "Horizon Forbidden West está disponível para PC."

    vetor = embeddings.embed_query(texto_teste)

    print(f"Modelo: {EMBEDDING_MODEL}")

    print(f"Dimensão do vetor: {len(vetor)}")

    print(
        "Primeiros 10 valores:",
        vetor[:10],
    )

    textos = [f"Texto de teste número {i}" for i in range(50)]

    vetores = embeddings.embed_documents(textos)

    print(f"Vetores criados: {len(vetores)}")
