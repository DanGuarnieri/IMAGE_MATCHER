from pathlib import Path
from config import SUPPORTED_EXTENSIONS
from .image_hash import calcular_hash


def listar_imagens(pasta: Path):
    """Lista somente imagens diretamente dentro da pasta (sem percorrer subpastas)."""
    return sorted(
        (arquivo for arquivo in pasta.iterdir()
         if arquivo.is_file() and arquivo.suffix.lower() in SUPPORTED_EXTENSIONS),
        key=lambda p: p.name.lower()
    )


def comparar_imagens(pasta_referencia, pasta_destino, tolerancia, emitir, cancelar):
    """
    Compara cada imagem de destino com TODAS as referências.
    Retorna uma lista de correspondências e estatísticas.
    """
    pasta_ref = Path(pasta_referencia)
    pasta_img = Path(pasta_destino)

    if not pasta_ref.is_dir():
        raise ValueError("A pasta de referências não existe ou não é válida.")
    if not pasta_img.is_dir():
        raise ValueError("A pasta de imagens não existe ou não é válida.")

    refs = listar_imagens(pasta_ref)
    destinos = listar_imagens(pasta_img)

    if not refs:
        raise ValueError("Nenhuma imagem compatível foi encontrada na pasta de referências.")
    if not destinos:
        raise ValueError("Nenhuma imagem compatível foi encontrada na pasta de destino.")

    emitir("info", f"{len(refs)} imagem(ns) de referência encontrada(s).")
    emitir("info", f"{len(destinos)} imagem(ns) para analisar.")

    hashes_ref = {}
    erros_ref = 0
    for indice, caminho in enumerate(refs, start=1):
        if cancelar.is_set():
            return None
        hash_img = calcular_hash(caminho)
        if hash_img is None:
            erros_ref += 1
            emitir("warning", f"Não foi possível ler a referência: {caminho.name}")
        else:
            hashes_ref[caminho.name] = hash_img
        emitir("progress", (indice, len(refs) + len(destinos),
                            f"Calculando referências: {indice}/{len(refs)}"))

    if not hashes_ref:
        raise ValueError("Nenhuma imagem de referência pôde ser processada.")

    resultados = []
    erros_destino = 0
    processadas = 0
    total = len(refs) + len(destinos)

    for indice, caminho_destino in enumerate(destinos, start=1):
        if cancelar.is_set():
            return None

        hash_destino = calcular_hash(caminho_destino)
        processadas += 1

        if hash_destino is None:
            erros_destino += 1
            emitir("warning", f"Não foi possível ler a imagem: {caminho_destino.name}")
        else:
            for nome_ref, hash_ref in hashes_ref.items():
                distancia = hash_ref - hash_destino
                if distancia <= tolerancia:
                    resultados.append({
                        "Imagem de Referência": nome_ref,
                        "Imagem Analisada": caminho_destino.name,
                        "Distância pHash": int(distancia),
                        "Similaridade (%)": round((64 - distancia) / 64 * 100, 2),
                    })

        emitir("progress", (len(refs) + indice, total,
                            f"Comparando imagens: {indice}/{len(destinos)}"))

    return {
        "resultados": resultados,
        "referencias": len(refs),
        "destinos": len(destinos),
        "processadas": processadas,
        "erros_referencia": erros_ref,
        "erros_destino": erros_destino,
    }
