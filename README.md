# Análise Financeira com Python

Solução do desafio prático da Pós em IA e Automação: ler um CSV bancário, validar registros e gerar métricas mensais e alertas. Os dados são **fictícios e didáticos**. A análise principal usa somente a biblioteca padrão do Python; pandas e Matplotlib são extras.

## Abrir e executar

**Mais simples: [abrir o notebook no Google Colab](https://colab.research.google.com/github/hooksdigital11-arch/clearbank-analise/blob/main/desafio-final.ipynb)** e escolher **Ambiente de execução → Executar tudo**. O notebook contém suas funções e a amostra CSV; não depende de clonar scripts nem de baixar dados pela rede. Se `dados/transacoes.csv` já existir, seu conteúdo é preservado. Os extras usam pandas e Matplotlib, normalmente disponíveis no Colab.

No Jupyter local, requer Python 3.10+. Abra `desafio-final.ipynb` e execute em ordem. Para os extras, instale antes:

```bash
python3 -m pip install -r requirements-analysis-optional.txt
```

As saídas executadas estão salvas no notebook: relatório textual, JSON, comparação pandas e gráfico. Os arquivos `relatorio.json` e `grafico.png` também estão na raiz. No Colab, use o painel **Arquivos** para baixar os resultados.

## Executar pelo terminal

```bash
git clone https://github.com/hooksdigital11-arch/clearbank-analise.git
cd clearbank-analise
python3 finance_analysis.py
```

Para outro CSV ou destino:

```bash
python3 finance_analysis.py caminho/transacoes.csv --output saida/relatorio.json
```

Erros de arquivo inexistente, cabeçalhos, codificação e gravação produzem mensagem clara e código de saída 2. Nenhuma credencial é necessária.

## Regras e resultados

| Exigência | Implementação |
|---|---|
| Leitura nativa | `csv.DictReader`, UTF-8/BOM e validação de cabeçalhos |
| Limpeza | ID inteiro único, cliente preenchido, data estrita e válida, tipo crédito/débito e valor positivo finito; descartes silenciosos |
| Amostra | 23 linhas: 17 válidas, 6 inválidas, 4 meses e 2 suspeitas |
| Métricas mensais | Quantidade, créditos, débitos, saldo, média, maior e menor transação |
| Datas | Período, intervalo e dias desde a transação mais antiga e mais recente até a data de execução |
| Suspeitas | Valor original estritamente maior que `LIMITE_SUSPEITO = 10000.00`; sem suspeitas, mensagem exata do enunciado |
| Exportação | `relatorio.json` em UTF-8, com contagens, período, métricas e detalhes das suspeitas |
| Extra pandas | `pd.read_csv` e `groupby`; comparação de todas as métricas mensais com a versão nativa |
| Extra Matplotlib | **Opção A: barras do saldo mensal**, com título e eixos; `grafico.png` e imagem no notebook |

A conversão `float` é validada em `try/except`, como solicitado. O cálculo monetário usa `Decimal`, sem perder precisão antes da soma ou do teste de suspeita. Na apresentação/exportação, valores são arredondados para centavos com meio para par. Datas futuras produzem diferença negativa: não são tratadas como ocorridas no passado. Descrição é texto livre; categoria vazia recebe `sem categoria`. IDs duplicados são descartados depois da primeira ocorrência válida. A alternativa pandas também descarta linhas com colunas excedentes antes de chamar `pd.read_csv`, para evitar inferência de índice ou interrupção por erro de estrutura. Campos textuais entre aspas, incluindo vírgulas e quebras de linha, são preservados.

## Organização

- `desafio-final.ipynb`: entrega principal, autocontida, funções organizadas por etapa e saídas salvas.
- `dados/transacoes.csv`: amostra incluída também no notebook.
- `finance_analysis.py`: análise nativa pelo terminal.
- `analise_pandas.py`: alternativa que compartilha o validador para manter as regras iguais.
- `gerar_grafico.py`: gráfico conforme a opção A.
- `tests/`: regressões, métricas, erros, extras e execução isolada do notebook.

Extras pelo terminal:

```bash
python3 analise_pandas.py
python3 gerar_grafico.py
```

## Testes

```bash
python3 -m unittest discover -s tests -v
```

Sem dependências opcionais, os testes de pandas/Matplotlib são explicitamente ignorados, e o notebook ainda executa a análise principal. Com as dependências, a suíte verifica também os extras. Há cobertura de NaN/Infinity, valores extremos, datas inválidas, duplicatas, limite exato e valores fracionários próximos ao limite, cabeçalhos, CSV ausente, JSON e igualdade entre pandas e Python.

O teste do notebook executa suas células em uma pasta vazia, sem scripts auxiliares ou CSV externo; também confere saídas salvas e igualdade das funções com o módulo. O GitHub Actions valida Python 3.10 e 3.12 com os extras instalados. A revisão de 13/10/2026 executou adicionalmente o notebook completo em kernel Jupyter, com 9 células de código, zero erros e gráfico incorporado.
