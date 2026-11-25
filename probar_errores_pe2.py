import json
import os
from unittest.mock import patch, MagicMock

from src.motor import ejecutar_motor


CASO = {
    "caso_id": "MC-0004",
    "dias_mora": 15,
    "importe_vencido": 92000,
    "canales_habilitados": ["whatsapp", "email"],
    "contacto_prohibido": False,
    "tipo_consulta": "ambigua",
    "observaciones": "Información contradictoria.",
}


def respuesta_simulada(datos):
    r = MagicMock()
    r.output_text = json.dumps(datos)
    r.model = "modelo-simulado"
    r.usage.input_tokens = 100
    r.usage.output_tokens = 40
    return r


@patch.dict(os.environ, {"OPENAI_API_KEY": "clave-simulada-pe2"})
def probar_reintento():
    invalida = {
        "caso_id": "MC-0004",
        "prioridad": "media",
        "canal_recomendado": "email",
        "fundamento": "Se recomienda enviar email para aclarar.",
        "requiere_supervision": False,
        "confianza": 0.7,
    }

    corregida = {
        **invalida,
        "prioridad": "bloqueada",
        "canal_recomendado": "ninguno",
        "requiere_supervision": True,
        "fundamento": (
            "La información es contradictoria. "
            "No se recomienda contactar hasta revisión humana."
        ),
    }

    with patch("src.motor.OpenAI") as cliente:
        cliente.return_value.responses.create.side_effect = [
            respuesta_simulada(invalida),
            respuesta_simulada(corregida),
        ]

        resultado = ejecutar_motor(CASO)

    assert resultado["ok"] is True
    assert resultado["intentos"] == 2
    assert resultado["salida"]["canal_recomendado"] == "ninguno"
    print("PRUEBA REINTENTO: OK")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


@patch.dict(os.environ, {"OPENAI_API_KEY": "clave-simulada-pe2"})
def probar_error_persistente():
    invalida = {
        "caso_id": "MC-0004",
        "prioridad": "media",
        "canal_recomendado": "email",
        "fundamento": "Se recomienda enviar email para aclarar.",
        "requiere_supervision": False,
        "confianza": 1.5,
    }

    with patch("src.motor.OpenAI") as cliente:
        cliente.return_value.responses.create.return_value = (
            respuesta_simulada(invalida)
        )

        resultado = ejecutar_motor(CASO)

    assert resultado["ok"] is False
    assert resultado["error"]["tipo"] == "salida_invalida"
    assert resultado["error"]["intentos"] == 2
    assert any(
        error["campo"] == "confianza"
        for error in resultado["error"]["detalle"]
    )

    print("PRUEBA ERROR PERSISTENTE: OK")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    probar_reintento()
    probar_error_persistente()
