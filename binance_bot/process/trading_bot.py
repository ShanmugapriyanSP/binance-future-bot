import datetime as dt
import logging
import math
import os
import sys
import time
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import List

import pandas as pd
import yaml

from binance_bot.clients.binance_client import BinanceClient
from binance_bot.clients.telegram_client import TelegramClient
from binance_bot.config.config import Config
from binance_bot.config.settings import Settings
from binance_bot.process.strategy import Strategy
from binance_bot.utils.constants import OrderSide, FuturesMarginType
from binance_bot.models.trade_entry import TradeEntry

from binance_bot.utils.utils import Utils


class TradingBot:
    RECV_WINDOW = 100000000
    CSV_FILE = Path(__file__).parent / "../../trade_log.csv"

    def __init__(self, settings, config):
        self.log = self.setup_logger(settings.market, settings.region)
        self.market = settings.market
        self.leverage = int(settings.leverage)
        self.margin_type = self.set_margin_type(settings.margin_type)
        self.confirmation_periods = settings.trading_periods.split(",")
        self.take_profit = float(settings.take_profit)
        self.stop_loss = float(settings.stop_loss)
        self.capital_steps = settings.capital_steps
        self.next_entry_step = settings.next_entry_step
        self.entry_iteration = 0
        self.current_capital = self.capital_steps[self.entry_iteration]
        self.trade_history: List[TradeEntry] = []
        self.wait_datetime = datetime.strptime(settings.bot_start_datetime, '%d-%m-%YT%H:%M:%S') \
            if hasattr(settings, "bot_start_datetime") and settings.bot_start_datetime != "" else None
        self.price_precision = 0
        self.qty_precision = 0
        self.tick_size = 0.0
        self.step_size = 0.0
        self.in_position = False
        self.order_side = OrderSide.INVALID
        self.stop_side = OrderSide.INVALID
        self.side = 0
        self.trade_wait_minutes = 75
        self.binance_client = BinanceClient(
            market=self.market,
            leverage=self.leverage,
            margin_type=self.margin_type,
            log=self.log,
            config=config,
            test_net=settings.test_net
        )
        self.strategy = Strategy(self.binance_client, self.confirmation_periods, self.log)
        self.telegram_client = TelegramClient(config.telegram_token, config.telegram_chat_id)
        self.log.info("Bot Started")

    def wait_till_specified_time(self):
        if self.wait_datetime and datetime.now() < self.wait_datetime:
            time_delta = (self.wait_datetime - datetime.now())
            wait_seconds = time_delta.days * 24 * 60 * 60 + time_delta.seconds
            if wait_seconds > 0:
                self.log.info(
                    f"Waiting for the 4hr candle to complete - {wait_seconds // 60} minutes {(wait_seconds % 60)} seconds."
                    f"Current time - {datetime.now().strftime('%H:%M:%S')}, Resume time - {self.wait_datetime.strftime('%d-%m-%Y_T_%H:%M:%S')}")
                time.sleep(wait_seconds)

    def reset_all_values(self):
        self.price_precision = 0
        self.qty_precision = 0
        self.in_position = False
        self.order_side = OrderSide.INVALID
        self.stop_side = OrderSide.INVALID
        self.side = 0
        self.trade_wait_minutes = 75
        self.entry_iteration = 0
        self.current_capital = self.capital_steps[self.entry_iteration]
        self.trade_history: List[TradeEntry] = []

    @staticmethod
    def setup_logger(market, region):
        date = datetime.now().strftime('%d_%m_%Y')
        logs_path = Path(__file__).parent / "../../logs"
        os.makedirs(f"{logs_path}/{date}", exist_ok=True)
        logging.basicConfig(
            filename=f'{logs_path}/{date}/app_{market}_{region}_{datetime.now().strftime("%d_%m_%Y_T_%H_%M_%S")}.log',
            filemode='w',
            format='%(asctime)s: %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        return logging.getLogger('Binance_BOT')

    @staticmethod
    def set_margin_type(margin_type):
        if margin_type.lower() == "isolated":
            return FuturesMarginType.ISOLATED
        elif margin_type.lower() == "crossed":
            return FuturesMarginType.CROSSED

    @staticmethod
    def get_std_out():
        return sys.stdout

    @staticmethod
    def get_remainder_from_5th_minute():
        return datetime.now().minute % 5

    @staticmethod
    def dict_to_string(dict):
        return str(dict).replace(', ', '\r\n').replace("u'", "").replace("'", "")[1:-1]

    @staticmethod
    def print_condition(my_dict, ind1, ind2, symbol):
        if isinstance(ind2, str):
            print(
                f"{ind1} {symbol} {ind2} | {my_dict[ind1]} {symbol} {my_dict[ind2]} | {eval(str(my_dict[ind1]) + symbol + str(my_dict[ind2]))}")
        else:
            print(
                f"{ind1} {symbol} {ind2} | {my_dict[ind1]} {symbol} {ind2} | {eval(str(my_dict[ind1]) + symbol + str(ind2))}")

        # def check_take_profit(self):

    #     candles = self.binance_client.get_candlestick_data(interval=CandlestickInterval.MIN3, limit=2)
    #     dataframe = self.get_dataframe(candles)
    #     return float(self.take_profit_price) >= dataframe["high"].iloc[-1] if self.order_side == OrderSide.BUY else \
    #         float(self.take_profit_price) <= dataframe["low"].iloc[-1]

    def check_order_status(self, order_id):
        order_status = self.binance_client.query_order(order_id)
        return order_status == "FILLED"

    # def continue_trade(self):
    #     take_profit = self.check_take_profit()
    #     order_status = self.check_order_status()
    #
    #     if take_profit and order_status:
    #         return Trade.PROCEED
    #
    #     if not take_profit:
    #         if not order_status:
    #             self.cancel_all_orders()
    #             return Trade.CLOSED
    #         else:
    #             self.execute_market_order(
    #                 self.qty,
    #                 _type=OrderType.STOP_MARKET,
    #                 _side=self.stop_side
    #             )
    #             return Trade.CLOSED
    #
    #     return Trade.CHECK_AGAIN

    def handle_signal(self):
        # initialise_futures(clients, _market=market, _leverage=leverage)

        # close any open trailing stops we have
        self.binance_client.cancel_all_orders()

        # close_position(clients, _market=market)

        qty = self.calculate_position()

        """ ******** ENTERING POSITION ********* """

        entry_1 = TradeEntry(
            entry_price=self.strategy.entry_price,
            capital=self.current_capital,
            qty=qty,
            take_profit=self.get_take_profit_price(self.strategy.entry_price),
            order_side=self.order_side,
            leveraged_capital=self.current_capital * self.leverage,
            entry_time=datetime.utcnow(),
            qty_precision=self.qty_precision,
            price_precision=self.price_precision,
            tick_size=self.tick_size,
            step_size=self.step_size
        )

        entry_1.order_id, entry_1.take_profit_order_id = self.binance_client.place_trade(entry_1)

        self.send_notification(entry_1)

        self.trade_history.append(entry_1)
        self.in_position = True

        entry_2 = self.get_next_entry()

        entry_2.order_id, _ = self.binance_client.place_trade(entry_2, skip_take_profit=True)

        self.send_notification(entry_2)
        self.trade_history.append(entry_2)

    def get_take_profit_price(self, entry_price):
        if self.order_side == OrderSide.SELL:
            self.take_profit = -self.take_profit

        take_profit_raw = float(entry_price) * ((100 + self.take_profit) / 100)
        return Utils.get_decimal_value(take_profit_raw, self.price_precision, self.tick_size)

    def increment_iteration(self):
        self.entry_iteration += 1
        self.current_capital = self.capital_steps[self.entry_iteration]

    def get_cumulative_qty(self, current_qty):
        cumulative_qty: float = current_qty

        for trade in self.trade_history:
            cumulative_qty += trade.qty_actual

        return cumulative_qty

    def get_cumulative_price(self, current_capital, cumulative_qty):
        cumulative_price: float = current_capital

        for trade in self.trade_history:
            cumulative_price += trade.capital

        cumulative_price = float(cumulative_price * self.leverage) / cumulative_qty

        return cumulative_price

    def get_next_entry_price(self):
        # (1 - ((0.5/100) * n))
        next_entry_percentage = (1 - (self.next_entry_step / 100) * self.entry_iteration)
        next_entry_price = float(self.trade_history[self.entry_iteration - 1].entry_price) * next_entry_percentage
        return Utils.get_decimal_value(next_entry_price, self.price_precision, self.tick_size)

    def get_next_entry(self):

        self.increment_iteration()
        qty = self.calculate_position()
        cumulative_qty = self.get_cumulative_qty(current_qty=qty)
        cumulative_price = self.get_cumulative_price(self.current_capital, cumulative_qty)

        return TradeEntry(
            entry_price=self.get_next_entry_price(),
            capital=self.current_capital,
            qty=qty,
            take_profit=self.get_take_profit_price(cumulative_price),
            order_side=self.order_side,
            leveraged_capital=self.current_capital * self.leverage,
            entry_time=datetime.utcnow(),
            qty_precision=self.qty_precision,
            price_precision=self.price_precision,
            tick_size=self.tick_size,
            step_size=self.step_size,
            cumulative_price=cumulative_price,
            cumulative_qty=cumulative_qty
        )

    def calculate_position(self):
        usdt = self.binance_client.get_futures_balance(_asset="USDT")

        if usdt < self.current_capital:
            raise Exception("Insufficient balance")

        qty = self.calculate_position_size(usdt_balance=self.current_capital)
        self.qty_precision, self.price_precision, self.tick_size, self.step_size = self.get_market_and_price_precision()
        return qty

    def get_futures_balance(self, _asset="USDT"):
        balances = self.binance_client.get_balance()
        asset_balance = 0
        for balance in balances:
            if balance["asset"] == _asset:
                asset_balance = balance["balance"]
                break

        return asset_balance

    def calculate_position_size(self, usdt_balance=1.0):
        price = self.get_current_price()

        qty = (usdt_balance / price) * self.leverage
        # qty = round(qty, 8)

        return qty

    def get_current_price(self):
        price = self.binance_client.get_ticker_price()
        return float(price)

    # get the precision of the market, this is needed to avoid errors when creating orders
    def get_market_and_price_precision(self):
        market_data = self.binance_client.get_exchange_info()
        market_precision = 3
        price_precision = 2
        tick_size = 0.001
        step_size = 0.01
        for market in market_data["symbols"]:
            if market["symbol"] == self.market:
                market_precision = market["quantityPrecision"]
                price_precision = market["pricePrecision"]
                tick_size = market["filters"][0]["tickSize"]
                step_size = market["filters"][1]["stepSize"]
                break

        return market_precision, price_precision, tick_size, step_size

    # round the position size we can open to the precision of the market
    @staticmethod
    def round_to_precision(_qty, _precision):
        """
        Returns a value rounded down to a specific number of decimal places.
        """
        if not isinstance(_precision, int):
            raise TypeError("decimal places must be an integer")
        elif _precision < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif _precision == 0:
            return math.floor(_qty)

        factor = 10 ** _precision
        return float(math.floor(_qty * factor) / factor)

    def get_specific_position(self):
        positions = self.binance_client.get_positions()

        for position in positions:
            if position["symbol"] == self.market:
                break

        return position

    @staticmethod
    def log_trade(_qty, _market="BTCUSDT", _leverage=1, _side="long", _cause="signal", _trigger_price=0.0,
                  _market_price=0.0, _type="exit"):
        df = pd.read_csv(TradingBot.CSV_FILE)
        df2 = pd.DataFrame()
        df2['time'] = [datetime.now()]
        df2['market'] = [_market]
        df2['qty'] = [_qty]
        df2['leverage'] = [_leverage]
        df2['cause'] = [_cause]
        df2['side'] = [_side]
        df2['trigger_price'] = [_trigger_price]
        df2['market_price'] = [_market_price]
        df2['type'] = [_type]
        df2['realised_pnl'] = [None]

        df = df.append(df2, ignore_index=True)
        df.to_csv(TradingBot.CSV_FILE, index=False)

    @staticmethod
    def get_str_decimal(count):
        return '.' + '0' * (count - 1) + '1'

    @staticmethod
    def get_decimal_half(value):
        return Decimal(int(value + 0.5))

    def wait_for_candle(self, minutes):
        wait_time = minutes - datetime.now().minute % minutes
        self.log.info(f"Wait for {wait_time} minutes to proceed next trade. "
                      f"Current Time - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        time.sleep(wait_time * 60)

    def check_in_position(self):
        position = self.get_specific_position()

        self.in_position = False

        if float(position.positionAmt) != 0.0:
            self.in_position = True

    def fetch_realised_pnl(self):
        trades = self.binance_client.get_trades()
        pnl = "0"
        if len(trades) > 0 and "realizedPnl" in trades[0]:
            pnl = str(trades[0]["realizedPnl"]) + " USDT"
            self.log_trade_result(pnl)
        msg = f"Trade Completed, Realised PNL: {pnl}"
        self.telegram_client.send_message(msg)
        self.log.info(f"Trade Completed, Realised PNL: {pnl}")

    def fetch_unrealised_pnl(self):
        position = self.binance_client.get_position_risk()
        msg = f"There is an open trade in progress for {self.market}."
        if len(position) > 0 and "unRealizedProfit" in position[0]:
            msg += " UnrealizedProfit: " + position[0]["unRealizedProfit"] + " USDT"
        self.log.info(msg)

    def close_and_wait(self):
        self.binance_client.cancel_all_orders()
        self.reset_all_values()
        self.wait_for_next_trade()

    def wait_for_next_trade(self):
        self.fetch_realised_pnl()
        self.exit_time = datetime.utcnow()
        exit_hr = self.exit_time.hour
        exit_min = self.exit_time.minute
        exit_second = self.exit_time.second
        wait_seconds = (4 * 60 * 60) - (((((exit_hr % 4) * 60) + exit_min) * 60) + exit_second)
        if wait_seconds > 0:
            resume_time = datetime.now() + dt.timedelta(seconds=wait_seconds)
            self.log.info(
                f"Waiting for the 4hr candle to complete - {wait_seconds // 60} minutes {(wait_seconds % 60)} seconds."
                f"Current time - {datetime.now().strftime('%H:%M:%S')}, Resume time - {resume_time.strftime('%H:%M:%S')}")
            time.sleep(wait_seconds)

    @staticmethod
    def log_trade_result(pnl):
        df = pd.read_csv(TradingBot.CSV_FILE)
        df.loc[df.index[-1], 'realised_pnl'] = pnl
        df.to_csv(TradingBot.CSV_FILE, index=False)

    def send_notification(self, trade_entry: TradeEntry, skip_take_profit=False):
        msg = f"ENTRY {self.entry_iteration + 1}:\nOrderSide: {trade_entry.order_side}\nMarket: {self.market}\nQty: " \
              f"{trade_entry.qty}\nEntryPrice: ${trade_entry.entry_price}\nLeverage: {self.leverage}x" \
              f"\nCurrent time: {datetime.now().strftime('%H:%M:%S')}"

        self.telegram_client.send_message(msg)
        self.log.info(msg)

        self.log_trade(_qty=trade_entry.qty, _market=self.market, _leverage=self.leverage, _side=self.side,
                       _cause="Signal Change",
                       _trigger_price=0, _market_price=float(trade_entry.entry_price), _type=trade_entry.order_side)

        if not skip_take_profit:
            msg = f"Take Profit ${trade_entry.take_profit} is created. Order side - {trade_entry.stop_side}"
            self.telegram_client.send_message(msg)
            self.log.info(msg)

        self.log.info("******************************************************************")

    def is_take_profit_filled(self, trade_entry: TradeEntry):
        return self.check_order_status(trade_entry.take_profit_order_id)

    def is_current_entry_filled(self, trade_entry: TradeEntry):
        return self.check_order_status(trade_entry.order_id)

    def monitor_trade(self):
        self.log.info(f"Monitoring Entry Position - {self.entry_iteration}")

        previous_entry = self.trade_history[self.entry_iteration - 1]
        current_entry = self.trade_history[self.entry_iteration]

        # Checking if take profit is filled
        if self.is_take_profit_filled(previous_entry):
            self.log.info("Take profit is filled")
            self.close_and_wait()
            return
        else:
            self.log.info("Take Profit is not filled")

        # Checking if current entry is filled
        if self.is_current_entry_filled(current_entry):
            self.log.info("Current entry position is filled. Cancelling previous take profit and placing new")
            # Cancel previous take profit order
            self.binance_client.cancel_order(previous_entry.take_profit_order_id)
            # Place new take profit order
            current_entry.take_profit_order_id = self.binance_client.place_take_profit(current_entry)
            # Update entry in trade history
            self.trade_history[self.entry_iteration] = current_entry
            # Calculate next entry
            next_entry = self.get_next_entry()
            # Place next entry
            next_entry.order_id, _ = self.binance_client.place_trade(next_entry, skip_take_profit=True)
            self.send_notification(next_entry, skip_take_profit=True)
            self.trade_history.append(next_entry)
        else:
            self.log.info("Next entry is not filled")

    def process(self):
        # if not currently in a position then execute this set of logic
        if not self.in_position:
            # generate signal data for the last 1000 candles
            self.order_side, self.stop_side = self.strategy.get_multi_scale_signal()

            if self.order_side in [OrderSide.BUY, OrderSide.SELL]:
                self.handle_signal()
            else:
                self.log.info("Conditions not matched, no trade will be taken\n")

        # If already in a position then check market and wait for the trade to complete
        elif self.in_position:
            self.monitor_trade()

        self.log.info("*" * 100)
        self.log.info("")
        time.sleep(10)


class Trade(Enum):
    PROCEED = "proceed"
    CLOSED = "closed"
    CHECK_AGAIN = "check_again"


def execute_locally():
    settings_path = Path(__file__).parent / "../../settings.yml"
    settings_dict = yaml.safe_load(Path(settings_path).read_text())
    trading_bot = TradingBot(settings=Settings(settings_dict), config=Config())

    iteration = 1

    while True:
        try:
            print(f"ITERATION {iteration}, MARKET - {trading_bot.market}:")
            trading_bot.log.info(f"ITERATION {iteration}, MARKET - {trading_bot.market}:\n")

            trading_bot.process()

            iteration += 1
        except Exception as e:
            trading_bot.log.exception(str(e), exc_info=True)
            trading_bot.telegram_client.send_message(f"Encountered Exception:\n {e}")
            trading_bot.binance_client.cancel_all_orders()
            raise


# if __name__ == "__main__":
#     execute_locally()
