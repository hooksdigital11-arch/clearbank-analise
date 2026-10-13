"""Casos de borda encontrados ao conferir o enunciado e as duas implementações."""
import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal
from pathlib import Path

from finance_analysis import (
    ErroArquivoTransacoes, exibir_relatorio, gerar_relatorio,
    ler_transacoes, validar_transacao,
)

HEADER = ["id", "data", "cliente_id", "tipo", "valor", "descricao", "categoria"]


def registro(**campos):
    base = dict(zip(HEADER, ["1", "2026-01-05", "CLI1", "credito", "10", "", ""] ))
    return base | campos


class AuditRegressions(unittest.TestCase):
    def test_descricao_livre_vazia_nao_invalida_campos_obrigatorios(self):
        self.assertIsNotNone(validar_transacao(registro(), 2))

    def test_ids_fracionarios_e_separadores_nao_sao_inteiros_csv(self):
        for value in ["1.0", "1e2", "1_000", ""]:
            self.assertIsNone(validar_transacao(registro(id=value), 2))

    def test_nan_inf_zero_negativo_e_extremo_sao_descartados(self):
        for value in ["NaN", "Infinity", "-Infinity", "0", "-1", "1e100", "abc"]:
            with self.subTest(value=value):
                self.assertIsNone(validar_transacao(registro(valor=value), 2))

    def test_data_estrita_e_calendario(self):
        for value in ["2026-1-5", "2026-02-30", "2026-02-29", "05/01/2026"]:
            self.assertIsNone(validar_transacao(registro(data=value), 2))
        self.assertIsNotNone(validar_transacao(registro(data="2024-02-29"), 2))

    def test_suspeita_avaliada_antes_de_arredondar_centavos(self):
        item = validar_transacao(registro(valor="10000.004"), 2)
        self.assertEqual(item.valor, Decimal("10000.004"))
        report = gerar_relatorio([item], 1, 0, date(2026, 1, 10))
        self.assertEqual(len(report["transacoes_suspeitas"]), 1)
        self.assertEqual(report["periodo_analisado"]["dias_desde_mais_antiga"], 5)
        self.assertEqual(report["periodo_analisado"]["dias_desde_mais_recente"], 5)

    def test_sem_suspeitas_tem_mensagem_exata(self):
        item = validar_transacao(registro(valor="10000.00"), 2)
        output = io.StringIO()
        with redirect_stdout(output):
            exibir_relatorio(gerar_relatorio([item], 1, 0))
        self.assertIn("Nenhuma transação suspeita encontrada.", output.getvalue())

    def test_cabecalho_normalizado_e_descartes_silenciosos(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "dados.csv"
            with p.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([f" {name.upper()} " for name in HEADER])
                writer.writerow(list(registro().values()))
                writer.writerow(list(registro(id="2", valor="erro").values()))
            output = io.StringIO()
            with redirect_stdout(output):
                _, read, valid, invalid = ler_transacoes(p)
            self.assertEqual((read, valid, invalid), (2, 1, 1))
            self.assertEqual(output.getvalue(), "")

    def test_cabecalho_duplicado_e_arquivo_nao_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "dados.csv"
            p.write_text(",".join(HEADER + ["id"]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ErroArquivoTransacoes, "duplicados"):
                ler_transacoes(p)
            p.write_bytes(b"id,data,cliente_id,tipo,valor,descricao,categoria\n1,2026-01-01,X,credito,1,\xff,X\n")
            with self.assertRaisesRegex(ErroArquivoTransacoes, "UTF-8"):
                ler_transacoes(p)

    def test_pandas_e_nativo_concordam_em_dados_adversos(self):
        try:
            from analise_pandas import gerar_resumo_pandas
        except ImportError:
            self.skipTest("pandas opcional não instalado")
        rows = [registro(id=str(i + 1), valor=value) for i, value in enumerate(
            ["0.005", "0.015", "10000.004", "1e100", "NaN", "Infinity", "0", "-1"])]
        rows += [registro(id="20", data="2026-1-5"), registro(id="1.0"), registro(id="1")]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "dados.csv"
            with p.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=HEADER)
                writer.writeheader(); writer.writerows(rows)
            items, _, valid, invalid = ler_transacoes(p)
            native = gerar_relatorio(items, valid, invalid)["resumo_mensal"]
            alternative = gerar_resumo_pandas(p)
            for month, metrics in alternative.items():
                for name in ["quantidade", "total_credito", "total_debito", "saldo", "media_por_transacao"]:
                    self.assertEqual(metrics[name], native[month][name], name)
