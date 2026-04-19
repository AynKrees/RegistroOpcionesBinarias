from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

# 1. Configuración: Creamos el archivo de la base de datos
engine = create_engine('sqlite:///trading.db')
Base = declarative_base()

# 2. Tabla de Estrategias (para no repetir texto)
class Strategy(Base):
    __tablename__ = 'strategies'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

# 3. Tabla de Trades (donde registrarás tus operaciones)
class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    executed_at = Column(DateTime, default=datetime.datetime.now)
    asset = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    result = Column(String, nullable=False)
    stake_amount = Column(Float, nullable=False)
    payout_percent = Column(Integer, nullable=False)
    profit_amount = Column(Float)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    screenshot_path = Column(String)
    notes = Column(String)

    __table_args__ = (
        CheckConstraint("direction IN ('CALL', 'PUT')"),
        CheckConstraint("result IN ('WIN', 'LOSS')"),
    )

# 4. Crear las tablas físicamente
Base.metadata.create_all(engine)
print("✅ ¡Base de datos y tablas creadas con éxito!")