"""Gera um gráfico comparativo de crédito, débito e saldo mensais."""

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
    largura = 0.25
    posicoes = list(range(len(meses)))

    figura, eixo = plt.subplots(figsize=(10, 5))
    eixo.bar([x - largura for x in posicoes], [resumo[m]["total_credito"] for m in meses], largura, label="Créditos")
    eixo.bar(posicoes, [resumo[m]["total_debito"] for m in meses], largura, label="Débitos")
    eixo.bar([x + largura for x in posicoes], [resumo[m]["saldo"] for m in meses], largura, label="Saldo")
    eixo.set_title("Resumo financeiro mensal")
    eixo.set_xlabel("Mês")
    eixo.set_ylabel("Valor (R$)")
    eixo.set_xticks(posicoes, meses)
    eixo.legend()
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
