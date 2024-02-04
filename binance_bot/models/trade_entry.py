from _decimal import Decimal

from binance_bot.utils.constants import OrderSide
from binance_bot.utils.utils import Utils


class TradeEntry:
    entry_price: Decimal
    entry_price_actual: float
    capital: int
    qty: Decimal
    qty_actual: float
    take_profit: Decimal
    leveraged_capital: int
    order_side: OrderSide
    stop_side: OrderSide
    order_id: int
    take_profit_order_id: int
    entry_time = None
    cumulative_price: Decimal
    cumulative_qty: Decimal

    def __init__(self, entry_price, capital, qty, take_profit, order_side, leveraged_capital, entry_time, qty_precision,
                 price_precision, tick_size, step_size, cumulative_price=Decimal(0.0), cumulative_qty=Decimal(0.0)):

        self.entry_price_actual = entry_price
        self.entry_price = Utils.get_decimal_value(entry_price, price_precision, tick_size)
        self.capital = capital
        self.qty_actual = qty
        qty = Utils.round_to_precision(qty, qty_precision)
        self.qty = Utils.get_decimal_value(qty, qty_precision, step_size)
        self.take_profit = take_profit
        self.order_side = order_side
        self.stop_side = OrderSide.BUY if order_side == OrderSide.SELL else OrderSide.SELL
        self.leveraged_capital = leveraged_capital
        self.entry_time = entry_time
        self.cumulative_price = cumulative_price
        self.cumulative_qty = cumulative_qty
