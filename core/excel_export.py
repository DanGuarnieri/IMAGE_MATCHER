from pathlib import Path
import pandas as pd


COLUNAS = [
    "Imagem de Referência",
    "Imagem Analisada",
    "Distância pHash",
    "Similaridade (%)",
]


def salvar_planilha(resultados, caminho_saida):
    """Exporta todas as correspondências para Excel."""
    caminho = Path(caminho_saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(resultados, columns=COLUNAS)
    if not df.empty:
        df = df.sort_values(
            by=["Imagem Analisada", "Distância pHash", "Imagem de Referência"],
            ascending=[True, True, True]
        )
    df.to_excel(caminho, index=False, engine="openpyxl")
    return caminho
