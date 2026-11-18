
import os

from pathlib import Path

from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
    text
)

from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker
)

from sqlalchemy.exc import SQLAlchemyError


# ==========================================
# 1. CARGAR VARIABLES DE ENTORNO
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ==========================================
# 2. CONFIGURACIÓN POSTGRESQL
# ==========================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:

    raise RuntimeError(
        "ERROR: No se encontró DATABASE_URL "
        "en backend/.env"
    )


# ==========================================
# 3. CREAR MOTOR DE CONEXIÓN
# ==========================================

engine = create_engine(
    DATABASE_URL,

    # Verificar conexiones antes de utilizarlas
    pool_pre_ping=True,

    # Máximo de conexiones permanentes
    pool_size=5,

    # Conexiones adicionales permitidas
    max_overflow=10,

    # Tiempo máximo esperando una conexión del pool
    pool_timeout=5,

    # Tiempo máximo para establecer la conexión
    connect_args={
        "connect_timeout": 5
    }
)


# ==========================================
# 4. CONFIGURAR SESIONES
# ==========================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)


# ==========================================
# 5. CLASE BASE DE SQLALCHEMY
# ==========================================

class Base(DeclarativeBase):
    pass


# ==========================================
# 6. DEPENDENCIA PARA FASTAPI
# ==========================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ==========================================
# 7. VERIFICAR CONEXIÓN POSTGRESQL
# ==========================================

def verificar_conexion():

    print(
        "[DATABASE] Verificando conexión "
        "con PostgreSQL..."
    )

    try:

        with engine.connect() as conexion:

            resultado = conexion.execute(
                text("SELECT 1")
            )

            valor = resultado.scalar_one()

            if valor == 1:

                print(
                    "[DATABASE] Conexión exitosa"
                )

                return True

    except SQLAlchemyError as error:

        print(
            "[DATABASE] ERROR DE CONEXIÓN:"
        )

        print(
            f"[DATABASE] {error}"
        )

        return False

    return False
