import csv
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from finance_analysis import (
    ErroArquivoTransacoes,
    Transacao,
    exibir_relatorio,
    gerar_relatorio,
    ler_transacoes,
    salvar_json,
    validar_transacao,
)


ROOT = Path(__file__).resolve().parents[1]
CABECALHO = ["id", "data", "cliente_id", "tipo", "valor", "descricao", "categoria"]


class LeituraEValidacaoTests(unittest.TestCase):
    def escrever_csv(self, diretorio: str, linhas: list[list[str]]) -> Path:
        caminho = Path(diretorio) / "transacoes.csv"
        with caminho.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo)
            escritor.writerow(CABECALHO)
            escritor.writerows(linhas)
        return caminho

    def test_amostra_cumpre_volume_de_dados_do_desafio(self):
        transacoes, lidas, validas, invalidas = ler_transacoes(ROOT / "dados/transacoes.csv")
        meses = {item.data.strftime("%Y-%m") for item in transacoes}
        suspeitas = [item for item in transacoes if item.valor > Decimal("10000.00")]

        self.assertGreaterEqual(validas, 15)
        self.assertGreaterEqual(invalidas, 5)
        self.assertGreaterEqual(len(meses), 3)
        self.assertGreaterEqual(len(suspeitas), 2)
        self.assertEqual(lidas, validas + invalidas)

    def test_descarta_linhas_invalidas_e_id_duplicado_sem_parar(self):
        linhas = [
            ["1", "2026-01-05", "CLI001", "credito", "3500.00", "Salário", "salario"],
            ["x", "2026-01-06", "CLI001", "debito", "10", "Inválida", "compra"],
            ["2", "2026-01-07", "", "debito", "10", "Sem cliente", "compra"],
            ["3", "2026-01-08", "CLI001", "debito", "0", "Valor zero", "compra"],
            ["1", "2026-01-09", "CLI002", "debito", "12", "ID repetido", "compra"],
            ["4", "2026-01-10", "CLI001", "debito", "25,50", "Válida", "compra"],
        ]
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = self.escrever_csv(diretorio, linhas)
            transacoes, lidas, validas, invalidas = ler_transacoes(caminho)

        self.assertEqual((lidas, validas, invalidas), (6, 2, 4))
        self.assertEqual([item.id for item in transacoes], [1, 4])
        self.assertEqual(transacoes[1].valor, Decimal("25.50"))

    def test_arquivo_ausente_tem_mensagem_clara(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "nao-existe.csv"
            with self.assertRaisesRegex(ErroArquivoTransacoes, "Arquivo não encontrado"):
                ler_transacoes(caminho)

    def test_cabecalho_incompleto_e_rejeitado(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "transacoes.csv"
            caminho.write_text("id,data,valor\n1,2026-01-01,10\n", encoding="utf-8")
            with self.assertRaisesRegex(ErroArquivoTransacoes, "Colunas obrigatórias ausentes"):
                ler_transacoes(caminho)

    def test_validar_transacao_aplica_formato_estrito_de_data(self):
        registro = {
            "id": "10",
            "data": "01/02/2026",
            "cliente_id": "CLI001",
            "tipo": "credito",
            "valor": "1.234,56",
            "descricao": "Receita",
            "categoria": "salario",
        }
        self.assertIsNone(validar_transacao(registro, 2))

    def test_csv_de_exemplo_tem_colunas_de_acordo_com_o_enunciado(self):
        with (ROOT / "dados/transacoes.csv").open(encoding="utf-8", newline="") as arquivo:
            leitor = csv.DictReader(arquivo)
            self.assertEqual(leitor.fieldnames, CABECALHO)


class RelatorioTests(unittest.TestCase):
    def setUp(self):
        self.transacoes = [
            Transacao(1, datetime(2026, 1, 5), "CLI001", "credito", Decimal("3500.00"), "Salário", "salario", 2),
            Transacao(2, datetime(2026, 1, 12), "CLI002", "debito", Decimal("180.50"), "Mercado", "compra", 3),
            Transacao(3, datetime(2026, 2, 14), "CLI003", "debito", Decimal("12000.00"), "Alerta", "transferencia", 4),
            Transacao(4, datetime(2026, 2, 20), "CLI001", "credito", Decimal("500.00"), "Reembolso", "outros", 5),
        ]

    def test_calcula_totais_mensais_periodo_e_maior_e_menor(self):
        relatorio = gerar_relatorio(self.transacoes, 4, 2, date(2026, 5, 14))
        janeiro = relatorio["resumo_mensal"]["2026-01"]
        fevereiro = relatorio["resumo_mensal"]["2026-02"]

        self.assertEqual(relatorio["gerado_em"], "2026-05-14")
        self.assertEqual(relatorio["total_transacoes_lidas"], 6)
        self.assertEqual(relatorio["periodo_analisado"]["dias_entre_transacoes"], 46)
        self.assertEqual(janeiro["quantidade"], 2)
        self.assertEqual(janeiro["total_credito"], 3500.0)
        self.assertEqual(janeiro["total_debito"], 180.5)
        self.assertEqual(janeiro["saldo"], 3319.5)
        self.assertEqual(janeiro["media_por_transacao"], 1840.25)
        self.assertEqual(janeiro["maior_transacao"]["id"], 1)
        self.assertEqual(janeiro["menor_transacao"]["id"], 2)
        self.assertEqual(fevereiro["maior_transacao"]["valor"], 12000.0)

    def test_somente_valores_acima_de_dez_mil_sao_sinalizados(self):
        abaixo_do_limite = Transacao(5, datetime(2026, 3, 1), "CLI004", "debito", Decimal("10000.00"), "Limite", "outros", 6)
        acima_do_limite = Transacao(6, datetime(2026, 3, 2), "CLI004", "debito", Decimal("10000.01"), "Suspeita", "outros", 7)
        relatorio = gerar_relatorio(self.transacoes + [abaixo_do_limite, acima_do_limite], 6, 0)

        self.assertEqual([item["id"] for item in relatorio["transacoes_suspeitas"]], [3, 6])

    def test_rejeita_relatorio_sem_transacoes_validas(self):
        with self.assertRaisesRegex(ValueError, "Não há transações válidas"):
            gerar_relatorio([], 0, 5)

    def test_exibe_resumo_formatado_no_terminal(self):
        from contextlib import redirect_stdout
        from io import StringIO

        relatorio = gerar_relatorio(self.transacoes, 4, 2, date(2026, 5, 14))
        saida = StringIO()
        with redirect_stdout(saida):
            exibir_relatorio(relatorio)

        texto = saida.getvalue()
        self.assertIn("===== RELATÓRIO MENSAL =====", texto)
        self.assertIn("Total de linhas lidas: 6", texto)
        self.assertIn("Período analisado: 2026-01-05 → 2026-02-20 (46 dias)", texto)
        self.assertIn("R$ 3.500,00", texto)
        self.assertIn("ID: 3 | Cliente: CLI003", texto)

    def test_salva_json_com_acentos_e_estrutura_mensal(self):
        relatorio = gerar_relatorio(self.transacoes, 4, 2, date(2026, 5, 14))
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "subpasta" / "relatorio.json"
            salvar_json(relatorio, caminho)
            salvo = json.loads(caminho.read_text(encoding="utf-8"))

        self.assertEqual(salvo["gerado_em"], "2026-05-14")
        self.assertIn("2026-01", salvo["resumo_mensal"])
        self.assertEqual(salvo["transacoes_suspeitas"][0]["cliente_id"], "CLI003")

    def test_execucao_cli_gera_json_e_relatorio(self):
        with tempfile.TemporaryDirectory() as diretorio:
            saida_json = Path(diretorio) / "relatorio.json"
            resultado = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "finance_analysis.py"),
                    str(ROOT / "dados/transacoes.csv"),
                    "--output",
                    str(saida_json),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            json_gerado = json.loads(saida_json.read_text(encoding="utf-8"))

        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("===== RELATÓRIO MENSAL =====", resultado.stdout)
        self.assertIn("Linhas inválidas: 6", resultado.stdout)
        self.assertEqual(json_gerado["total_transacoes_validas"], 17)
        self.assertEqual(json_gerado["total_transacoes_invalidas"], 6)


if __name__ == "__main__":
    unittest.main()
