
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.database import (
    Base,
    engine,
    verificar_conexion
)

from app import models

from app.messaging import kafka_outbox, kafka_analytics
from app.routes.kafka_dashboard import router as kafka_dashboard_router

from app.routes import (
    pokemon,
    players,
    battles,
    rewards,
    turns
)


# ==========================================
# CICLO DE VIDA DE FASTAPI
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("\n===================================")
    print(" POKEMON ROJO MASSIMO - BACKEND")
    print("===================================")

    try:

        print(
            "[DATABASE] Verificando PostgreSQL..."
        )

        if not verificar_conexion():

            raise RuntimeError(
                "No se pudo conectar con PostgreSQL"
            )

        print("[DATABASE] PostgreSQL conectado")

        Base.metadata.create_all(
            bind=engine
        )

        print("[DATABASE] Tablas verificadas")

        print("[FRONTEND] Angular se sirve por Nginx; backend solo expone API")

        print("\n[API] Rutas registradas:")
        print(" - /pokemon/")
        print(" - /players/")
        print(" - /battles/")
        print(" - /battles/start")
        print(" - /rewards/")
        print(" - /kafka/overview")
        print(" - /kafka/activity")

        print("\n===================================")
        print(" SERVIDOR LISTO")
        print("===================================\n")

        yield

    finally:

        engine.dispose()

        print("[DATABASE] Conexiones cerradas")
        print("[API] Servidor detenido")


# ==========================================
# CREAR FASTAPI
# ==========================================

app = FastAPI(
    title="Pokemon Rojo Massimo API",
    description=(
        "RPG con PostgreSQL, RabbitMQ "
        "y combates por turnos"
    ),
    version="1.4.0",
    lifespan=lifespan
)


# ==========================================
# ENDPOINT PRINCIPAL
# ==========================================

@app.get("/", tags=["Sistema"])
def inicio():

    return {
        "proyecto": "Pokemon Rojo Massimo",
        "estado": "API funcionando",
        "version": "1.4.0",
        "frontend": "http://localhost:4200",
        "documentacion": "/docs"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health", tags=["Sistema"])
def health():

    return {
        "status": "ok",
        "servicio": "backend",
        "version": "1.4.0"
    }


# ==========================================
# REGISTRAR ROUTERS
# ==========================================

app.include_router(pokemon.router)

app.include_router(players.router)

app.include_router(battles.router)

app.include_router(rewards.router)

app.include_router(turns.router)

app.include_router(kafka_dashboard_router)
