import tempfile
from unittest.mock import patch
import unittest
from pathlib import Path

from finance_analysis import gerar_relatorio, ler_transacoes
try:
    from analise_pandas import gerar_resumo_pandas
    from gerar_grafico import gerar_grafico
    EXTRAS_DISPONIVEIS = True
except ImportError:
    EXTRAS_DISPONIVEIS = False


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(EXTRAS_DISPONIVEIS, "Dependências opcionais não instaladas")
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


@unittest.skipUnless(EXTRAS_DISPONIVEIS, "Dependências opcionais não instaladas")
class GraficoTests(unittest.TestCase):
    def test_gera_imagem_png_na_localizacao_informada(self):
        with tempfile.TemporaryDirectory() as diretorio:
            destino = Path(diretorio) / "subpasta" / "resumo.png"
            resultado = gerar_grafico(ROOT / "dados" / "transacoes.csv", destino)

            self.assertEqual(resultado, destino)
            self.assertTrue(destino.is_file())
            self.assertGreater(destino.stat().st_size, 1000)
            self.assertEqual(destino.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
    def test_grafico_corresponde_a_opcao_a_saldo_mensal(self):
        import matplotlib.pyplot as plt
        resumo = gerar_resumo_pandas(ROOT / "dados/transacoes.csv")
        figura, eixo = plt.subplots()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("gerar_grafico.plt.subplots", return_value=(figura, eixo)):
                gerar_grafico(ROOT / "dados/transacoes.csv", Path(tmp) / "grafico.png")
        self.assertEqual([barra.get_height() for barra in eixo.patches],
                         [mes["saldo"] for mes in resumo.values()])
        self.assertEqual(eixo.get_xlabel(), "Mês")
        self.assertEqual(eixo.get_ylabel(), "Valor (R$)")
        self.assertIn("Saldo", eixo.get_title())



if __name__ == "__main__":
    unittest.main()
