"""Reproduz as métricas mensais usando pandas para comparar com a versão nativa."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


COLUNAS = {"id", "data", "cliente_id", "tipo", "valor", "descricao", "categoria"}


def ler_dados_validos(caminho: str | Path) -> pd.DataFrame:
    """Lê o CSV e remove registros inválidos, mantendo uma linha por ID."""
    arquivo = Path(caminho)
    if not arquivo.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    dados = pd.read_csv(arquivo, dtype=str, encoding="utf-8-sig")
    dados.columns = [coluna.strip().lower() for coluna in dados.columns]
    ausentes = COLUNAS - set(dados.columns)
    if ausentes:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(ausentes))}")

    dados["id_num"] = pd.to_numeric(dados["id"].str.strip(), errors="coerce")
    dados["data_dt"] = pd.to_datetime(dados["data"].str.strip(), format="%Y-%m-%d", errors="coerce")
    dados["valor_num"] = pd.to_numeric(
        dados["valor"].str.strip().str.replace(",", ".", regex=False), errors="coerce"
    )
    dados["tipo_limpo"] = dados["tipo"].str.strip().str.lower()
    dados["cliente_limpo"] = dados["cliente_id"].fillna("").str.strip()
    dados["descricao_limpa"] = dados["descricao"].fillna("").str.strip()

    validas = dados[
        dados["id_num"].notna()
        & (dados["id_num"] % 1 == 0)
        & (dados["cliente_limpo"] != "")
        & dados["data_dt"].notna()
        & dados["tipo_limpo"].isin(["credito", "debito"])
        & dados["valor_num"].notna()
        & (dados["valor_num"] > 0)
        & (dados["descricao_limpa"] != "")
    ].copy()
    validas["id_num"] = validas["id_num"].astype(int)
    validas = validas.drop_duplicates(subset="id_num", keep="first")
    validas["mes"] = validas["data_dt"].dt.strftime("%Y-%m")
    return validas


def gerar_resumo_pandas(caminho: str | Path) -> dict[str, dict]:
    """Retorna contagem, totais, saldo, média, maior e menor por mês."""
    dados = ler_dados_validos(caminho)
    if dados.empty:
        raise ValueError("Não há transações válidas para analisar.")

    resumo: dict[str, dict] = {}
    for mes, grupo in dados.groupby("mes", sort=True):
        valores = grupo["valor_num"]
        credito = round(float(grupo.loc[grupo["tipo_limpo"] == "credito", "valor_num"].sum()), 2)
        debito = round(float(grupo.loc[grupo["tipo_limpo"] == "debito", "valor_num"].sum()), 2)
        resumo[mes] = {
            "quantidade": int(len(grupo)),
            "total_credito": credito,
            "total_debito": debito,
            "saldo": round(credito - debito, 2),
            "media_por_transacao": round(float(valores.mean()), 2),
            "maior_valor": round(float(valores.max()), 2),
            "menor_valor": round(float(valores.min()), 2),
        }
    return resumo


if __name__ == "__main__":
    arquivo_csv = Path(__file__).resolve().parent / "dados" / "transacoes.csv"
    for mes, metricas in gerar_resumo_pandas(arquivo_csv).items():
        print(f"{mes}: {metricas}")
