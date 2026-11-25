import argparse
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

def medir(carpeta: Path):
    resultados = []
    for numero, caso in enumerate(CASOS, start=1):
        print(f"\nEJECUTANDO CASO {numero}/{len(CASOS)}: {caso['caso_id']}", flush=True)
        resultado = ejecutar_motor(caso)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))

        if not resultado["ok"]:
            raise SystemExit(
                f"Medición incompleta en {caso['caso_id']}: "
                f"{resultado['error']['tipo']}"
            )

        metricas = resultado["metricas"]
        if not metricas["tokens_entrada"] or not metricas["tokens_salida"]:
            raise SystemExit(f"Medición incompleta en {caso['caso_id']}: faltan tokens de usage")

        tipo = "prohibido" if caso["contacto_prohibido"] else caso.get("tipo_consulta", "normal")
        if tipo == "ambigua":
            tipo = "ambiguo"

        resultados.append({
            "caso": caso["caso_id"],
            "tipo": tipo,
            "valido": True,
            "tokens_entrada": metricas["tokens_entrada"],
            "tokens_salida": metricas["tokens_salida"],
            "costo_usd": metricas["costo_usd"],
            "latencia_ms": metricas["latencia_ms"],
            "intentos": resultado["intentos"],
        })

    carpeta.mkdir(parents=True, exist_ok=True)

    with (carpeta / "mediciones_pe2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=resultados[0].keys())
        escritor.writeheader()
        escritor.writerows(resultados)

    with (carpeta / "resultados_pe2.json").open("w", encoding="utf-8") as archivo:
        json.dump(resultados, archivo, ensure_ascii=False, indent=2)

    print("\nPROMEDIOS DE LAS CINCO CONSULTAS")
    for campo in ("tokens_entrada", "tokens_salida", "costo_usd", "latencia_ms"):
        promedio = sum(fila[campo] for fila in resultados) / len(resultados)
        print(f"{campo}: {promedio:.8f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mide cinco consultas reales de PE2")
    parser.add_argument("--salida", type=Path, default=Path("evidencias"))
    medir(parser.parse_args().salida)
