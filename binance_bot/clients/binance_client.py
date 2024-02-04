import time

from binance.error import ClientError
from binance.um_futures import UMFutures

from binance_bot.config.config import Config
from binance_bot.utils.constants import OrderType, OrderSide, PositionSide, TimeInForce, WorkingType
from binance_bot.models.trade_entry import TradeEntry
from binance_bot.utils.utils import Utils


class BinanceClient:
    RECV_WINDOW = 100000000

    def __init__(self, market, leverage, margin_type, log, config: Config, test_net: bool):
        self.log = log
        self.market = market
        self.leverage = leverage
        self.margin_type = margin_type
        self.client = None
        self.config = config
        self.test_net = test_net
        self.initialise_futures()

    def initialise_futures(self):
        self.client = UMFutures(
            key=self.config.get_public_key(self.test_net),
            secret=self.config.get_private_key(self.test_net),
            base_url=self.config.get_api_url(self.test_net)
        )
        try:
            response = self.client.change_leverage(
                symbol=self.market, leverage=self.leverage, recvWindow=self.RECV_WINDOW
            )
            self.log.info(response)
        except ClientError as error:
            self.log.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

        try:
            response = self.client.change_margin_type(
                symbol=self.market, marginType=self.margin_type, recvWindow=self.RECV_WINDOW
            )
            self.log.info(response)
        except ClientError as error:
            self.log.warning(f"Ignoring error since margin type - {self.margin_type} is already set.")

    def get_balance(self):
        try:
            response = self.client.balance(recvWindow=self.RECV_WINDOW)
        except ClientError as error:
            self.log.info(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
            raise

        return response

    def get_futures_balance(self, _asset="USDT"):
        balances = self.get_balance()
        asset_balance = 0
        for balance in balances:
            if balance["asset"] == _asset:
                asset_balance = balance["balance"]
                break

        return float(asset_balance)

    def get_candlestick_data(self, interval, limit):
        request = self.client.klines(symbol=self.market, interval=interval, limit=limit)
        return Utils.parse_json(request)

    def get_mark_price(self):
        return self.client.mark_price(symbol=self.market)["markPrice"]

    def get_ticker_price(self):
        return self.client.ticker_price(self.market)["price"]

    def get_exchange_info(self):
        return self.client.exchange_info()

    def query_order(self, order_id):
        return self.client.query_order(orderId=order_id, symbol=self.market)["status"]

    def get_positions(self):
        try:
            positions = self.client.get_position_risk(recvWindow=self.RECV_WINDOW)
        except ClientError as error:
            self.log.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
            raise

        return positions

    def get_trades(self):
        return self.client.get_account_trades(symbol=self.market, limit=1)

    def get_position_risk(self):
        return self.client.get_position_risk(symbol=self.market)

    def cancel_all_orders(self):
        try:
            response = self.client.cancel_open_orders(symbol=self.market, recvWindow=self.RECV_WINDOW)
            self.log.info(response)
        except ClientError as error:
            self.log.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

    def cancel_order(self, order_id):
        try:
            response = self.client.cancel_order(symbol=self.market, order_id=order_id)
            self.log.info(response)
        except ClientError as error:
            self.log.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

    def execute_order(self, _type=OrderType.MARKET, _side=OrderSide.BUY, _position_side=PositionSide.BOTH, _qty=1.0):

        try:
            response = self.client.new_order(
                symbol=self.market,
                side=_side,
                type=_type,
                quantity=_qty,
                positionSide=_position_side
            )
            self.log.info(response)
        except ClientError as error:
            self.log.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
            raise
        return response

    def execute_limit_order(self, _price, _qty, _type=OrderType.LIMIT, _side=OrderSide.SELL,
                            time_in_force=TimeInForce.GTC, reduce_only=True):

        try:
            response = self.client.new_order(
                symbol=self.market,
                side=_side,
                type=_type,
                quantity=_qty,
                price=_price,
                timeInForce=time_in_force,
                reduceOnly=reduce_only
            )
            self.log.info(response)
        except ClientError as error:
            self.log.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
            raise
        return response

    def execute_market_order(self, _stop_price, _type, _side=OrderSide.SELL):

        try:
            response = self.client.new_order(
                symbol=self.market,
                side=_side,
                type=_type,
                stopPrice=_stop_price,
                workingType=WorkingType.MARK_PRICE,
                closePosition=True,
                # reduceOnly=True,
                timeInForce=TimeInForce.GTE_GTC
            )
            self.log.info(response)
        except ClientError as error:
            self.log.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
            raise
        return response

    def place_trade(self, trade_entry: TradeEntry, skip_take_profit=False):
        order_id = 0
        take_profit_order_id = 0

        order_id = self.execute_limit_order(
            _price=trade_entry.entry_price,
            _qty=trade_entry.qty,
            _type=OrderType.LIMIT,
            _side=trade_entry.order_side,
            reduce_only=False
        )["orderId"]

        if not skip_take_profit:
            i = 0
            while True:
                i += 1
                if self.query_order(order_id) == "FILLED":
                    take_profit_order_id = self.place_take_profit(trade_entry)
                    break
                else:
                    time.sleep(1)
                self.log.info(f"iteration - {i}")

        return order_id, take_profit_order_id

    def place_take_profit(self, trade_entry: TradeEntry):
        return self.execute_limit_order(
            _price=trade_entry.take_profit,
            _qty=trade_entry.qty,
            _type=OrderType.LIMIT,
            _side=trade_entry.stop_side
        )["orderId"]
