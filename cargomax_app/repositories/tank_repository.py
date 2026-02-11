from __future__ import annotations

from typing import List

from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, Session

from .database import Base
from ..models import Tank, TankType


class TankORM(Base):
    __tablename__ = "tanks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ship_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tank_type: Mapped[str] = mapped_column(String(32), nullable=False)
    capacity_m3: Mapped[float] = mapped_column(Float, default=0.0)
    longitudinal_pos: Mapped[float] = mapped_column(Float, default=0.5)
    kg_m: Mapped[float] = mapped_column(Float, default=0.0)
    tcg_m: Mapped[float] = mapped_column(Float, default=0.0)
    lcg_m: Mapped[float] = mapped_column(Float, default=0.0)


class TankRepository:
    """Repository for CRUD operations on tanks."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_ship(self, ship_id: int) -> List[Tank]:
        tanks: List[Tank] = []
        for obj in (
            self._db.query(TankORM)
            .filter(TankORM.ship_id == ship_id)
            .order_by(TankORM.name)
            .all()
        ):
            tanks.append(
                Tank(
                    id=obj.id,
                    ship_id=obj.ship_id,
                    name=obj.name,
                    tank_type=TankType[obj.tank_type],
                    capacity_m3=obj.capacity_m3,
                    longitudinal_pos=obj.longitudinal_pos,
                    kg_m=obj.kg_m,
                    tcg_m=obj.tcg_m,
                    lcg_m=obj.lcg_m,
                )
            )
        return tanks

    def create(self, tank: Tank) -> Tank:
        if tank.ship_id is None:
            raise ValueError("Tank.ship_id must be set for create")
        obj = TankORM(
            ship_id=tank.ship_id,
            name=tank.name,
            tank_type=tank.tank_type.name,
            capacity_m3=tank.capacity_m3,
            longitudinal_pos=tank.longitudinal_pos,
            kg_m=tank.kg_m,
            tcg_m=tank.tcg_m,
            lcg_m=tank.lcg_m,
        )
        self._db.add(obj)
        self._db.commit()
        self._db.refresh(obj)
        tank.id = obj.id
        return tank

    def update(self, tank: Tank) -> Tank:
        if tank.id is None:
            raise ValueError("Tank.id must be set for update")
        obj = self._db.get(TankORM, tank.id)
        if obj is None:
            raise ValueError(f"Tank with id {tank.id} not found")

        obj.name = tank.name
        obj.tank_type = tank.tank_type.name
        obj.capacity_m3 = tank.capacity_m3
        obj.longitudinal_pos = tank.longitudinal_pos
        obj.kg_m = tank.kg_m
        obj.tcg_m = tank.tcg_m
        obj.lcg_m = tank.lcg_m

        self._db.commit()
        self._db.refresh(obj)
        return tank

    def delete(self, tank_id: int) -> None:
        obj = self._db.get(TankORM, tank_id)
        if obj is None:
            return
        self._db.delete(obj)
        self._db.commit()


