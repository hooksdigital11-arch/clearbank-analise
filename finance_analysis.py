"""Leitura, validação e análise de transações financeiras a partir de CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Mapping


LIMITE_SUSPEITO = Decimal("10000.00")
CENTAVOS = Decimal("0.01")
CABECALHOS_OBRIGATORIOS = {
    "id",
    "data",
    "cliente_id",
    "tipo",
    "valor",
    "descricao",
    "categoria",
}


class ErroArquivoTransacoes(ValueError):
    """Erro de leitura ou estrutura do arquivo de transações."""


@dataclass(frozen=True)
class Transacao:
    id: int
    data: datetime
    cliente_id: str
    tipo: str
    valor: Decimal
    descricao: str
    categoria: str
    linha: int


def validar_transacao(registro: Mapping[str, str | None], linha: int) -> Transacao | None:
    """Valida uma linha e retorna a transação limpa, ou None quando inválida."""
    try:
        id_transacao = int((registro.get("id") or "").strip())
    except (ValueError, AttributeError):
        return None

    cliente_id = (registro.get("cliente_id") or "").strip()
    if not cliente_id:
        return None

    texto_data = (registro.get("data") or "").strip()
    try:
        data_transacao = datetime.strptime(texto_data, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None
    if data_transacao.strftime("%Y-%m-%d") != texto_data:
        return None

    tipo = (registro.get("tipo") or "").strip().lower()
    if tipo not in {"credito", "debito"}:
        return None

    texto_valor = (registro.get("valor") or "").strip().replace(",", ".")
    try:
        valor = Decimal(texto_valor)
    except (InvalidOperation, ValueError):
        return None
    if not valor.is_finite() or valor <= 0:
        return None

    descricao = (registro.get("descricao") or "").strip()
    if not descricao:
        return None

    categoria = (registro.get("categoria") or "").strip() or "sem categoria"
    return Transacao(
        id=id_transacao,
        data=data_transacao,
        cliente_id=cliente_id,
        tipo=tipo,
        valor=valor.quantize(CENTAVOS),
        descricao=descricao,
        categoria=categoria,
        linha=linha,
    )


def ler_transacoes(caminho: str | Path) -> tuple[list[Transacao], int, int, int]:
    """Lê o CSV e retorna (válidas, linhas lidas, válidas, inválidas).

    Registros inválidos e IDs duplicados são descartados sem interromper a leitura.
    """
    arquivo = Path(caminho)
    try:
        with arquivo.open("r", encoding="utf-8-sig", newline="") as entrada:
            leitor = csv.DictReader(entrada)
            if not leitor.fieldnames:
                raise ErroArquivoTransacoes("O CSV está vazio ou não possui cabeçalho.")

            nomes = {nome.strip().lower() for nome in leitor.fieldnames if nome}
            ausentes = CABECALHOS_OBRIGATORIOS - nomes
            if ausentes:
                lista = ", ".join(sorted(ausentes))
                raise ErroArquivoTransacoes(f"Colunas obrigatórias ausentes: {lista}.")

            transacoes: list[Transacao] = []
            ids_vistos: set[int] = set()
            total_lido = 0
            total_invalido = 0

            for numero_linha, registro in enumerate(leitor, start=2):
                if not registro:
                    continue
                total_lido += 1
                if None in registro:
                    total_invalido += 1
                    continue

                transacao = validar_transacao(registro, numero_linha)
                if transacao is None or transacao.id in ids_vistos:
                    total_invalido += 1
                    continue

                ids_vistos.add(transacao.id)
                transacoes.append(transacao)

    except FileNotFoundError as exc:
        raise ErroArquivoTransacoes(f"Arquivo não encontrado: {arquivo}") from exc
    except OSError as exc:
        raise ErroArquivoTransacoes(f"Não foi possível ler '{arquivo}': {exc}") from exc
    except csv.Error as exc:
        raise ErroArquivoTransacoes(f"CSV inválido em '{arquivo}': {exc}") from exc

    return transacoes, total_lido, len(transacoes), total_invalido


def _em_reais(valor: Decimal) -> float:
    return float(valor.quantize(CENTAVOS))


def _detalhes_transacao(transacao: Transacao) -> dict:
    return {
        "id": transacao.id,
        "cliente_id": transacao.cliente_id,
        "data": transacao.data.strftime("%Y-%m-%d"),
        "tipo": transacao.tipo,
        "valor": _em_reais(transacao.valor),
        "descricao": transacao.descricao,
        "categoria": transacao.categoria,
    }


def _calcular_metricas(transacoes: list[Transacao]) -> dict:
    creditos = [item.valor for item in transacoes if item.tipo == "credito"]
    debitos = [item.valor for item in transacoes if item.tipo == "debito"]
    total_credito = sum(creditos, Decimal("0"))
    total_debito = sum(debitos, Decimal("0"))
    maior = max(transacoes, key=lambda item: item.valor)
    menor = min(transacoes, key=lambda item: item.valor)
    media = sum((item.valor for item in transacoes), Decimal("0")) / len(transacoes)

    return {
        "quantidade": len(transacoes),
        "total_credito": _em_reais(total_credito),
        "total_debito": _em_reais(total_debito),
        "saldo": _em_reais(total_credito - total_debito),
        "media_por_transacao": _em_reais(media),
        "maior_transacao": _detalhes_transacao(maior),
        "menor_transacao": _detalhes_transacao(menor),
    }


def gerar_relatorio(
    transacoes: Iterable[Transacao],
    total_validas: int,
    total_invalidas: int,
    gerado_em: date | None = None,
) -> dict:
    """Agrupa transações por mês e monta o relatório do desafio."""
    itens = sorted(transacoes, key=lambda item: (item.data, item.id))
    if not itens:
        raise ValueError("Não há transações válidas para analisar.")

    por_mes: dict[str, list[Transacao]] = defaultdict(list)
    for transacao in itens:
        por_mes[transacao.data.strftime("%Y-%m")].append(transacao)

    primeira_data = min(item.data for item in itens)
    ultima_data = max(item.data for item in itens)
    suspeitas = [item for item in itens if item.valor > LIMITE_SUSPEITO]

    return {
        "gerado_em": (gerado_em or date.today()).isoformat(),
        "total_transacoes_lidas": total_validas + total_invalidas,
        "total_transacoes_validas": total_validas,
        "total_transacoes_invalidas": total_invalidas,
        "periodo_analisado": {
            "data_inicial": primeira_data.strftime("%Y-%m-%d"),
            "data_final": ultima_data.strftime("%Y-%m-%d"),
            "dias_entre_transacoes": (ultima_data - primeira_data).days,
        },
        "resumo_geral": _calcular_metricas(itens),
        "resumo_mensal": {
            mes: _calcular_metricas(grupo) for mes, grupo in sorted(por_mes.items())
        },
        "transacoes_suspeitas": [_detalhes_transacao(item) for item in suspeitas],
    }


def _formatar_reais(valor: float) -> str:
    formatado = f"{valor:,.2f}"
    formatado = formatado.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatado}"


def exibir_relatorio(relatorio: Mapping) -> None:
    """Mostra os totais de limpeza e um resumo mensal legível no terminal."""
    periodo = relatorio["periodo_analisado"]
    print("===== LIMPEZA DO CSV =====")
    print(f"Total de linhas lidas: {relatorio['total_transacoes_lidas']}")
    print(f"Linhas válidas: {relatorio['total_transacoes_validas']}")
    print(f"Linhas inválidas: {relatorio['total_transacoes_invalidas']}")
    print(
        "Período analisado: "
        f"{periodo['data_inicial']} → {periodo['data_final']} "
        f"({periodo['dias_entre_transacoes']} dias)"
    )

    print("\n===== RELATÓRIO MENSAL =====")
    for mes, metricas in relatorio["resumo_mensal"].items():
        print(f"Mês: {mes}")
        print(f"  Transações: {metricas['quantidade']}")
        print(f"  Total crédito: {_formatar_reais(metricas['total_credito'])}")
        print(f"  Total débito:  {_formatar_reais(metricas['total_debito'])}")
        print(f"  Saldo:         {_formatar_reais(metricas['saldo'])}")
        print(f"  Média:         {_formatar_reais(metricas['media_por_transacao'])}")
        print(
            "  Maior valor:   "
            f"{_formatar_reais(metricas['maior_transacao']['valor'])} "
            f"(ID {metricas['maior_transacao']['id']})"
        )
        print(
            "  Menor valor:   "
            f"{_formatar_reais(metricas['menor_transacao']['valor'])} "
            f"(ID {metricas['menor_transacao']['id']})"
        )

    print("\n===== TRANSAÇÕES SUSPEITAS =====")
    suspeitas = relatorio["transacoes_suspeitas"]
    if not suspeitas:
        print("Nenhuma transação suspeita encontrada.")
        return
    for transacao in suspeitas:
        print(
            f"ID: {transacao['id']} | Cliente: {transacao['cliente_id']} | "
            f"Data: {transacao['data']} | Valor: {_formatar_reais(transacao['valor'])}"
        )


def salvar_json(relatorio: Mapping, caminho: str | Path = "relatorio.json") -> None:
    """Salva o relatório em JSON UTF-8 com identação legível."""
    destino = Path(caminho)
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ErroArquivoTransacoes(f"Não foi possível salvar '{destino}': {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Valida transações bancárias e gera um resumo financeiro mensal."
    )
    parser.add_argument(
        "csv_file", nargs="?", default="dados/transacoes.csv", help="Arquivo CSV de entrada"
    )
    parser.add_argument(
        "--output", default="relatorio.json", help="Arquivo JSON de saída"
    )
    argumentos = parser.parse_args(argv)

    try:
        transacoes, total_lido, total_validas, total_invalidas = ler_transacoes(
            argumentos.csv_file
        )
        if not transacoes:
            raise ErroArquivoTransacoes("O arquivo não contém transações válidas.")
        relatorio = gerar_relatorio(transacoes, total_validas, total_invalidas)
        exibir_relatorio(relatorio)
        salvar_json(relatorio, argumentos.output)
    except (ErroArquivoTransacoes, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2

    print(f"\nRelatório salvo em: {argumentos.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
