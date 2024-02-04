import json
from datetime import datetime
from pathlib import Path
from unittest import TestCase

import pandas as pd

from binance_bot import config as cfg
from binance.um_futures import UMFutures
from pprint import pprint
#
# from telegram.ext.updater import Updater
# from telegram.update import Update
# from telegram.ext.callbackcontext import CallbackContext
# from telegram.ext.commandhandler import CommandHandler
# from telegram.ext.messagehandler import MessageHandler
# from telegram.ext.filters import Filters

import yaml
from munch import DefaultMunch


class CheckProfitLoss(TestCase):

    def setUp(self) -> None:
        self.client = UMFutures(key=cfg.get_public_key(), secret=cfg.get_private_key(),
                                base_url=cfg.get_bot_settings().api_url)

        # print(self.clients.trades("BTCUSDT", limit=500))

    def test_profit(self):
        # pprint(self.clients.get_account_trades(symbol="BTCUSDT", limit=1)[0])
        pprint(self.client.get_position_risk(symbol="BTCUSDT"))
        # pprint(self.clients.query_order(symbol="BTCUSDT", orderId=3195368068))

    def test_csv(self):
        df = pd.read_csv("../trade_log.csv")
        df2 = pd.DataFrame()
        df2['time'] = [datetime.now()]
        df2['market'] = ["BTCUSDT"]
        df2['qty'] = ["21"]
        df2['leverage'] = ["2"]
        df2['cause'] = [None]
        df2['side'] = [None]
        df2['trigger_price'] = [0]
        df2['market_price'] = ["d2435"]
        df2['type'] = [None]
        df2['realised_pnl'] = [None]

        df = df.append(df2, ignore_index=True)
        df.to_csv("../trade_log.csv", index=False)

    def test_log_result(self):
        df = pd.read_csv("../trade_log.csv")
        df.loc[df.index[-1], 'realised_pnl'] = 4.0
        df.to_csv("../trade_log.csv", index=False)

    def test_yml_read(self):
        settings_path = Path(__file__).parent / "../settings.yml"
        obj = DefaultMunch.fromDict(yaml.safe_load(open(settings_path, "r")))
        print(obj.test_net)

    def test_telegram_bot(self):
        import requests

        bot_token = '5540510895:AAEJNrxMGwQK0IyXLi9ePyxcOWU1A6quieI'
        bot_chatID = '560458030'
        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + "HELLO WORLD"

        response = requests.get(send_text)

        return response.json()

        # from telegram import Update
        # from telegram.ext import CommandHandler, ContextTypes
        #
        # async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        #     await update.message.reply_text(f'Hello {update.effective_user.first_name}')
        #
        # app = ApplicationBuilder().token("YOUR TOKEN HERE").build()
        #
        # app.add_handler(CommandHandler("hello", hello))
        #
        # app.run_polling()
