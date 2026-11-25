import json
import os
from unittest import TestCase
from unittest.mock import Mock, patch

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    OpenAIError,
)

from probar_errores_pe2 import CASO, probar_error_persistente, probar_reintento
from src.motor import ejecutar_motor


CLAVE_FICTICIA = "clave-ficticia-para-regresion"


class TestMotor(TestCase):
    def test_entrada_invalida_se_detecta_antes_de_configurar_openai(self):
        with patch.dict(os.environ, {}, clear=True), patch("src.motor.OpenAI") as cliente:
            resultado = ejecutar_motor({**CASO, "dias_mora": 0})

        cliente.assert_not_called()
        self.assertFalse(resultado["ok"])
        self.assertEqual(resultado["error"]["tipo"], "entrada_invalida")
        self.assertEqual(resultado["error"]["detalle"][0]["campo"], "dias_mora")
        self.assertEqual(resultado["error"]["intentos"], 0)

    def test_clave_ausente_o_vacia(self):
        for entorno in ({}, {"OPENAI_API_KEY": ""}, {"OPENAI_API_KEY": "   "}):
            with self.subTest(entorno=entorno), patch.dict(
                os.environ, entorno, clear=True
            ), patch("src.motor.OpenAI") as cliente:
                resultado = ejecutar_motor(CASO)
                cliente.assert_not_called()
                self.assertFalse(resultado["ok"])
                self.assertEqual(resultado["error"]["tipo"], "configuracion_api")
                self.assertEqual(resultado["error"]["detalle"]["campo"], "OPENAI_API_KEY")
                self.assertEqual(resultado["error"]["intentos"], 0)

    @patch.dict(os.environ, {"OPENAI_API_KEY": CLAVE_FICTICIA})
    def test_fallo_de_inicializacion_no_expone_la_clave(self):
        with patch("src.motor.OpenAI", side_effect=OpenAIError(CLAVE_FICTICIA)):
            resultado = ejecutar_motor(CASO)

        self.assertFalse(resultado["ok"])
        self.assertEqual(resultado["error"]["tipo"], "configuracion_api")
        self.assertEqual(resultado["error"]["intentos"], 0)
        self.assertNotIn(CLAVE_FICTICIA, json.dumps(resultado))

    @patch.dict(os.environ, {"OPENAI_API_KEY": CLAVE_FICTICIA})
    def test_clasifica_fallos_del_sdk_sin_exponer_detalles(self):
        solicitud = Mock()
        ejemplos = (
            (APIConnectionError(message=CLAVE_FICTICIA, request=solicitud), "conexion_api"),
            (APITimeoutError(solicitud), "timeout_api"),
            (APIError(CLAVE_FICTICIA, solicitud, body=CLAVE_FICTICIA), "error_api"),
        )
        for fallo, tipo in ejemplos:
            with self.subTest(tipo=tipo), patch("src.motor.OpenAI") as cliente:
                crear = cliente.return_value.responses.create
                crear.side_effect = fallo
                resultado = ejecutar_motor(CASO)
                crear.assert_called_once()
                self.assertFalse(resultado["ok"])
                self.assertEqual(resultado["error"]["tipo"], tipo)
                self.assertEqual(resultado["error"]["intentos"], 1)
                self.assertNotIn(CLAVE_FICTICIA, json.dumps(resultado))

    @patch.dict(os.environ, {"OPENAI_API_KEY": CLAVE_FICTICIA})
    def test_clasifica_estados_http_sin_exponer_el_cuerpo(self):
        estados = {
            400: "solicitud_api_invalida",
            401: "autenticacion_api",
            403: "permiso_api",
            404: "error_api",
            429: "limite_api",
            503: "servidor_api",
        }
        for estado, tipo in estados.items():
            with self.subTest(estado=estado), patch("src.motor.OpenAI") as cliente:
                respuesta = Mock(status_code=estado, headers={})
                crear = cliente.return_value.responses.create
                crear.side_effect = APIStatusError(
                    CLAVE_FICTICIA, response=respuesta, body=CLAVE_FICTICIA
                )
                resultado = ejecutar_motor(CASO)
                crear.assert_called_once()
                self.assertFalse(resultado["ok"])
                self.assertEqual(resultado["error"]["tipo"], tipo)
                self.assertEqual(resultado["error"]["intentos"], 1)
                self.assertEqual(resultado["error"]["detalle"]["http"], estado)
                self.assertNotIn(CLAVE_FICTICIA, json.dumps(resultado))

    @patch.dict(os.environ, {"OPENAI_API_KEY": CLAVE_FICTICIA})
    def test_json_invalido_no_expone_el_texto_del_modelo(self):
        with patch("src.motor.OpenAI") as cliente:
            crear = cliente.return_value.responses.create
            crear.return_value = Mock(output_text=CLAVE_FICTICIA, usage=None)
            resultado = ejecutar_motor(CASO)

        self.assertEqual(crear.call_count, 2)
        self.assertFalse(resultado["ok"])
        self.assertEqual(resultado["error"]["tipo"], "salida_invalida")
        self.assertEqual(resultado["error"]["intentos"], 2)
        self.assertNotIn(CLAVE_FICTICIA, json.dumps(resultado))

    @patch.dict(os.environ, {}, clear=True)
    def test_reintento_recupera_una_salida_invalida(self):
        probar_reintento()
        self.assertNotIn("OPENAI_API_KEY", os.environ)

    @patch.dict(os.environ, {}, clear=True)
    def test_salida_invalida_persistente_reporta_campo(self):
        probar_error_persistente()
        self.assertNotIn("OPENAI_API_KEY", os.environ)
