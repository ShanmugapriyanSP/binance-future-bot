from typing import List

from flask import Blueprint, request

from binance_bot import db
from binance_bot.clients.sql_client import SqlClient
from binance_bot.config.config import Config
from binance_bot.config.settings import Settings
from binance_bot.models.trade_execution import TradeExecution
from binance_bot.process.runner import Runner
from binance_bot.utils.utils import Utils

trade = Blueprint('trade', __name__)
config = Config()
sql_client = SqlClient(db)
runner = Runner(sql_client)


@trade.route('/', methods=['GET'])
def home():
    return "<h1>App started</h1>"


@trade.route('/trade/start', methods=['POST'])
def start_trade():
    settings: Settings = Settings(request.json)
    result = runner.start(settings, config)

    if result:
        return Utils.get_response({"message": f"Bot is started for {settings.market}"}, status_code=200)
    else:
        return Utils.get_response({"message": f"Bot is already running for {settings.market}"}, status_code=403)


@trade.route('/trade/stop', methods=['DELETE'])
def stop_trade():
    args = request.args
    result = runner.stop(args["market"], args["region"])
    if result:
        return Utils.get_response({"message": f"Bot is stopping for {args['market']}"}, status_code=200)
    else:
        return Utils.get_response({"message": f"Error while stopping bot for {args['market']}"}, status_code=500)


@trade.route('/trade/check', methods=['GET'])
def check_running_trade():
    bots: List[TradeExecution] = sql_client.get_all()
    if len(bots) == 0:
        return Utils.get_response({"message": f"No bot is running", "bots": []}, status_code=200)

    status = []
    for bot in bots:
        status.append(
            {
                "market": bot.market,
                "region": bot.region,
                "status": bot.status
            }
        )

    return Utils.get_response({"message": f"Bot is running for following futures", "bots": status}, status_code=200)
