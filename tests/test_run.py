import unittest
from pathlib import Path

import yaml

from binance_bot.config.config import Config
from binance_bot.config.settings import Settings
from binance_bot.process.trading_bot import TradingBot


class TestExecution(unittest.TestCase):
    def test_trading_bot(self):
        settings_path = Path(__file__).parent / "../settings.yml"
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


if __name__ == '__main__':
    unittest.main()
