import os


class Config:

    def __init__(self):
        self.binance_api_key = os.environ.get('BINANCE_API_KEY')
        self.binance_api_secret = os.environ.get('BINANCE_API_SECRET')
        self.test_binance_api_key = os.environ.get('TEST_BINANCE_API_KEY')
        self.test_binance_api_secret = os.environ.get('TEST_BINANCE_API_SECRET')
        self.telegram_token = os.environ.get('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.api_url = "https://fapi.binance.com"
        self.test_net_url = "https://testnet.binancefuture.com/"

    def get_api_url(self, test_net):
        return self.api_url if not test_net else self.test_net_url

    def get_public_key(self, test_net):
        return self.binance_api_key if not test_net else self.test_binance_api_key

    def get_private_key(self, test_net):
        return self.binance_api_secret if not test_net else self.test_binance_api_secret
