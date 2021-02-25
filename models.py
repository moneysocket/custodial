from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager

login = LoginManager()
db = SQLAlchemy()

class UserModel(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String())
    account_assignments = db.relationship('AccountAssignment', backref='users',
                                          lazy=True)
    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)


@login.user_loader
def load_user(id):
    return UserModel.query.get(int(id))



class AccountAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
            nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
