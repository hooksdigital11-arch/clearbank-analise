# Análise Financeira com Python

Projeto para validar transações de uma fintech e gerar um resumo financeiro mensal a partir de um CSV. O notebook usa a biblioteca padrão do Python e inclui exemplos de registros inválidos e transações que merecem atenção.

## Arquivos

- `desafio-final.ipynb`: notebook completo, organizado por etapas e com as saídas da execução salvas.
- `dados/transacoes.csv`: dados de exemplo usados pelo notebook.
- `relatorio.json`: relatório estruturado gerado pela análise.
- `grafico.png`: visualização opcional de créditos, débitos e saldo por mês.

## Como executar

1. Baixe ou clone este repositório.
2. Abra `desafio-final.ipynb` no Google Colab ou Jupyter Notebook.
3. Mantenha `dados/transacoes.csv` no caminho indicado no notebook.
4. Execute as células em ordem, da primeira à última.

O notebook lê e valida as linhas do CSV, agrupa as transações por mês, calcula totais, médias e extremos, identifica valores acima de R$ 10.000,00, exibe um relatório e salva `relatorio.json`.

## Dados de exemplo

O CSV contém 23 registros: 17 válidos, 6 inválidos, distribuídos em quatro meses. Há duas transações acima do limite de R$ 10.000,00 para demonstrar a sinalização.
