# app/schemas.py

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ============================================================
# SCHEMA DA ANÁLISE DA CONSULTA
# ============================================================


class AnaliseConsulta(BaseModel):
    """
    Schema responsável por validar a análise
    estruturada da mensagem do usuário.
    """

    dentro_dominio: bool = Field(
        description=("Indica se a consulta do usuário pertence " "ao domínio de games.")
    )

    assunto: str = Field(
        min_length=2,
        max_length=120,
        description=("Assunto principal identificado na " "mensagem do usuário."),
    )

    tipo_consulta: Literal[
        "informacao", "recomendacao", "comparacao", "estrategia", "outro"
    ] = Field(
        description=(
            "Tipo principal da consulta. "
            "Deve ser informacao, recomendacao, "
            "comparacao, estrategia ou outro."
        )
    )

    jogo_mencionado: str | None = Field(
        default=None,
        description=(
            "Nome do jogo mencionado explicitamente "
            "pelo usuário. Caso nenhum jogo seja "
            "mencionado, deve ser null."
        ),
    )

    precisa_contexto_adicional: bool = Field(
        description=(
            "Indica se faltam informações importantes "
            "para responder adequadamente à consulta."
        )
    )

    resumo: str = Field(
        min_length=3,
        max_length=300,
        description=("Resumo curto e objetivo da intenção " "principal do usuário."),
    )

    # ========================================================
    # VALIDAÇÃO DO ASSUNTO
    # ========================================================

    @field_validator("assunto")
    @classmethod
    def validar_assunto(cls, valor):

        valor = valor.strip()

        if not valor:

            raise ValueError("O assunto não pode ser vazio.")

        return valor

    # ========================================================
    # VALIDAÇÃO DO JOGO
    # ========================================================

    @field_validator("jogo_mencionado")
    @classmethod
    def validar_jogo_mencionado(cls, valor):

        if valor is None:

            return None

        valor = valor.strip()

        if not valor:

            return None

        return valor

    # ========================================================
    # VALIDAÇÃO DO RESUMO
    # ========================================================

    @field_validator("resumo")
    @classmethod
    def validar_resumo(cls, valor):

        valor = valor.strip()

        if not valor:

            raise ValueError("O resumo não pode ser vazio.")

        return valor
