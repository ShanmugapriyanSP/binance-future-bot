from binance_bot import db


class TradeExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    market = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(20),  nullable=False)
    thread_name = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"Execution('{self.market}', '{self.status}', '{self.region}')"
