import asyncio
from pathlib import Path

import pandas as pd

from ragas import SingleTurnSample
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from app.rag import (
    buscar_vectorstore,
    buscar_parent,
    criar_llm,
)
from app.embeddings import criar_embeddings
from app.vectorstore import (
    COLLECTION_500,
    COLLECTION_1000,
)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

ARQUIVO_RESULTADOS = OUTPUT_DIR / "ragas_resultados.csv"


PERGUNTAS_AVALIACAO = [
    {
        "pergunta": ("Como funciona o combate em " "God of War Ragnarök?"),
        "game": "god_of_war_ragnarok",
    },
    {
        "pergunta": (
            "Quais são os requisitos para jogar " "God of War Ragnarök no PC?"
        ),
        "game": "god_of_war_ragnarok",
    },
    {
        "pergunta": (
            "Quais recursos de acessibilidade existem em "
            "Star Wars Jedi: Fallen Order?"
        ),
        "game": "jedi_fallen_order",
    },
    {
        "pergunta": (
            "Quais são os requisitos de sistema de " "Red Dead Redemption 2 para PC?"
        ),
        "game": "red_dead_redemption_2",
    },
    {
        "pergunta": ("O que é a expansão Burning Shores de " "Horizon Forbidden West?"),
        "game": "horizon_forbidden_west",
    },
]


CONFIGURACOES = {
    "500/50": COLLECTION_500,
    "1000/100": COLLECTION_1000,
    "Parent Retriever": None,
}


def criar_avaliadores():
    llm = criar_llm()
    embeddings = criar_embeddings()

    evaluator_llm = LangchainLLMWrapper(llm)

    evaluator_embeddings = LangchainEmbeddingsWrapper(embeddings)

    faithfulness = Faithfulness(
        llm=evaluator_llm,
    )

    answer_relevancy = AnswerRelevancy(
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )

    return faithfulness, answer_relevancy


def extrair_contextos(documentos):
    contextos = []

    for documento in documentos:
        contextos.append(documento.page_content)

    return contextos


async def avaliar_resposta(
    pergunta,
    resposta,
    documentos,
    faithfulness,
    answer_relevancy,
):
    contextos = extrair_contextos(documentos)

    sample = SingleTurnSample(
        user_input=pergunta,
        response=resposta,
        retrieved_contexts=contextos,
    )

    nota_faithfulness = await faithfulness.single_turn_ascore(sample)

    nota_answer_relevancy = await answer_relevancy.single_turn_ascore(sample)

    return (
        nota_faithfulness,
        nota_answer_relevancy,
    )


async def executar_avaliacao():
    faithfulness, answer_relevancy = criar_avaliadores()

    resultados = []

    total = len(PERGUNTAS_AVALIACAO) * len(CONFIGURACOES)

    atual = 0

    for numero, teste in enumerate(
        PERGUNTAS_AVALIACAO,
        start=1,
    ):
        pergunta = teste["pergunta"]
        game = teste["game"]

        print("\n" + "=" * 70)
        print(f"PERGUNTA {numero}")
        print("=" * 70)
        print(pergunta)

        print(f"Jogo: {game}")

        for configuracao, collection_name in CONFIGURACOES.items():
            atual += 1

            print(
                f"\n[{atual}/{total}] " f"Avaliando configuração " f"{configuracao}..."
            )

            # ================================================
            # PARENT RETRIEVER
            # ================================================

            if configuracao == "Parent Retriever":
                resultado_rag = buscar_parent(
                    consulta=pergunta,
                    game=game,
                )

                chunk_size = 1000
                chunk_overlap = 0

            # ================================================
            # VECTORSTORES
            # ================================================

            else:
                resultado_rag = buscar_vectorstore(
                    consulta=pergunta,
                    collection_name=collection_name,
                    game=game,
                )

                if configuracao == "500/50":
                    chunk_size = 500
                    chunk_overlap = 50

                else:
                    chunk_size = 1000
                    chunk_overlap = 100

            resposta = resultado_rag["resposta"]
            documentos = resultado_rag["documentos"]

            # ================================================
            # RAGAS
            # ================================================

            (
                nota_faithfulness,
                nota_answer_relevancy,
            ) = await avaliar_resposta(
                pergunta=pergunta,
                resposta=resposta,
                documentos=documentos,
                faithfulness=faithfulness,
                answer_relevancy=answer_relevancy,
            )

            print(f"Faithfulness: " f"{nota_faithfulness:.4f}")

            print(f"Answer Relevancy: " f"{nota_answer_relevancy:.4f}")

            resultados.append(
                {
                    "pergunta_id": numero,
                    "pergunta": pergunta,
                    "game": game,
                    "configuracao": configuracao,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "faithfulness": float(nota_faithfulness),
                    "answer_relevancy": float(nota_answer_relevancy),
                    "resposta": resposta,
                }
            )

    return resultados


def salvar_resultados(resultados):
    df = pd.DataFrame(resultados)

    df.to_csv(
        ARQUIVO_RESULTADOS,
        index=False,
        encoding="utf-8-sig",
    )

    return df


def mostrar_resumo(df):
    print("\n\n" + "=" * 70)
    print("RESULTADOS COMPLETOS")
    print("=" * 70)

    print(
        df[
            [
                "pergunta_id",
                "configuracao",
                "faithfulness",
                "answer_relevancy",
            ]
        ].to_string(index=False)
    )

    medias = (
        df.groupby("configuracao")[
            [
                "faithfulness",
                "answer_relevancy",
            ]
        ]
        .mean()
        .round(4)
    )

    print("\n")
    print("=" * 70)
    print("MÉDIAS POR CONFIGURAÇÃO")
    print("=" * 70)

    print(medias)

    print(f"\nResultados salvos em: " f"{ARQUIVO_RESULTADOS}")


async def main():
    resultados = await executar_avaliacao()

    df = salvar_resultados(resultados)

    mostrar_resumo(df)


if __name__ == "__main__":
    asyncio.run(main())
