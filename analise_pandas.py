"""Alternativa com pandas, usando as mesmas regras monetárias da análise nativa."""

from __future__ import annotations

import csv
from io import StringIO
from decimal import Decimal
from pathlib import Path

import pandas as pd

from finance_analysis import CABECALHOS_OBRIGATORIOS, _em_reais, validar_transacao


def ler_dados_validos(caminho: str | Path) -> pd.DataFrame:
    """Lê com pandas e aplica o validador comum antes de agrupar os dados."""
    arquivo = Path(caminho)
    if not arquivo.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    # pandas pode inferir um índice de colunas excedentes ou interromper a leitura.
    # Normalize só a estrutura; as regras de negócio continuam no validador comum.
    csv_normalizado = StringIO()
    with arquivo.open(encoding="utf-8-sig", newline="") as entrada:
        leitor = csv.reader(entrada)
        nomes = [nome.strip().lower() for nome in next(leitor, [])]
        if not nomes:
            raise ValueError("O CSV está vazio ou não possui cabeçalho.")
        if len(nomes) != len(set(nomes)):
            raise ValueError("Cabeçalhos duplicados no CSV.")
        escritor = csv.writer(csv_normalizado)
        escritor.writerow(nomes)
        for campos in leitor:
            if not campos or len(campos) > len(nomes):
                continue
            escritor.writerow(campos + [""] * (len(nomes) - len(campos)))
    csv_normalizado.seek(0)
    dados = pd.read_csv(csv_normalizado, dtype=str, keep_default_na=False)
    dados.columns = [coluna.strip().lower() for coluna in dados.columns]
    ausentes = CABECALHOS_OBRIGATORIOS - set(dados.columns)
    if ausentes:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(ausentes))}")
    if dados.columns.duplicated().any():
        raise ValueError("Cabeçalhos duplicados no CSV.")

    transacoes = [
        transacao
        for linha, registro in enumerate(dados.to_dict("records"), start=2)
        if (transacao := validar_transacao(registro, linha)) is not None
    ]
    validas = pd.DataFrame(
        [{"id": item.id, "mes": item.data.strftime("%Y-%m"),
          "tipo": item.tipo, "valor": item.valor} for item in transacoes],
        columns=["id", "mes", "tipo", "valor"],
    )
    return validas.drop_duplicates(subset="id", keep="first")


def gerar_resumo_pandas(caminho: str | Path) -> dict[str, dict]:
    """Agrupa com groupby e mantém Decimal até a exportação em centavos."""
    dados = ler_dados_validos(caminho)
    if dados.empty:
        raise ValueError("Não há transações válidas para analisar.")

    resumo: dict[str, dict] = {}
    for mes, grupo in dados.groupby("mes", sort=True):
        valores = grupo["valor"]
        credito = sum(grupo.loc[grupo["tipo"] == "credito", "valor"], Decimal("0"))
        debito = sum(grupo.loc[grupo["tipo"] == "debito", "valor"], Decimal("0"))
        resumo[mes] = {
            "quantidade": int(len(grupo)),
            "total_credito": _em_reais(credito),
            "total_debito": _em_reais(debito),
            "saldo": _em_reais(credito - debito),
            "media_por_transacao": _em_reais(sum(valores, Decimal("0")) / len(grupo)),
            "maior_valor": _em_reais(max(valores)),
            "menor_valor": _em_reais(min(valores)),
        }
    return resumo


if __name__ == "__main__":
    arquivo_csv = Path(__file__).resolve().parent / "dados" / "transacoes.csv"
    for mes, metricas in gerar_resumo_pandas(arquivo_csv).items():
        print(f"{mes}: {metricas}")
