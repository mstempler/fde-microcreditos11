import csv
import json
from pathlib import Path

from src.motor import ejecutar_motor

CASOS = [
    {
        "caso_id": "MC-0001",
        "dias_mora": 12,
        "importe_vencido": 85000,
        "canales_habilitados": ["whatsapp", "email"],
        "contacto_prohibido": False,
        "observaciones": "Caso sintético de mora temprana.",
    },
    {
        "caso_id": "MC-0002",
        "dias_mora": 28,
        "importe_vencido": 210000,
        "canales_habilitados": ["telefono", "email"],
        "contacto_prohibido": False,
        "observaciones": "No hay políticas de priorización disponibles.",
    },
    {
        "caso_id": "MC-0003",
        "dias_mora": 7,
        "importe_vencido": 35000,
        "canales_habilitados": ["email"],
        "contacto_prohibido": True,
        "observaciones": "Contacto expresamente prohibido.",
    },
    {
        "caso_id": "MC-0004",
        "tipo_consulta": "ambigua",
        "dias_mora": 15,
        "importe_vencido": 92000,
        "canales_habilitados": ["whatsapp", "email"],
        "contacto_prohibido": False,
        "observaciones": (
            "Caso ambiguo: información contradictoria sobre "
            "la disponibilidad de contacto. Requiere aclaración."
        ),
    },
    {
        "caso_id": "MC-0005",
        "tipo_consulta": "fuera_de_tema",
        "dias_mora": 4,
        "importe_vencido": 18000,
        "canales_habilitados": ["email"],
        "contacto_prohibido": False,
        "observaciones": (
            "Consulta fuera de tema: ¿cuál es la capital de Francia? "
            "No corresponde responder preguntas generales."
        ),
    },
]

carpeta = Path("evidencias")
carpeta.mkdir(exist_ok=True)

resultados = []
for numero, caso in enumerate(CASOS, start=1):
    print(f"\nEJECUTANDO CASO {numero}/5: {caso['caso_id']}", flush=True)
    resultado = ejecutar_motor(caso)
    metricas = resultado.get("metricas", {})

    fila = {
        "caso": caso["caso_id"],
        "tipo": (
            "prohibido" if numero == 3
            else "ambiguo" if numero == 4
            else "fuera_de_tema" if numero == 5
            else "normal"
        ),
        "valido": resultado["ok"],
        "tokens_entrada": metricas.get("tokens_entrada", 0),
        "tokens_salida": metricas.get("tokens_salida", 0),
        "costo_usd": metricas.get("costo_usd", 0),
        "latencia_ms": metricas.get("latencia_ms", 0),
        "intentos": resultado.get("intentos"),
    }

    resultados.append(fila)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))

with (carpeta / "mediciones_pe2.csv").open(
    "w", newline="", encoding="utf-8"
) as archivo:
    escritor = csv.DictWriter(archivo, fieldnames=resultados[0].keys())
    escritor.writeheader()
    escritor.writerows(resultados)

with (carpeta / "resultados_pe2.json").open(
    "w", encoding="utf-8"
) as archivo:
    json.dump(resultados, archivo, ensure_ascii=False, indent=2)

print("\nRESUMEN DE MEDICIONES")
for fila in resultados:
    print(fila)

print("\nPROMEDIOS DE LAS CINCO CONSULTAS")
for campo in ("tokens_entrada", "tokens_salida", "costo_usd", "latencia_ms"):
    promedio = sum(fila[campo] for fila in resultados) / len(resultados)
    print(f"{campo}: {promedio:.8f}")
