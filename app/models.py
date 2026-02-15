from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import pytz

au_tz = pytz.timezone("Australia/Sydney")

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    avatar = db.Column(db.String(120), nullable=False, default="default.jpg")
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Tip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match = db.Column(db.String(100), nullable=False)
    selected_team = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(au_tz))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'match', name='unique_user_match'),
    )

class Fixture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.String, unique=True, nullable=False)
    season = db.Column(db.Integer, nullable=False)
    round = db.Column(db.Integer, nullable=False)
    home_team = db.Column(db.String, nullable=True)
    home_score = db.Column(db.Integer, nullable=True)
    away_team = db.Column(db.String, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    datetime = db.Column(db.String, nullable=True)

    #__table_args__ = (db.UniqueConstraint('season', 'round', 'home_team', 'away_team', name='_unique_fixture'),)

class FixtureFree(db.Model):
    __tablename__ = 'fixture_free'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.String, unique=True, nullable=False)
    season = db.Column(db.Integer, nullable=False)
    round = db.Column(db.Integer, nullable=False)
    home_team = db.Column(db.String, nullable=True)
    home_score = db.Column(db.Integer, nullable=True)
    away_team = db.Column(db.String, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    date = db.Column(db.Date, nullable=True)
    time = db.Column(db.Time, nullable=True)
    
    @classmethod
    def get_winning_team(cls, match_id):
        fixture = cls.query.filter_by(match_id=match_id).first()
        if not fixture or fixture.home_score is None or fixture.away_score is None:
            return None  # No result yet or match not found

        if fixture.home_score > fixture.away_score:
            return fixture.home_team
        elif fixture.away_score > fixture.home_score:
            return fixture.away_team
        else:
            return "Draw"
    
    #__table_args__ = (db.UniqueConstraint('season', 'round', 'home_team', 'away_team', name='_unique_fixture'),)
    
    
class UserTipStats(db.Model):
    __tablename__ = 'user_tip_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    successful_tips = db.Column(db.Integer, default=0)
    failed_tips = db.Column(db.Integer, default=0)
    pending_tips = db.Column(db.Integer, default=0)

    user = db.relationship('User', backref=db.backref('tip_stats', lazy=True))
    
    
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    match_id = db.Column(db.String, db.ForeignKey("fixture_free.match_id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(au_tz))
    
    user = db.relationship("User", backref="chat_messages")
    match = db.relationship("FixtureFree", backref="chat_messages")
    