from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from .session import Base


# class Ticker(Base):
#     __tablename__ = "tickers"

#     id = Column(Integer, primary_key=True, index=True)
#     symbol = Column(String, unique=True, nullable=False)
#     trades = relationship("Trade", back_populates="ticker")


# class Trade(Base):
#     __tablename__ = "trades"

#     id = Column(Integer, primary_key=True, index=True)
#     ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
#     trade_date = Column(Date, nullable=False)
#     strike_price = Column(Float, nullable=False)
#     volume = Column(Integer, nullable=False)
#     premium = Column(Float, nullable=False)
#     ticker = relationship("Ticker", back_populates="trades")
