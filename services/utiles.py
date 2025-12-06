from unidecode import unidecode
import string




def limpio(texto):
    # Verificar y convertir a cadena si el texto es un número (int o float)
    
    if isinstance(texto, (float, int)):
        texto = str(texto)
    # Convertir a minúsculas
    texto = texto.lower()
    # print(f"limpiar 1: {texto}")
    # Eliminar acentos
    texto = unidecode(texto)
    # print(f"limpiar 2: {texto}")
    # Eliminar signos de puntuación
    texto = texto.translate(str.maketrans('', '', string.punctuation))
    # print(f"limpiar 3: {texto}")
    # Eliminar espacios extra
    texto = ' '.join(texto.split())
    # print(f"limpiar 4: {texto}")
    
    # Eliminar todos los espacios
    texto = texto.replace(' ', '')
    # print(f"limpiar 5: {texto}")
    
    
    return texto


