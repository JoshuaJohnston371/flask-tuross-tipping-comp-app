from app import create_app, db
from app.models import ChatMessage, Tip, User, UserTipStats


def clear_users():
    app = create_app()
    with app.app_context():
        ChatMessage.query.delete()
        Tip.query.delete()
        UserTipStats.query.delete()
        User.query.delete()
        db.session.commit()


if __name__ == "__main__":
    clear_users()
    print("All users and related data cleared.")
