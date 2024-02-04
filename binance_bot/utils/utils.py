import math
from typing import Union

from _decimal import Decimal, ROUND_DOWN
from flask import make_response, jsonify

from binance_bot.models.candlestick import Candlestick
from binance_bot.utils.jsonwrapper import JsonWrapper


class Utils:

    @staticmethod
    def parse_json(json):
        result = list()
        json_wrapper = JsonWrapper(json)
        data_list = json_wrapper.convert_2_array()
        for item in data_list.get_items():
            element = Candlestick.json_parse(item)
            result.append(element)
        return result

    @staticmethod
    def get_str_decimal(count):
        return '.' + '0' * (count - 1) + '1'

    @staticmethod
    def get_decimal_value(value, precision, tick_size):
        return Utils.round_step_size(
            Decimal(str(value)).quantize(Decimal(Utils.get_str_decimal(precision)), rounding=ROUND_DOWN),
            tick_size
        )

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

    @staticmethod
    def round_step_size(quantity: Union[float, Decimal], step_size: Union[float, Decimal]) -> float:
        """Rounds a given quantity to a specific step size

        :param quantity: required
        :param step_size: required

        :return: decimal
        """
        quantity = Decimal(str(quantity))
        return float(quantity - quantity % Decimal(str(step_size)))

    @staticmethod
    def get_response(response_body, status_code):
        return make_response(
            jsonify(response_body),
            status_code
        )
