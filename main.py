from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config["SECRET_KEY"] = "3TDE1-Kb7t7mCW1xt7-Yh4NF03bobu4TSZAYyo8TxBo"
# Generated from terminal: python -c "import secrets; print(secrets.token_urlsafe(32))"


# CREATE DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///passwords.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# CREATE TABLE
class Password(db.Model):
    __tablename__ = "password_manager"
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), nullable=False)
    site_url = db.Column(db.String(250), nullable=False)
    login = db.Column(db.String(100),  nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Run only once to create data base
# db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/show_all')
def get_all_passwords():
    passwords = Password.query.all()
    print(passwords[0].login)
    return render_template("show-all.html", all_passwords=passwords)


@app.route("/add", methods=["GET", "POST"])
def add_new_entry():
    if request.method == "POST":
        data = request.form
        new_password = Password(
            site_name=data["site"],
            site_url=data["site_url"],
            login=data["login"],
            password=data["password"]
        )
        db.session.add(new_password)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add-password.html")


@app.route("/edit_password/<int:password_id>", methods=["GET", "POST"])
def edit_entry():
    if request.method == "POST":
        return redirect(url_for("home"))
    return redirect(url_for("home"))


@app.route("/delete_password/<int:password_id>")
def edit_entry():
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
