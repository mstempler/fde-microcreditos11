from enum import Enum
from pydantic import BaseModel, Field, model_validator


class Canal(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    TELEFONO = "telefono"
    NINGUNO = "ninguno"


class Prioridad(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"
    BLOQUEADA = "bloqueada"


class TipoConsulta(str, Enum):
    COBRANZA = "cobranza"
    AMBIGUA = "ambigua"
    FUERA_DE_TEMA = "fuera_de_tema"


class Entrada(BaseModel):
    caso_id: str = Field(pattern=r"^MC-[0-9]{4}$")
    dias_mora: int = Field(ge=1, le=30)
    importe_vencido: float = Field(gt=0)
    canales_habilitados: list[Canal] = Field(min_length=1)
    contacto_prohibido: bool = False
    observaciones: str = Field(default="", max_length=500)
    tipo_consulta: TipoConsulta = TipoConsulta.COBRANZA

    @model_validator(mode="after")
    def validar_canales(self):
        if len(self.canales_habilitados) != len(set(self.canales_habilitados)):
            raise ValueError("Los canales habilitados no pueden repetirse")
        if Canal.NINGUNO in self.canales_habilitados:
            raise ValueError("'ninguno' no es un canal habilitado")
        return self


class Salida(BaseModel):
    caso_id: str = Field(pattern=r"^MC-[0-9]{4}$")
    prioridad: Prioridad
    canal_recomendado: Canal
    fundamento: str = Field(min_length=20, max_length=500)
    requiere_supervision: bool
    confianza: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validar_bloqueo(self):
        if self.prioridad == Prioridad.BLOQUEADA:
            if self.canal_recomendado != Canal.NINGUNO:
                raise ValueError(
                    "Un caso bloqueado no puede recomendar contacto"
                )
            if not self.requiere_supervision:
                raise ValueError(
                    "Un caso bloqueado requiere supervisión"
                )
        return self
