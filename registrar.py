from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Trade, Strategy, engine # Importamos lo que creamos antes

# 1. Configurar la sesión para escribir en la DB
Session = sessionmaker(bind=engine)
session = Session()

def registrar_trade(asset, direction, result, stake, payout, strategy_name, notes="", screenshot=""):
    # Buscar si la estrategia ya existe, si no, crearla
    strat = session.query(Strategy).filter_by(name=strategy_name).first()
    if not strat:
        strat = Strategy(name=strategy_name)
        session.add(strat)
        session.commit()

    # Lógica de cálculo de Profit (la que me pediste)
    if result.upper() == "WIN":
        profit = stake * (payout / 100)
    else:
        profit = -stake

    # Crear el objeto del trade
    nuevo_trade = Trade(
        asset=asset,
        direction=direction.upper(),
        result=result.upper(),
        stake_amount=stake,
        payout_percent=payout,
        profit_amount=round(profit, 2),
        strategy_id=strat.id,
        notes=notes,
        screenshot_path=screenshot
    )

    session.add(nuevo_trade)
    session.commit()
    print(f"✅ Trade registrado: {result} | Profit: ${round(profit, 2)}")

# --- PRUEBA DE REGISTRO ---
# Aquí puedes cambiar los datos por los de tus operaciones reales
registrar_trade(
    asset="EURUSD", 
    direction="CALL", 
    result="WIN", 
    stake=5.0, 
    payout=85, 
    strategy_name="Soporte y Resistencia",
    notes="Rebote en nivel 1.0850",
    screenshot="screenshots/trade1.png"
)