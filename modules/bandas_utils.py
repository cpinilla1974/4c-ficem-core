"""
Utilidades para manejo de Bandas GCCA
Funciones comunes para clasificación de cementos y concretos
"""
import json
import pandas as pd


def cargar_bandas(json_path):
    """Cargar bandas GCCA desde archivo JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        bandas = json.load(f)
    # Asegurar que las claves de resistencia sean enteros
    bandas = {k: {int(r): v for r, v in d.items()} for k, d in bandas.items()}
    return bandas


def calcular_rangos_gcca(CCr):
    """
    Calcula los rangos de clasificación GCCA según la fórmula oficial:
    X_i = (40 + 85 * CCr) * i

    Donde:
    - CCr: Relación Clínker/Cemento (Clinker to Cement ratio)
    - i: Índice de clase (1 para A, 2 para B, etc.)

    Basado en la metodología oficial GCCA para Global Low Carbon Ratings
    """
    rangos = {'AA': 0}  # Near Zero - siempre es 0

    # Calcular X1 a X7 según la fórmula
    base = 40 + 85 * CCr
    for i in range(1, 8):
        if i == 1:
            rangos['A'] = int(base * i)
        elif i == 2:
            rangos['B'] = int(base * i)
        elif i == 3:
            rangos['C'] = int(base * i)
        elif i == 4:
            rangos['D'] = int(base * i)
        elif i == 5:
            rangos['E'] = int(base * i)
        elif i == 6:
            rangos['F'] = int(base * i)
        elif i == 7:
            rangos['G'] = int(base * i)

    return rangos


def clasificar_cemento(gwp, rangos):
    """
    Clasifica un cemento basado en su GWP (kg CO2e/t) utilizando los rangos GCCA

    Args:
        gwp: Valor de huella de carbono en kg CO2e/t
        rangos: Diccionario con los límites para cada clase

    Returns:
        Clase GCCA (AA-G)
    """
    clases = list(rangos.keys())

    # Caso especial para AA (Near Zero)
    if gwp <= rangos['A']:
        return 'AA'

    # Para el resto de clases
    for i in range(1, len(clases)-1):  # Excluimos AA y G
        clase_actual = clases[i]
        clase_siguiente = clases[i+1]

        if rangos[clase_actual] <= gwp < rangos[clase_siguiente]:
            return clase_actual

    # Si es mayor o igual que el límite de F pero menor que G
    if 'G' in rangos and 'F' in rangos:
        if rangos['F'] <= gwp < rangos['G']:
            return 'F'
        elif gwp >= rangos['G']:
            return 'G'
    else:
        # Si no hay clase G, entonces F es la última
        if gwp >= rangos['F']:
            return 'F'

    # Por defecto (no debería llegar aquí)
    return 'F'


def obtener_color_clase(clase):
    """
    Retorna el código de color hexadecimal correspondiente a cada clase GCCA.
    Los colores siguen el esquema oficial del sistema GCCA.
    """
    colores = {
        'AA': '#00A651',  # Verde oscuro
        'A': '#39B54A',   # Verde
        'B': '#8DC63F',   # Verde claro / Cyan
        'C': '#00AEEF',   # Azul claro
        'D': '#0054A6',   # Azul oscuro
        'E': '#A7A9AC',   # Gris claro
        'F': '#6D6E71',   # Gris oscuro
        'G': '#231F20'    # Negro
    }
    return colores.get(clase, '#CCCCCC')


def clasificar_en_bandas(rest, huella, df_bandas):
    """
    Función auxiliar para clasificar valores en bandas según resistencia y huella

    Args:
        rest: Resistencia en MPa
        huella: Huella de CO2 en kg/m³
        df_bandas: DataFrame con bandas GCCA

    Returns:
        Nombre de la banda
    """
    bandas_ordenadas = df_bandas.index.tolist()

    for banda in bandas_ordenadas:
        if rest in df_bandas.columns and huella <= df_bandas.loc[banda, rest]:
            return banda

    return "Top of H"  # Por defecto si no cae en ninguna banda
