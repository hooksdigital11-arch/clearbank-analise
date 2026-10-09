import tempfile
import unittest
from pathlib import Path

from analise_pandas import gerar_resumo_pandas
from finance_analysis import gerar_relatorio, ler_transacoes
from gerar_grafico import gerar_grafico


ROOT = Path(__file__).resolve().parents[1]


class AnalisePandasTests(unittest.TestCase):
    def test_pandas_repete_metricas_mensais_da_implementacao_nativa(self):
        arquivo_csv = ROOT / "dados" / "transacoes.csv"
        transacoes, _, validas, invalidas = ler_transacoes(arquivo_csv)
        nativo = gerar_relatorio(transacoes, validas, invalidas)["resumo_mensal"]
        pandas = gerar_resumo_pandas(arquivo_csv)

        self.assertEqual(set(pandas), set(nativo))
        for mes, metricas in pandas.items():
            for campo in (
                "quantidade",
                "total_credito",
                "total_debito",
                "saldo",
                "media_por_transacao",
            ):
                self.assertEqual(metricas[campo], nativo[mes][campo], (mes, campo))
            self.assertEqual(metricas["maior_valor"], nativo[mes]["maior_transacao"]["valor"])
            self.assertEqual(metricas["menor_valor"], nativo[mes]["menor_transacao"]["valor"])

    def test_pandas_reporta_arquivo_ausente_com_mensagem_clara(self):
        with tempfile.TemporaryDirectory() as diretorio:
            with self.assertRaisesRegex(FileNotFoundError, "Arquivo não encontrado"):
                gerar_resumo_pandas(Path(diretorio) / "ausente.csv")


class GraficoTests(unittest.TestCase):
    def test_gera_imagem_png_na_localizacao_informada(self):
        with tempfile.TemporaryDirectory() as diretorio:
            destino = Path(diretorio) / "subpasta" / "resumo.png"
            resultado = gerar_grafico(ROOT / "dados" / "transacoes.csv", destino)

            self.assertEqual(resultado, destino)
            self.assertTrue(destino.is_file())
            self.assertGreater(destino.stat().st_size, 1000)
            self.assertEqual(destino.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
