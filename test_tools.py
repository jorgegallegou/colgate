"""
Tests automatizados para las herramientas del agente.
Cubre funciones deterministas (sin llamadas a API ni vectorstore).

Ejecutar con:  uv run pytest test_tools.py -v
"""
import uuid
import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def buscar():
    """Carga la función de búsqueda estructurada una sola vez para todos los tests."""
    from tools import buscar_en_datos_estructurados
    return buscar_en_datos_estructurados


# ── Tests: herramienta de datos estructurados ─────────────────────────────────

class TestDatosEstructurados:

    def test_telefono(self, buscar):
        r = buscar("¿Cuál es el número de teléfono?")
        assert "018000520800" in r

    def test_whatsapp(self, buscar):
        r = buscar("¿Cuál es el teléfono de atención?")
        assert "317 6405757" in r

    def test_nit(self, buscar):
        r = buscar("¿Cuál es el NIT de la empresa?")
        assert "890300546" in r

    def test_horario(self, buscar):
        r = buscar("¿Cuál es el horario de atención?")
        assert "Lunes" in r
        assert "Viernes" in r

    def test_sedes(self, buscar):
        r = buscar("¿Dónde están las sedes en Colombia?")
        assert "Cali" in r
        assert "Bogotá" in r or "Bogota" in r
        assert "Medellín" in r or "Medellin" in r

    def test_marcas(self, buscar):
        r = buscar("¿Cuáles son las marcas que venden?")
        assert "Colgate" in r
        assert "Palmolive" in r

    def test_redes_sociales(self, buscar):
        r = buscar("¿Cuáles son las redes sociales de Colgate?")
        assert "facebook" in r.lower() or "instagram" in r.lower()

    def test_redes_sociales_con_instagram(self, buscar):
        r = buscar("¿Tienen Instagram?")
        assert "instagram" in r.lower()

    def test_correo(self, buscar):
        r = buscar("¿Cuál es el correo electrónico?")
        assert "colpal.com" in r

    def test_sostenibilidad(self, buscar):
        r = buscar("¿Qué hace Colgate en sostenibilidad?")
        assert "reciclable" in r.lower() or "carbono" in r.lower() or "ambiental" in r.lower()

    def test_fundacion(self, buscar):
        r = buscar("¿Qué es la Fundación Colgate?")
        assert "1977" in r or "Fundación" in r or "Fundacion" in r

    def test_programa_social(self, buscar):
        r = buscar("¿Tienen programa social?")
        assert "Fundación" in r or "Fundacion" in r or "sonrisas" in r.lower()

    def test_sitio_web(self, buscar):
        r = buscar("¿Cuál es el sitio web oficial?")
        assert "colgatepalmolive.com.co" in r

    def test_sin_match_retorna_fallback(self, buscar):
        r = buscar("¿Cuántos empleados tienen en Asia?")
        assert "No encontré" in r or "no encontré" in r.lower()

    def test_normalizacion_sin_tildes(self, buscar):
        """La normalización debe manejar preguntas sin tildes correctamente."""
        r = buscar("cual es el numero de telefono")
        assert "018000520800" in r

    def test_normalizacion_mayusculas(self, buscar):
        """La normalización debe manejar mayúsculas correctamente."""
        r = buscar("CUAL ES EL NIT")
        assert "890300546" in r


# ── Tests: función nueva_sesion ───────────────────────────────────────────────

class TestNuevaSesion:

    def test_retorna_string(self):
        from agent import nueva_sesion
        assert isinstance(nueva_sesion(), str)

    def test_es_uuid_valido(self):
        from agent import nueva_sesion
        session = nueva_sesion()
        parsed = uuid.UUID(session)  # lanza ValueError si no es UUID válido
        assert str(parsed) == session

    def test_sesiones_son_unicas(self):
        from agent import nueva_sesion
        sesiones = {nueva_sesion() for _ in range(10)}
        assert len(sesiones) == 10


# ── Tests: función _normalizar ────────────────────────────────────────────────

class TestNormalizar:

    def test_elimina_tildes(self):
        from tools import _normalizar
        assert _normalizar("teléfono") == "telefono"
        assert _normalizar("Medellín") == "medellin"
        assert _normalizar("atención") == "atencion"

    def test_convierte_a_minusculas(self):
        from tools import _normalizar
        assert _normalizar("COLGATE") == "colgate"

    def test_cadena_vacia(self):
        from tools import _normalizar
        assert _normalizar("") == ""
