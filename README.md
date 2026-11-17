# IMAGE MATCHER

Aplicação desktop para localizar imagens semelhantes por pHash, com interface CustomTkinter.

## Recursos

- Pastas separadas para referências e imagens analisadas.
- Comparação com todas as referências (uma imagem de destino pode gerar várias correspondências).
- Pesquisa somente no nível da pasta selecionada; subpastas não são percorridas.
- Tolerância pHash ajustável de 0 a 64.
- Execução em thread separada para manter a interface responsiva.
- Barra de progresso, log, cancelamento e exportação Excel.
- Extensões: JPG, JPEG, PNG, WEBP, BMP, TIF e TIFF.

## Instalação

Recomendado: Python 3.10 ou superior.

No terminal, dentro da pasta do projeto:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Executar

```bash
python main.py
```

## Como funciona a tolerância

O pHash gera uma assinatura de 64 bits. A comparação calcula a distância de Hamming entre duas assinaturas:

- `0`: hashes idênticos.
- Valores baixos: imagens visualmente mais próximas.
- Valores altos: imagens mais diferentes.

O padrão inicial é `8`. Ajuste conforme os resultados reais das suas imagens.

A coluna `Similaridade (%)` é uma conversão simples da distância (`(64 - distância) / 64`), não uma probabilidade nem uma métrica visual calibrada.

## Estrutura

```text
IMAGE_MATCHER/
├── main.py
├── config.py
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── image_hash.py
│   ├── comparator.py
│   └── excel_export.py
└── interface/
    ├── __init__.py
    ├── app.py
    └── logger.py
```
