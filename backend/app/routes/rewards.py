from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Jugador, Recompensa


router = APIRouter(
    prefix="/rewards",
    tags=["Recompensas RabbitMQ"]
)


@router.get("/")
def listar_recompensas(
    db: Session = Depends(get_db)
):

    recompensas = db.scalars(
        select(Recompensa).order_by(Recompensa.id)
    ).all()

    return [
        {
            "id": r.id,
            "operation_id": r.operation_id,
            "combate_id": r.combate_id,
            "jugador_id": r.jugador_id,
            "monedas": r.monedas
        }
        for r in recompensas
    ]


@router.get("/player/{jugador_id}")
def consultar_monedas(
    jugador_id: int,
    db: Session = Depends(get_db)
):

    jugador = db.get(Jugador, jugador_id)

    if jugador is None:
        raise HTTPException(
            status_code=404,
            detail="Jugador no encontrado"
        )

    monedas = db.scalar(
        select(
            func.coalesce(
                func.sum(Recompensa.monedas),
                0
            )
        ).where(
            Recompensa.jugador_id == jugador_id
        )
    )

    return {
        "jugador_id": jugador.id,
        "jugador": jugador.nombre,
        "monedas": monedas
    }