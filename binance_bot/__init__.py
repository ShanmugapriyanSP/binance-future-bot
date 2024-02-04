from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///bot.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

    with app.app_context():
        db.init_app(app)
        from binance_bot.models.trade_execution import TradeExecution
        db.drop_all()
        db.create_all()
        db.session.commit()

    from binance_bot.controllers.trade_controller import trade

    app.register_blueprint(trade)
    CORS(app)

    return app
