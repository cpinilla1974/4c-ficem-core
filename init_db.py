"""
Script para inicializar la base de datos con datos de prueba
"""
from database import init_db, get_engine
from database.repository import EmpresaRepository

def main():
    print("Inicializando base de datos...")

    # Crear base de datos y tablas
    engine = init_db()
    print("✓ Base de datos PostgreSQL conectada y tablas creadas")

    # Crear repositorio
    repo = EmpresaRepository(engine)

    # Verificar si ya hay empresas
    if repo.count() > 0:
        print(f"✓ Base de datos ya contiene {repo.count()} empresas")
        return

    # Insertar empresas de prueba
    print("\nInsertando empresas de prueba...")

    empresas_prueba = [
        {
            "nombre": "Cementos Acme Colombia",
            "pais": "Colombia",
            "perfil_planta": "integrada",
            "contacto": "Juan Pérez",
            "email": "jperez@acme.co"
        },
        {
            "nombre": "Cementos Andinos Perú",
            "pais": "Perú",
            "perfil_planta": "molienda",
            "contacto": "María García",
            "email": "mgarcia@andinos.pe"
        },
        {
            "nombre": "Concretos Premium Chile",
            "pais": "Chile",
            "perfil_planta": "concreto",
            "contacto": "Carlos Rodríguez",
            "email": "crodriguez@premium.cl"
        }
    ]

    for emp_data in empresas_prueba:
        empresa = repo.create(**emp_data)
        print(f"  ✓ {empresa.nombre} ({empresa.pais})")

    print(f"\n✓ Total empresas creadas: {repo.count()}")
    print("✓ Base de datos lista para usar")

if __name__ == "__main__":
    main()
