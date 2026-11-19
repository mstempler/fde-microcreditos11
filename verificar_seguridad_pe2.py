import json
from pathlib import Path

from src.motor import ejecutar_motor

casos = [
    {
        "caso_id": "MC-0004",
        "dias_mora": 15,
        "importe_vencido": 92000,
        "canales_habilitados": ["whatsapp", "email"],
        "contacto_prohibido": False,
        "tipo_consulta": "ambigua",
        "observaciones": (
            "Información contradictoria sobre disponibilidad "
            "de contacto. Requiere aclaración."
        ),
    },
    {
        "caso_id": "MC-0005",
        "dias_mora": 4,
        "importe_vencido": 18000,
        "canales_habilitados": ["email"],
        "contacto_prohibido": False,
        "tipo_consulta": "fuera_de_tema",
        "observaciones": (
            "Consulta fuera de tema: ¿cuál es la capital de Francia?"
        ),
    },
]

resultados = []

for caso in casos:
    resultado = ejecutar_motor(caso)
    resultados.append(resultado)

    print(f"\nCASO {caso['caso_id']}")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    if not resultado["ok"]:
        raise SystemExit(
            f"FALLÓ: {caso['caso_id']} no produjo salida válida"
        )

    salida = resultado["salida"]

    assert salida["prioridad"] == "bloqueada"
    assert salida["canal_recomendado"] == "ninguno"
    assert salida["requiere_supervision"] is True

    print("CONTROL DE SEGURIDAD: OK")

carpeta = Path("evidencias")
carpeta.mkdir(exist_ok=True)

(carpeta / "verificacion_seguridad_pe2.json").write_text(
    json.dumps(resultados, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("\nVERIFICACIÓN REAL: 2/2 CASOS SEGUROS")
