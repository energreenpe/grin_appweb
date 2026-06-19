"""
Fixtures de pytest para el backend GRIN.

`client` levanta la app FastAPI real con TestClient. Los tests de catálogos del
módulo MATH son de integración (solo lectura) contra la BD de desarrollo ya
migrada y sembrada (scripts/seed_math.py). Requieren PostgreSQL levantado.

Los tests de los motores de cálculo (Aislado / Autoconsumo) son puros y no usan
estos fixtures ni la BD.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
