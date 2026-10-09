import json
import os
import shutil
import sys
import tempfile
from types import ModuleType
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NotebookExecutionTests(unittest.TestCase):
    def test_notebook_executa_todas_as_celulas_de_codigo(self):
        notebook = json.loads((ROOT / "desafio-final.ipynb").read_text(encoding="utf-8"))
        cells = notebook.get("cells", [])
        self.assertGreaterEqual(len(cells), 8)

        with tempfile.TemporaryDirectory() as diretorio:
            shutil.copytree(ROOT / "dados", Path(diretorio) / "dados")
            modulo = ModuleType("notebook_test")
            namespace = modulo.__dict__
            sys.modules[modulo.__name__] = modulo
            stdout = StringIO()
            diretorio_atual = Path.cwd()
            os.chdir(diretorio)
            try:
                with redirect_stdout(stdout):
                    for index, cell in enumerate(cells, start=1):
                        if cell.get("cell_type") != "code":
                            continue
                        codigo = "".join(cell.get("source", []))
                        with self.subTest(cell=index):
                            exec(compile(codigo, f"cell_{index}", "exec"), namespace)
            finally:
                os.chdir(diretorio_atual)
                sys.modules.pop(modulo.__name__, None)

            report_path = Path(diretorio) / "relatorio.json"
            self.assertTrue(report_path.is_file())
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(report["total_transacoes_validas"], 17)
        self.assertEqual(report["total_transacoes_invalidas"], 6)
        self.assertEqual(len(report["resumo_mensal"]), 4)
        self.assertEqual(len(report["transacoes_suspeitas"]), 2)
        self.assertIn("Relatório salvo em: relatorio.json", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
