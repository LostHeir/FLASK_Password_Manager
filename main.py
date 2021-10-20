from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SECRET_KEY'] = '3TDE1-Kb7t7mCW1xt7-Yh4NF03bobu4TSZAYyo8TxBo'
# Generated from terminal: python -c "import secrets; print(secrets.token_urlsafe(32))"


# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///passwords.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CREATE TABLE
class Password(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Run only once to create data base
# db.create_all()


@app.route("/")
def home():
    return "<h1>Hello World!</h1>"


if __name__ == '__main__':
    app.run(debug=True)
