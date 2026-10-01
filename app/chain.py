# app/chain.py

import os

from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.prompts import (
    SYSTEM_PROMPT_GAMES,
    ANALISE_PROMPT_GAMES,
)

from app.schemas import AnaliseConsulta

# ============================================================
# CARREGAMENTO DAS VARIÁVEIS DE AMBIENTE
# ============================================================

load_dotenv()


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama.com")

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:cloud")


# ============================================================
# VERIFICAÇÃO DA API KEY
# ============================================================

if not OLLAMA_API_KEY:

    raise RuntimeError(
        "OLLAMA_API_KEY não encontrada. "
        "Crie um arquivo .env baseado no .env.example "
        "e adicione sua chave da Ollama Cloud."
    )


# Disponibiliza as configurações para a biblioteca Ollama.
os.environ["OLLAMA_HOST"] = OLLAMA_HOST
os.environ["OLLAMA_API_KEY"] = OLLAMA_API_KEY


# ============================================================
# CRIAÇÃO DO MODELO
# ============================================================


def criar_llm(temperatura=0.7, num_predict=512):
    """
    Cria uma instância do modelo utilizado pelo projeto.

    temperatura:
        controla a criatividade da resposta.

    num_predict:
        define aproximadamente o limite máximo
        de tokens que o modelo pode gerar.
    """

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_HOST,
        temperature=temperatura,
        num_predict=num_predict,
    )

    return llm


# ============================================================
# MODELOS UTILIZADOS PELO CHATBOT
# ============================================================

# Modelo utilizado nas respostas conversacionais.
llm_chat = criar_llm(temperatura=0.7, num_predict=512)


# Modelo com temperatura menor para a análise estruturada.
llm_analise = criar_llm(temperatura=0.2, num_predict=512)


# Mantido para compatibilidade com outros módulos,
# como context_rot.py.
llm = llm_chat


# ============================================================
# PYDANTIC OUTPUT PARSER
# ============================================================

parser_analise = PydanticOutputParser(pydantic_object=AnaliseConsulta)


# ============================================================
# PROMPT DA ANÁLISE
# ============================================================

prompt_analise = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT_GAMES), ("human", ANALISE_PROMPT_GAMES)]
)


# Adiciona automaticamente ao prompt as instruções
# de formato geradas pelo PydanticOutputParser.
prompt_analise = prompt_analise.partial(
    instrucoes_formato=(parser_analise.get_format_instructions())
)


# ============================================================
# PIPELINE LCEL
# ============================================================

chain_analise = prompt_analise | llm_analise | parser_analise


# ============================================================
# FUNÇÃO DE ANÁLISE
# ============================================================


def analisar_consulta(pergunta):
    """
    Analisa a mensagem do usuário e retorna
    um objeto AnaliseConsulta validado pelo Pydantic.
    """

    resultado = chain_analise.invoke({"pergunta": pergunta})

    return resultado


# ============================================================
# TESTE DA CHAIN
# ============================================================


def testar_chain():
    """
    Executa um teste simples da pipeline estruturada.
    """

    pergunta = (
        "Quero um RPG difícil para jogar sozinho no PC. "
        "Você pode me recomendar algum?"
    )

    resultado = analisar_consulta(pergunta)

    print("\n==========================================")

    print("       ANÁLISE ESTRUTURADA")

    print("==========================================\n")

    print(f"Dentro do domínio: " f"{resultado.dentro_dominio}")

    print(f"Assunto: " f"{resultado.assunto}")

    print(f"Tipo de consulta: " f"{resultado.tipo_consulta}")

    print(f"Jogo mencionado: " f"{resultado.jogo_mencionado}")

    print("Precisa de contexto adicional: " f"{resultado.precisa_contexto_adicional}")

    print(f"Resumo: " f"{resultado.resumo}")


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    testar_chain()
