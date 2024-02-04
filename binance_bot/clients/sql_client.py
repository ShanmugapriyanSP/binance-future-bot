from binance_bot.config.settings import Settings
from binance_bot.models.trade_execution import TradeExecution
from binance_bot.utils.constants import TradeExecutionStatus


class SqlClient:

    def __init__(self, db):
        self._db = db

    def create(self, settings: Settings):
        from run import app
        with app.app_context():
            execution_entry = TradeExecution(
                market=settings.market,
                status=TradeExecutionStatus.RUNNING,
                region=settings.region,
                thread_name=settings.market
            )
            self._db.session.add(execution_entry)
            self._db.session.commit()
            return execution_entry.id

    def update_status(self, entry_id, status: str):
        from run import app
        with app.app_context():
            self._db.session.query(TradeExecution).filter_by(id=entry_id).update({"status": status})
            self._db.session.commit()

    def delete(self, entry_id):
        from run import app
        with app.app_context():
            execution = self.get(entry_id)
            self._db.session.delete(execution)
            self._db.session.commit()

    def get(self, entry_id):
        from run import app
        with app.app_context():
            return self._db.session.query(TradeExecution).get_or_404(entry_id)
        # import run
        # with run.app.app_context():
        #     return TradeExecution.query.get_or_404(entry_id)

    def get_by_status(self, entry_id, status: str):
        from run import app
        with app.app_context():
            return self._db.session.query(TradeExecution).filter_by(id=entry_id, status=status).first()
        # import run
        # with run.app.app_context():
        #     return TradeExecution.query.filter_by(id=entry_id, status=status).first()

    def get_all_by_status(self, status: str):
        from run import app
        with app.app_context():
            return self._db.session.query(TradeExecution).filter_by(status=status).all()

    def get_all(self):
        from run import app
        with app.app_context():
            return self._db.session.query(TradeExecution).all()

    def get_by_market_region_status(self, market, region, status: str):
        from run import app
        with app.app_context():
            return self._db.session.query(TradeExecution).filter_by(market=market, region=region, status=status).first()
        # import run
        # with run.app.app_context():
        #     return TradeExecution.query.filter_by(market=market, region=region, status=status).first()

    # def delete_running_records(self):
    #     executions = self.get_all_by_status(TradeExecutionStatus.RUNNING)
    #     (lambda e: self.delete(e.id), executions)
