from pathlib import Path

import pandas as pd

ARQUIVO_RESULTADOS = Path("output/ragas_resultados.csv")


def carregar_resultados():
    if not ARQUIVO_RESULTADOS.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_RESULTADOS}")

    return pd.read_csv(ARQUIVO_RESULTADOS)


def calcular_medias(df):
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

    return medias


def calcular_score_geral(medias):
    medias = medias.copy()

    medias["score_geral"] = (medias["faithfulness"] + medias["answer_relevancy"]) / 2

    medias["score_geral"] = medias["score_geral"].round(4)

    return medias


def mostrar_comparacao_por_pergunta(df):
    print("\n")
    print("=" * 70)
    print("COMPARAÇÃO POR PERGUNTA")
    print("=" * 70)

    for pergunta_id in sorted(df["pergunta_id"].unique()):
        dados = df[df["pergunta_id"] == pergunta_id]

        pergunta = dados.iloc[0]["pergunta"]

        print("\n" + "-" * 70)
        print(f"PERGUNTA {pergunta_id}")
        print("-" * 70)

        print(pergunta)

        print(
            dados[
                [
                    "configuracao",
                    "faithfulness",
                    "answer_relevancy",
                ]
            ].to_string(index=False)
        )


def mostrar_ranking(medias):
    ranking = medias.sort_values(
        by="score_geral",
        ascending=False,
    )

    print("\n")
    print("=" * 70)
    print("RANKING GERAL")
    print("=" * 70)

    print(ranking)

    melhor = ranking.index[0]

    print("\nMelhor configuração:")
    print(melhor)

    return ranking


def analisar_zeros(df):
    zeros = df[df["answer_relevancy"] == 0]

    print("\n")
    print("=" * 70)
    print("ANSWER RELEVANCY IGUAL A ZERO")
    print("=" * 70)

    if zeros.empty:
        print("Nenhum resultado com relevância igual a zero.")
        return

    print(
        zeros[
            [
                "pergunta_id",
                "configuracao",
                "answer_relevancy",
            ]
        ].to_string(index=False)
    )


def salvar_resumo(ranking):
    arquivo = Path("output/resumo_avaliacao.csv")

    ranking.to_csv(
        arquivo,
        encoding="utf-8-sig",
    )

    print(f"\nResumo salvo em: {arquivo}")


def main():
    print("Carregando resultados...")

    df = carregar_resultados()

    print(f"Resultados encontrados: {len(df)}")

    medias = calcular_medias(df)

    medias = calcular_score_geral(medias)

    print("\n")
    print("=" * 70)
    print("MÉDIAS")
    print("=" * 70)

    print(medias)

    mostrar_comparacao_por_pergunta(df)

    analisar_zeros(df)

    ranking = mostrar_ranking(medias)

    salvar_resumo(ranking)


if __name__ == "__main__":
    main()
