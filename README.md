# Análise Financeira com Python

Projeto didático que lê um CSV de transações, descarta registros inválidos sem interromper o processamento e monta um relatório financeiro geral e mensal. O notebook é independente; o mesmo conjunto de regras também pode ser executado pelo terminal e conferido com pandas.

## O que foi implementado

- Validação de cabeçalhos, datas, tipos, valores positivos e IDs únicos.
- Contagem de linhas lidas, válidas e inválidas, com continuação após cada linha incorreta.
- Agrupamento mensal com quantidade, créditos, débitos, saldo, média, maior e menor transação.
- Sinalização de valores **acima de R$ 10.000,00**.
- Exportação de `relatorio.json` e gráfico opcional de créditos, débitos e saldo.

## Arquivos

- `desafio-final.ipynb`: solução completa e executável no Google Colab ou Jupyter.
- `dados/transacoes.csv`: dados de demonstração; 17 linhas válidas e 6 inválidas em quatro meses.
- `finance_analysis.py`: versão de terminal, sem dependências além do Python.
- `analise_pandas.py` e `gerar_grafico.py`: comparação opcional de métricas e gráfico.
- `relatorio.json` e `grafico.png`: exemplos gerados com o CSV incluído.
- `tests/`: testes das regras, do notebook e dos recursos opcionais.

## Executar o notebook

Abra `desafio-final.ipynb` no Google Colab ou Jupyter, mantenha `dados/transacoes.csv` no caminho indicado e execute as células em ordem. O notebook usa somente a biblioteca padrão do Python e grava `relatorio.json` no diretório atual.

## Executar pelo terminal

Requer Python 3.10 ou superior. Na raiz do repositório:

```bash
python3 finance_analysis.py
```

Para usar outro CSV ou salvar o relatório em outro local:

```bash
python3 finance_analysis.py caminho/para/transacoes.csv --output saida/relatorio.json
```

## Extras com pandas e gráfico

Eles não são necessários para o notebook ou para a análise principal:

```bash
python3 -m pip install -r requirements-analysis-optional.txt
python3 analise_pandas.py
python3 gerar_grafico.py
```

## Testes

Os testes principais usam apenas a biblioteca padrão. Os testes de pandas e Matplotlib são executados quando as dependências opcionais estão instaladas; sem elas, a suíte informa que foram ignorados.

```bash
python3 -m unittest discover -s tests -v
```

A suíte também executa as células do notebook em uma pasta temporária e confere as contagens e os totais esperados. O GitHub Actions executa os testes com Python 3.10 e 3.12.
