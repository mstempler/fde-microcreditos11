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
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Editar `.env` localmente y configurar `OPENAI_API_KEY`.
Nunca publicar la clave.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m src.motor
```

## Pruebas

Pruebas simuladas de reintento y error persistente:

```powershell
.\.venv\Scripts\python.exe probar_errores_pe2.py
```

Cinco consultas reales con mediciones:

```powershell
.\.venv\Scripts\python.exe medir_pe2.py
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

## Evidencia

- `evidencias/mediciones_pe2.csv`: cinco consultas iniciales.
- `evidencias/resultados_pe2.json`: resumen inicial.
- `evidencias/verificacion_seguridad_pe2.json`:
  verificaciones reales posteriores.

Promedios iniciales de cinco consultas:
- Entrada: 428,8 tokens.
- Salida: 70,8 tokens.
- Latencia: 1.728,4 ms.
- Costo estimado: USD 0,0002848 por consulta.

Costos calculados con tarifas de referencia de
USD 0,40/M tokens de entrada y USD 1,60/M tokens
de salida; verificar vigencia antes de citar precios
oficiales en la entrega.

## KPI y limitaciones

KPI técnico de PE1: cobertura de recomendaciones
para al menos el 90% de los casos elegibles.

Las cinco consultas son pruebas exploratorias y no
demuestran cumplimiento estadístico del KPI.
Tampoco demuestran precisión de políticas sobre
100 casos etiquetados ni impacto comercial.

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
