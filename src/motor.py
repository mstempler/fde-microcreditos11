import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    OpenAI,
    APIConnectionError,
    APIError,
    APITimeoutError,
    APIStatusError,
    OpenAIError,
)
from pydantic import ValidationError

from src.contratos import Entrada, Salida, Canal, Prioridad, TipoConsulta


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
PROMPT = (ROOT / "src" / "prompt_sistema.txt").read_text(
    encoding="utf-8-sig"
)

# USD por millón de tokens. Verificar contra tarifa oficial
# antes de preparar las métricas definitivas.
PRECIO_ENTRADA = 0.40
PRECIO_SALIDA = 1.60


def calcular_costo(entrada_tokens, salida_tokens):
    return round(
        (entrada_tokens * PRECIO_ENTRADA +
         salida_tokens * PRECIO_SALIDA) / 1_000_000,
        8,
    )


def error_estructurado(tipo, detalle, intentos):
    return {
        "ok": False,
        "error": {
            "tipo": tipo,
            "detalle": detalle,
            "intentos": intentos,
        },
    }


def validar_reglas_negocio(entrada: Entrada, salida: Salida):
    errores = []

    if salida.caso_id != entrada.caso_id:
        errores.append({
            "campo": "caso_id",
            "mensaje": "El identificador no coincide con la entrada",
        })

    if (
        entrada.contacto_prohibido
        or entrada.tipo_consulta in (
            TipoConsulta.AMBIGUA,
            TipoConsulta.FUERA_DE_TEMA,
        )
    ):
        if salida.prioridad != Prioridad.BLOQUEADA:
            errores.append({
                "campo": "prioridad",
                "mensaje": "Un caso restringido debe quedar bloqueado",
            })

        if salida.canal_recomendado != Canal.NINGUNO:
            errores.append({
                "campo": "canal_recomendado",
                "mensaje": "No se permite recomendar contacto en este caso",
            })

        if not salida.requiere_supervision:
            errores.append({
                "campo": "requiere_supervision",
                "mensaje": "El caso requiere supervisión",
            })

    elif salida.canal_recomendado not in (
        *entrada.canales_habilitados,
        Canal.NINGUNO,
    ):
        errores.append({
            "campo": "canal_recomendado",
            "mensaje": "El canal no está habilitado",
        })

    if (
        salida.canal_recomendado == Canal.NINGUNO
        and not salida.requiere_supervision
    ):
        errores.append({
            "campo": "requiere_supervision",
            "mensaje": "Sin canal recomendado debe intervenir un humano",
        })


    return errores


def ejecutar_motor(datos: dict):
    inicio = time.perf_counter()

    try:
        entrada = Entrada.model_validate(datos)
    except ValidationError as exc:
        return error_estructurado(
            "entrada_invalida",
            [
                {
                    "campo": ".".join(map(str, e["loc"])),
                    "mensaje": e["msg"],
                }
                for e in exc.errors()
            ],
            0,
        )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return error_estructurado(
            "configuracion_api",
            {"campo": "OPENAI_API_KEY", "mensaje": "Falta configurar la clave de OpenAI"},
            0,
        )

    try:
        client = OpenAI(api_key=api_key, max_retries=0, timeout=30.0)
    except OpenAIError:
        return error_estructurado(
            "configuracion_api",
            {"mensaje": "No se pudo inicializar el cliente de OpenAI"},
            0,
        )

    mensajes = [
        {
            "role": "system",
            "content": PROMPT,
        },
        {
            "role": "user",
            "content": entrada.model_dump_json(),
        },
    ]

    total_entrada = 0
    total_salida = 0
    fallos = []

    for intento in range(1, 3):
        try:
            respuesta = client.responses.create(
                model=MODEL,
                input=mensajes,
                max_output_tokens=500,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "recomendacion_cobranzas",
                        "schema": Salida.model_json_schema(),
                        "strict": False,
                    }
                },
            )

            if respuesta.usage:
                total_entrada += respuesta.usage.input_tokens
                total_salida += respuesta.usage.output_tokens

            texto = respuesta.output_text

            try:
                salida = Salida.model_validate_json(texto)
                errores = validar_reglas_negocio(entrada, salida)

                if errores:
                    fallos = errores
                else:
                    return {
                        "ok": True,
                        "intentos": intento,
                        "salida": salida.model_dump(mode="json"),
                        "metricas": {
                            "modelo": respuesta.model,
                            "tokens_entrada": total_entrada,
                            "tokens_salida": total_salida,
                            "costo_usd": calcular_costo(
                                total_entrada,
                                total_salida,
                            ),
                            "latencia_ms": round(
                                (time.perf_counter() - inicio) * 1000
                            ),
                        },
                    }

            except ValidationError as exc:
                fallos = [
                    {
                        "campo": ".".join(map(str, e["loc"])),
                        "mensaje": (
                            "La respuesta no contiene JSON válido"
                            if e["type"] == "json_invalid"
                            else e["msg"]
                        ),
                    }
                    for e in exc.errors()
                ]

            except ValueError:
                fallos = [{
                    "campo": "respuesta_json",
                    "mensaje": "La respuesta no contiene JSON válido",
                }]

            if intento == 1:
                mensajes.append({
                    "role": "assistant",
                    "content": texto,
                })
                mensajes.append({
                    "role": "user",
                    "content": (
                        "La respuesta anterior fue inválida. "
                        "Corregí estos errores y devolvé únicamente JSON: "
                        + json.dumps(fallos, ensure_ascii=False)
                    ),
                })

        except APITimeoutError:
            return error_estructurado("timeout_api", "APITimeoutError", intento)

        except APIConnectionError:
            return error_estructurado("conexion_api", "APIConnectionError", intento)

        except APIStatusError as exc:
            estado = exc.status_code
            tipo = {
                400: "solicitud_api_invalida",
                401: "autenticacion_api",
                403: "permiso_api",
                429: "limite_api",
            }.get(estado, "servidor_api" if 500 <= estado < 600 else "error_api")
            return error_estructurado(
                tipo,
                {"http": estado, "tipo": type(exc).__name__},
                intento,
            )

        except APIError:
            return error_estructurado(
                "error_api",
                {"mensaje": "El cliente de OpenAI no pudo procesar la respuesta"},
                intento,
            )

    return {
        **error_estructurado(
            "salida_invalida",
            fallos,
            2,
        ),
        "metricas": {
            "modelo": MODEL,
            "tokens_entrada": total_entrada,
            "tokens_salida": total_salida,
            "costo_usd": calcular_costo(
                total_entrada,
                total_salida,
            ),
            "latencia_ms": round(
                (time.perf_counter() - inicio) * 1000
            ),
        },
    }


if __name__ == "__main__":
    caso = {
        "caso_id": "MC-0001",
        "dias_mora": 12,
        "importe_vencido": 85000,
        "canales_habilitados": ["whatsapp", "email"],
        "contacto_prohibido": False,
        "observaciones": (
            "Caso sintético de mora temprana. "
            "No hay políticas de priorización disponibles."
        ),
    }

    resultado = ejecutar_motor(caso)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
