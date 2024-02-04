import asyncio
import threading
import time
from threading import Thread

from binance_bot.config.config import Config
from binance_bot.config.settings import Settings
from binance_bot.process.trading_bot import TradingBot
from binance_bot.utils.constants import TradeExecutionStatus


def fire_and_forget(f):
    def wrapped(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)

    return wrapped


class Runner:

    def __init__(self, sql_client):
        self.sql_client = sql_client

    def trigger(self, entry_id: int, settings, config):
        trading_bot = TradingBot(settings=settings, config=config)
        iteration = 1

        while self.sql_client.get_by_status(entry_id, TradeExecutionStatus.RUNNING):
            try:
                print(f"ITERATION {iteration}, MARKET - {trading_bot.market}:")
                trading_bot.log.info(f"ITERATION {iteration}, MARKET - {trading_bot.market}:\n")

                trading_bot.process()

                iteration += 1
            except Exception as e:
                trading_bot.log.exception(str(e), exc_info=True)
                trading_bot.telegram_client.send_message(f"Encountered Exception:\n {e}")
                trading_bot.binance_client.cancel_all_orders()
                self.sql_client.update_status(entry_id, TradeExecutionStatus.FAILED)

        else:
            trading_bot.binance_client.cancel_all_orders()
            print(f"DELETING - {settings.market}")
            self.sql_client.delete(entry_id)

    def start(self, settings: Settings, config: Config):
        if self.sql_client.get_by_market_region_status(
                market=settings.market, region=settings.region, status=TradeExecutionStatus.RUNNING
        ):
            return False

        entry_id = self.sql_client.create(settings)
        thread = Thread(target=self.trigger, name=settings.market, args=(entry_id, settings, config))
        thread.start()
        return True

    def stop(self, market, region):
        execution_entry = self.sql_client.get_by_market_region_status(market, region, TradeExecutionStatus.RUNNING)
        if not execution_entry:
            return False

        self.sql_client.update_status(execution_entry.id, TradeExecutionStatus.STOPPING)

        # Not needed for now
        # self.stop_thread(market, execution_entry.id)

        return True

    @staticmethod
    def get_thread(market):
        for thread in threading.enumerate():
            if thread.name == market:
                return thread

        return None

    @fire_and_forget
    def stop_thread(self, market, entry_id):
        thread = Runner.get_thread(market)

        while self.sql_client.get(entry_id):
            time.sleep(2)
            continue

        print(f"Process stopped - {market}")

        return thread.join()

    @staticmethod
    def thread_exists(market):
        for thread in threading.enumerate():
            if thread.name == market:
                return True

        return False
