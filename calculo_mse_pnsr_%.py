# -*- coding: utf-8 -*-
"""
Compara imagens PGM filtradas com a imagem LIMPA (sem ruído, o gabarito).

Calcula, para cada imagem filtrada:
MSE  = média de (pixel_comparado - pixel_limpo)^2 em todos os pixels
       -> quanto MENOR, mais parecida com a original.
PSNR = 10 * log10(maximo^2 / MSE), em dB
       -> quanto MAIOR, mais parecida com a original.
% de ruído removido = dos pixels que estavam com ruído, quantos o filtro
       deixou MAIS PERTO do valor limpo (o erro diminuiu).
% de pixels bons danificados = dos pixels que NÃO tinham ruído, quantos o
       filtro alterou (ficaram diferentes do valor limpo).

Para isso o código usa TRÊS imagens: a limpa, a com ruído e a filtrada.
Um pixel é "ruidoso" quando o valor na imagem com ruído é diferente do
valor na imagem limpa.

Uso: coloque as imagens na mesma pasta deste arquivo, ajuste os nomes
abaixo e execute:  python calcular_mse_psnr.py
"""

import math

# ====== CONFIGURAÇÕES (altere aqui) ======
ARQUIVO_LIMPO = "limpa.pgm"       # imagem original, sem ruído (P2)
ARQUIVO_RUIDOSO = "ruido.pgm"   # imagem com ruído (a que entrou nos filtros)

# Imagens que serão comparadas com a limpa (pode adicionar ou remover)
ARQUIVOS_COMPARAR = [
    "ruido.pgm",     # imagem com ruído (antes de filtrar)
    "saida_media_3x3.pgm",       # filtrada 3x3
    "saida_media_4x4.pgm",   # filtrada 4x4
    "saida_media_5x5.pgm",   # filtrada 5x5
    "saida_media_6x6.pgm",   # filtrada 6x6
]
# =========================================


def ler_pgm(nome):
    """Lê um PGM P2 e devolve (largura, altura, maximo, matriz)."""
    with open(nome, "r") as f:
        # Remove comentários (tudo depois de '#') e junta todos os números
        texto = ""
        for linha in f:
            texto += linha.split("#")[0] + " "
    dados = texto.split()

    if dados[0] != "P2":
        raise ValueError("Este programa só lê PGM no formato P2 (ASCII).")

    largura = int(dados[1])
    altura = int(dados[2])
    maximo = int(dados[3])
    valores = [int(v) for v in dados[4:4 + largura * altura]]

    # Transforma a lista em matriz (lista de linhas)
    matriz = []
    for i in range(altura):
        matriz.append(valores[i * largura:(i + 1) * largura])
    return largura, altura, maximo, matriz


def calcular_mse(limpa, outra, largura, altura):
    """MSE: soma dos (diferença)^2 de cada pixel, dividida pelo nº de pixels."""
    soma = 0
    for y in range(altura):
        for x in range(largura):
            diferenca = outra[y][x] - limpa[y][x]
            soma += diferenca ** 2
    return soma / (largura * altura)


def calcular_psnr(mse, maximo):
    """PSNR em dB. Se o MSE for 0 (imagens idênticas), o PSNR é infinito."""
    if mse == 0:
        return float("inf")
    return 10 * math.log10(maximo ** 2 / mse)


def calcular_ruido_e_danos(limpa, ruidosa, filtrada, largura, altura):
    """
    Devolve (% de ruído removido, % de pixels bons danificados).

    Pixel ruidoso  : ruidosa != limpa
    Pixel bom      : ruidosa == limpa
    Ruído removido : pixel ruidoso cujo erro diminuiu depois do filtro,
                     isto é, |filtrada - limpa| < |ruidosa - limpa|
    Bom danificado : pixel bom que o filtro alterou (filtrada != limpa)
    """
    total_ruidosos = 0
    removidos = 0
    total_bons = 0
    danificados = 0

    for y in range(altura):
        for x in range(largura):
            valor_limpo = limpa[y][x]
            if ruidosa[y][x] != valor_limpo:
                # Pixel com ruído: o erro diminuiu depois do filtro?
                total_ruidosos += 1
                erro_antes = abs(ruidosa[y][x] - valor_limpo)
                erro_depois = abs(filtrada[y][x] - valor_limpo)
                if erro_depois < erro_antes:
                    removidos += 1
            else:
                # Pixel bom: o filtro mexeu nele?
                total_bons += 1
                if filtrada[y][x] != valor_limpo:
                    danificados += 1

    # Se não houver nenhum pixel desse tipo, devolve None (evita dividir por 0)
    pct_removido = removidos / total_ruidosos * 100 if total_ruidosos > 0 else None
    pct_danificado = danificados / total_bons * 100 if total_bons > 0 else None
    return pct_removido, pct_danificado


def formatar(valor, casas=1):
    """Transforma número em texto; None vira '-'."""
    if valor is None:
        return "-"
    return f"{valor:.{casas}f}"


# ---------------- Programa principal ----------------
largura, altura, maximo, limpa = ler_pgm(ARQUIVO_LIMPO)
l_r, a_r, _, ruidosa = ler_pgm(ARQUIVO_RUIDOSO)

if (l_r, a_r) != (largura, altura):
    raise ValueError("A imagem com ruído tem tamanho diferente da imagem limpa.")

print(f"Imagem limpa: {ARQUIVO_LIMPO} ({largura}x{altura}, máximo = {maximo})")
print(f"Imagem com ruído: {ARQUIVO_RUIDOSO}")
print()
print(f"{'Imagem':<18}{'MSE':>10}{'PSNR (dB)':>12}{'Ruído removido':>16}{'Bons danificados':>18}")
print("-" * 74)

for nome in ARQUIVOS_COMPARAR:
    try:
        l2, a2, _, filtrada = ler_pgm(nome)
    except FileNotFoundError:
        print(f"{nome:<18}  arquivo não encontrado")
        continue

    # As imagens precisam ter o mesmo tamanho para comparar pixel a pixel
    if (l2, a2) != (largura, altura):
        print(f"{nome:<18}  tamanho diferente ({l2}x{a2}), ignorada")
        continue

    mse = calcular_mse(limpa, filtrada, largura, altura)
    psnr = calcular_psnr(mse, maximo)
    pct_removido, pct_danificado = calcular_ruido_e_danos(
        limpa, ruidosa, filtrada, largura, altura)

    texto_psnr = "infinito" if psnr == float("inf") else f"{psnr:.2f}"

    print(f"{nome:<18}{mse:>10.2f}{texto_psnr:>12}"
          f"{formatar(pct_removido) + ' %':>16}{formatar(pct_danificado) + ' %':>18}")