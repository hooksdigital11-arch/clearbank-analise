"""Gera barras do saldo mensal, conforme a opção A do desafio."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from analise_pandas import gerar_resumo_pandas


def gerar_grafico(caminho_csv: str | Path, caminho_imagem: str | Path) -> Path:
    resumo = gerar_resumo_pandas(caminho_csv)
    destino = Path(caminho_imagem)
    destino.parent.mkdir(parents=True, exist_ok=True)
    meses = list(resumo)
    posicoes = list(range(len(meses)))
    saldos = [resumo[mes]["saldo"] for mes in meses]

    figura, eixo = plt.subplots(figsize=(10, 5))
    eixo.bar(posicoes, saldos, color=["#237a57" if saldo >= 0 else "#b83232" for saldo in saldos])
    eixo.axhline(0, color="#333333", linewidth=0.8)
    eixo.set_title("Saldo financeiro por mês")
    eixo.set_xlabel("Mês")
    eixo.set_ylabel("Valor (R$)")
    eixo.set_xticks(posicoes, meses)
    eixo.grid(axis="y", alpha=0.25)
    figura.tight_layout()
    figura.savefig(destino, dpi=160)
    plt.close(figura)
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default="dados/transacoes.csv", help="CSV de entrada")
    parser.add_argument("--output", default="grafico.png", help="Imagem de saída")
    argumentos = parser.parse_args()
    destino = gerar_grafico(argumentos.csv, argumentos.output)
    print(f"Gráfico salvo em: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
