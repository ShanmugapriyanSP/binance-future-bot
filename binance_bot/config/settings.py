class Settings:

    def __init__(self, json):
        if "test_net" in json:
            self.test_net = json["test_net"]
            self.region = "TestNet" if self.test_net else "Live"
        elif "binance" in json and "run_type" in json["binance"] and "test_net" in json["binance"]["run_type"]:
            self.test_net = json["binance"]["run_type"]["test_net"]
            self.region = "TestNet" if self.test_net else "Live"
        if "bot_start_datetime" in json:
            self.bot_start_datetime = json["bot_start_datetime"]
        if "trade" in json:
            trade = json["trade"]
            if "market" in trade:
                self.market = trade["market"]
            if "leverage" in trade:
                self.leverage = trade["leverage"]
            if "trading_periods" in trade:
                self.trading_periods = trade["trading_periods"]
            if "margin_type" in trade:
                self.margin_type = trade["margin_type"]
            if "take_profit" in trade:
                self.take_profit = trade["take_profit"]
            if "stop_loss" in trade:
                self.stop_loss = trade["stop_loss"]
            if "next_entry_step" in trade:
                self.next_entry_step = trade["next_entry_step"]
            if "capital_steps" in trade:
                self.capital_steps = trade["capital_steps"]
