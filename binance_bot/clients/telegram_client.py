import requests


class TelegramClient:

    def __init__(self, token, chat_id):
        self.token = token
        self.url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        self.chat_id = chat_id

    def send_message(self, message):
        """
        https://stackoverflow.com/questions/29003305/sending-telegram-message-from-python
        :param message:
        :return:
        """
        try:
            requests.post(self.url, json={'chat_id': self.chat_id, 'text': message})
        except:
            pass
