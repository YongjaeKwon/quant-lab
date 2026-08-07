from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import Date, Float, ForeignKey, String, create_engine, delete, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import NullPool, StaticPool

from operation.models import AccountSnapshot, Holding


class Base(DeclarativeBase):
    pass


class AccountSnapshotRow(Base):
    __tablename__ = "account_snapshot"

    asof: Mapped[date] = mapped_column(Date, primary_key=True)
    total_krw: Mapped[float] = mapped_column(Float)
    cash_krw: Mapped[float] = mapped_column(Float)
    invested_krw: Mapped[float] = mapped_column(Float)
    pnl_rate: Mapped[float] = mapped_column(Float)
    daily_pnl_rate: Mapped[float] = mapped_column(Float)


class HoldingSnapshotRow(Base):
    __tablename__ = "holding_snapshot"

    asof: Mapped[date] = mapped_column(
        Date,
        ForeignKey("account_snapshot.asof"),
        primary_key=True,
    )
    symbol: Mapped[str] = mapped_column(String(24), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    market: Mapped[str] = mapped_column(String(12))
    quantity: Mapped[float] = mapped_column(Float)
    last_price: Mapped[float] = mapped_column(Float)
    average_price: Mapped[float] = mapped_column(Float)


class SnapshotStore:
    """Stores one replaceable account snapshot per date.

    Saving the same date again replaces both the summary and its holdings. This
    makes retries safe and keeps the public demo aligned with the private
    system's idempotent snapshot boundary.
    """

    def __init__(self, db_url: str):
        url = make_url(db_url)
        engine_options: dict[str, object] = {}
        if url.get_backend_name() == "sqlite":
            engine_options["connect_args"] = {"check_same_thread": False}
            if url.database in {None, "", ":memory:"}:
                engine_options["poolclass"] = StaticPool
            else:
                Path(url.database).parent.mkdir(parents=True, exist_ok=True)
                # File handles are released after each unit of work. This matters for
                # temporary-directory cleanup on Windows and is sufficient for the
                # small, local-only demo workload.
                engine_options["poolclass"] = NullPool
        self.engine = create_engine(url, **engine_options)
        Base.metadata.create_all(self.engine)

    def save(self, snapshot: AccountSnapshot) -> None:
        symbols = [holding.symbol for holding in snapshot.holdings]
        if len(symbols) != len(set(symbols)):
            raise ValueError("holding symbols must be unique within a snapshot")
        with Session(self.engine) as session, session.begin():
            session.execute(
                delete(HoldingSnapshotRow).where(HoldingSnapshotRow.asof == snapshot.asof)
            )
            session.execute(
                delete(AccountSnapshotRow).where(AccountSnapshotRow.asof == snapshot.asof)
            )
            session.add(
                AccountSnapshotRow(
                    asof=snapshot.asof,
                    total_krw=snapshot.total_krw,
                    cash_krw=snapshot.cash_krw,
                    invested_krw=snapshot.invested_krw,
                    pnl_rate=snapshot.pnl_rate,
                    daily_pnl_rate=snapshot.daily_pnl_rate,
                )
            )
            session.add_all(
                HoldingSnapshotRow(
                    asof=snapshot.asof,
                    symbol=holding.symbol,
                    name=holding.name,
                    market=holding.market,
                    quantity=holding.quantity,
                    last_price=holding.last_price,
                    average_price=holding.average_price,
                )
                for holding in snapshot.holdings
            )

    def latest(self) -> AccountSnapshot | None:
        with Session(self.engine) as session:
            row = session.scalars(
                select(AccountSnapshotRow)
                .order_by(AccountSnapshotRow.asof.desc())
                .limit(1)
            ).first()
            if row is None:
                return None
            holdings = self._holdings_for(session, row.asof)
            return self._to_snapshot(row, holdings)

    def history(self, days: int = 90) -> list[AccountSnapshot]:
        if days <= 0:
            raise ValueError("days must be positive")
        latest = self.latest()
        if latest is None:
            return []
        cutoff = latest.asof - timedelta(days=days - 1)
        with Session(self.engine) as session:
            rows = session.scalars(
                select(AccountSnapshotRow)
                .where(AccountSnapshotRow.asof >= cutoff)
                .order_by(AccountSnapshotRow.asof.asc())
            ).all()
            return [self._to_snapshot(row, ()) for row in rows]

    def count(self) -> int:
        with Session(self.engine) as session:
            return int(session.scalar(select(func.count()).select_from(AccountSnapshotRow)) or 0)

    def close(self) -> None:
        self.engine.dispose()

    @staticmethod
    def _holdings_for(session: Session, asof: date) -> tuple[Holding, ...]:
        rows = session.scalars(
            select(HoldingSnapshotRow)
            .where(HoldingSnapshotRow.asof == asof)
            .order_by(HoldingSnapshotRow.symbol.asc())
        ).all()
        return tuple(
            Holding(
                symbol=row.symbol,
                name=row.name,
                market=row.market,
                quantity=row.quantity,
                last_price=row.last_price,
                average_price=row.average_price,
            )
            for row in rows
        )

    @staticmethod
    def _to_snapshot(
        row: AccountSnapshotRow,
        holdings: tuple[Holding, ...],
    ) -> AccountSnapshot:
        return AccountSnapshot(
            asof=row.asof,
            total_krw=row.total_krw,
            cash_krw=row.cash_krw,
            invested_krw=row.invested_krw,
            pnl_rate=row.pnl_rate,
            daily_pnl_rate=row.daily_pnl_rate,
            holdings=holdings,
        )
