# MicroCreditos11 SA — FDE Pre-Entrega 2

Motor de recomendaciones de próxima acción para cobranzas
tempranas, desarrollado como ejercicio académico con datos
exclusivamente sintéticos.

## Objetivo

Implementar la historia HU-01 de PE1: recomendar prioridad,
canal y fundamento para ayudar al gestor de cobranzas.

El sistema NO envía mensajes, ejecuta llamadas, modifica
cuentas ni autoriza acuerdos.

## Tecnologías

- Python
- OpenAI Responses API (`gpt-4.1-mini`)
- Pydantic v2
- python-dotenv

## Instalación desde un clon limpio

```powershell
git clone https://github.com/mstempler/fde-microcreditos11.git
cd fde-microcreditos11
git switch pe2/hito1-manejo-errores-openai
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Editar `.env` localmente y configurar `OPENAI_API_KEY`.
Nunca publicar la clave.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m src.motor
```

## Pruebas

Suite de regresión con cliente simulado y sin credenciales reales.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Evidencia de terminal para el reintento y el error persistente.

```powershell
.\.venv\Scripts\python.exe probar_errores_pe2.py
```

Cinco consultas reales con mediciones en una carpeta nueva.

```powershell
.\.venv\Scripts\python.exe medir_pe2.py --salida evidencias/corrida-nueva
```

Verificación real de dos casos restringidos:

```powershell
.\.venv\Scripts\python.exe verificar_seguridad_pe2.py
```

Las pruebas que llaman a OpenAI requieren una clave válida
y generan consumo facturable.

## Contratos y seguridad

`Entrada` valida identificador, mora de 1 a 30 días,
importe positivo, canales no vacíos y sin duplicados.

`Salida` valida prioridad, canal, fundamento, supervisión
y confianza entre 0 y 1.

El motor comprueba además la coincidencia del caso,
los canales permitidos y los bloqueos por contacto
prohibido o tipo de consulta restringido.

Las respuestas inválidas reciben un único reintento.
Si persiste el error, se devuelve un objeto estructurado.

Si falta `OPENAI_API_KEY`, el motor devuelve `configuracion_api` con cero intentos.
Los fallos de OpenAI devuelven tipos estructurados y detalles controlados, con el estado HTTP cuando corresponde.

## Evidencia

La tanda del 25 de noviembre de 2026 usó el commit `3642a03`
y el modelo `gpt-4.1-mini-2025-04-14`. Las cinco respuestas fueron válidas
en el primer intento. Los tres casos restringidos quedaron bloqueados,
sin canal y con supervisión humana.

| Caso | Tipo | Tokens entrada | Tokens salida | Costo estimado (USD) | Latencia (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| MC-0001 | Normal | 447 | 117 | 0,00036600 | 3.052 |
| MC-0002 | Normal | 446 | 132 | 0,00038960 | 2.146 |
| MC-0003 | Contacto prohibido | 442 | 83 | 0,00030960 | 2.475 |
| MC-0004 | Ambigua | 456 | 102 | 0,00034560 | 1.994 |
| MC-0005 | Fuera de tema | 457 | 85 | 0,00031880 | 2.016 |
| **Promedio** | | **449,6** | **103,8** | **0,00034592** | **2.336,6** |

Los tokens provienen de `usage` y la latencia mide el tiempo del motor por caso.
El costo total estimado fue USD 0,00172960. El cálculo aplica USD 0,40 por
millón de tokens de entrada y USD 1,60 por millón de tokens de salida.
[Tarifas del modelo](https://developers.openai.com/api/docs/models/gpt-4.1-mini)

- [Cinco respuestas completas y métricas](evidencias/corrida_pe2_2026-11-25.json).
- [Registro de la corrida real](https://github.com/mstempler/fde-microcreditos11/actions/runs/45628736825).
- [Ejecución de la suite con dependencias fijadas](https://github.com/mstempler/fde-microcreditos11/actions/runs/45628735545).
- [Etiqueta histórica `pe2` (`033ef51`)](https://github.com/mstempler/fde-microcreditos11/tree/pe2).

## KPI y limitaciones

PE1 fija una cobertura de recomendaciones de al menos 90% en casos elegibles.
En esta muestra, los dos casos elegibles recibieron una recomendación de canal
(2/2, 100% observado). Los tres casos restringidos quedan fuera del denominador.
El tamaño de la muestra es insuficiente para validar la meta del 90%.
Los promedios de tokens, costo y latencia describen el desempeño operativo.

La clasificación `tipo_consulta` llega como dato de
entrada: no se demuestra detección autónoma de
ambigüedad o consultas fuera de tema.

No se proporcionaron políticas empresariales reales.
Las recomendaciones no equivalen a autorización de
contacto ni a conformidad regulatoria.

La confianza declarada por el LLM no está calibrada.
El fundamento puede contener inconsistencias semánticas
que las validaciones estructurales no detecten.

## Arquitectura

- `src/contratos.py`: modelos y validaciones Pydantic.
- `src/prompt_sistema.txt`: instrucciones del modelo.
- `src/motor.py`: integración OpenAI, validación,
  reintento, seguridad y métricas.
- `medir_pe2.py`: pruebas y métricas de cinco casos.
- `probar_errores_pe2.py`: pruebas simuladas de errores.
- `verificar_seguridad_pe2.py`: verificaciones reales.
