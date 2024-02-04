import time
from datetime import datetime
from logging import Logger

import pandas as pd
import datetime as dt
import talib.abstract as ta

from binance_bot.clients.binance_client import BinanceClient
from binance_bot.utils.constants import OrderSide, CandlestickInterval


class Strategy:

    def __init__(self, binance_client: BinanceClient, confirmation_periods, log: Logger):
        self.binance_client = binance_client
        self.confirmation_periods = confirmation_periods
        self.log = log
        self.entry_price = 0
        
    def proceed_to_check(self):
        candle_to_check = 3
        number_of_candles = 10
        current_time = datetime.utcnow()
        if current_time.hour % 4 == 0 and current_time.minute < candle_to_check * number_of_candles:
            wait_seconds = (((candle_to_check * number_of_candles) - current_time.minute) * 60) - current_time.second
            resume_time = datetime.now() + dt.timedelta(seconds=wait_seconds)
            self.log.info(
                f"Waiting for {candle_to_check}mins candle start from 4hr confirmation - {wait_seconds // 60} minutes {wait_seconds % 60} seconds."
                f" Current time - {datetime.now().strftime('%H:%M:%S')}, Resume time - {resume_time.strftime('%H:%M:%S')}")
            time.sleep(wait_seconds)
        else:
            current_time = datetime.utcnow()
            current_hr = current_time.hour
            current_min = current_time.minute
            current_second = current_time.second
            wait_seconds = (4 * 60 * 60) - (((((current_hr % 4) * 60) + current_min) * 60) + current_second)
            if wait_seconds > 0:
                resume_time = datetime.now() + dt.timedelta(seconds=wait_seconds)
                self.log.info(
                    f"Waiting for the 4hr candle to complete - {wait_seconds // 60} minutes {(wait_seconds % 60)} seconds."
                    f"Current time - {datetime.now().strftime('%H:%M:%S')}, Resume time - {resume_time.strftime('%H:%M:%S')}")
                time.sleep(wait_seconds)
        
    def get_multi_scale_signal(self):
        order_side = OrderSide.INVALID
        stop_side = OrderSide.INVALID
        signal = 0

        self.proceed_to_check()
        for i, v in enumerate(self.confirmation_periods):
            _signal = self.get_signal(_period=v)
            signal = signal + _signal

        signal = signal / len(self.confirmation_periods)
        # signal = 1
        if signal == 1:
            order_side = OrderSide.BUY
            stop_side = OrderSide.SELL
        elif signal == -1:
            order_side = OrderSide.SELL
            stop_side = OrderSide.BUY

        return order_side, stop_side

    def get_signal(self, _period):
        # candles = self.binance_client.get_candlestick_data(interval=_period, limit=1000)
        candles = self.binance_client.get_candlestick_data(interval=_period, limit=50)
        # candles1m = self.binance_client.get_candlestick_data(interval=CandlestickInterval.MIN1, limit=1000)
        candles3m = self.binance_client.get_candlestick_data(interval=CandlestickInterval.MIN3, limit=50)
        candles1m = self.binance_client.get_candlestick_data(interval=CandlestickInterval.MIN1, limit=50)
        # candles5m = self.binance_client.get_candlestick_data(interval=CandlestickInterval.MIN5, limit=50)
        # candles15m = self.binance_client.get_candlestick_data(interval=CandlestickInterval.MIN15, limit=1000)
        # candles4h = self.binance_client.get_candlestick_data(interval=CandlestickInterval.HOUR4, limit=1000)
        current_price = self.binance_client.get_mark_price()
        dataframe = self.get_dataframe(candles)
        dataframe1m = self.get_dataframe(candles1m)
        dataframe3m = self.get_dataframe(candles3m)
        # dataframe5m = self.get_dataframe(candles5m)
        # dataframe15m = self.get_dataframe(candles15m)
        # dataframe4h = self.get_dataframe(candles4h)
        # entry = self.scalp(dataframe, dataframe1m, dataframe3m, dataframe5m, dataframe15m, dataframe4h, current_price)
        entry = self.scalp(dataframe, dataframe1m, dataframe3m, current_price)
        return entry

    def get_dataframe(self, candles):
        o, h, l, c, v = self.convert_candles(candles)
        return self.to_dataframe(o, h, l, c, v)

    @staticmethod
    def convert_candles(candles):
        o = []
        h = []
        l = []
        c = []
        v = []

        for candle in candles:
            o.append(float(candle.open))
            h.append(float(candle.high))
            l.append(float(candle.low))
            c.append(float(candle.close))
            v.append(float(candle.volume))

        return o, h, l, c, v

    @staticmethod
    def to_dataframe(o, h, l, c, v):
        df = pd.DataFrame()

        df['open'] = o
        df['high'] = h
        df['low'] = l
        df['close'] = c
        df['volume'] = v

        return df

    def scalp(self, dataframe, dataframe1m, dataframe3m, current_price):
        ## HIDDEN
        return entry
    

