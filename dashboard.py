from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database import Trade, engine

Session = sessionmaker(bind=engine)
session = Session()

# Tu capital inicial real
CAPITAL_INICIAL = 51.75

def mostrar_estadisticas():
    # 1. Calcular P&L Total
    total_profit = session.query(func.sum(Trade.profit_amount)).scalar() or 0
    
    # 2. Calcular Winrate
    total_trades = session.query(Trade).count()
    wins = session.query(Trade).filter_by(result="WIN").count()
    winrate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    # 3. Balance Actual
    balance_actual = CAPITAL_INICIAL + total_profit

    print("-" * 30)
    print("📊 DASHBOARD DE TRADING")
    print("-" * 30)
    print(f"💰 Capital Inicial: ${CAPITAL_INICIAL}")
    print(f"📈 P&L Total:      ${round(total_profit, 2)}")
    print(f"🏦 Balance Actual:  ${round(balance_actual, 2)}")
    print(f"🎯 Winrate:         {round(winrate, 2)}%")
    print(f"🔢 Total Trades:    {total_trades}")
    print("-" * 30)

if __name__ == "__main__":
    mostrar_estadisticas()