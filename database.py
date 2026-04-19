import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from urllib.parse import quote_plus
import datetime

# 1. DEFINIR BASE (Esto faltaba en tu mensaje)
Base = declarative_base()

# 2. Configuración Híbrida
if "supabase" in st.secrets:
    raw_url = st.secrets["supabase"]["URL"]
    
    # Si la URL tiene el #, lo limpiamos automáticamente
    if "#" in raw_url and "%23" not in raw_url:
        # Extraemos la contraseña 'melquisv11#' y la limpiamos
        # Tu URL tiene este formato: postgresql://usuario:clave@host...
        try:
            # Separamos por el @ para obtener la parte de la clave
            protocol_user_pass, host_part = raw_url.split("@", 1)
            protocol_user, password = protocol_user_pass.rsplit(":", 1)
            
            safe_password = quote_plus(password)
            DATABASE_URL = f"{protocol_user}:{safe_password}@{host_part}"
        except Exception:
            # Si falla la limpieza, usamos la URL tal cual
            DATABASE_URL = raw_url
    else:
        DATABASE_URL = raw_url
else:
    DATABASE_URL = 'sqlite:///trading.db'

# Fix de compatibilidad para SQLAlchemy 2.0+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

# 3. Tabla de Estrategias
class Strategy(Base):
    __tablename__ = 'strategies'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

# 4. Tabla de Trades
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

# 5. CREAR TABLAS AUTOMÁTICAMENTE
Base.metadata.create_all(engine)

# Configuración de la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)