from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from sqlalchemy.orm import relationship
from cryptography.fernet import Fernet


# I will be using Fernet to encrypt and decrypt password stored in database.
# Encryption key is needed, I will use Fernet to generate such key, it can be done by using other random key generators.
key = "SW3HojFnjgC80mLvthtAcKjaELM_qNJkooSYIKK5GxY=".encode()  # key generated with: Fernet.generate_key()
fernet = Fernet(key)

app = Flask(__name__)
app.config["SECRET_KEY"] = "3TDE1-Kb7t7mCW1xt7-Yh4NF03bobu4TSZAYyo8TxBo"
# Generated from terminal: python -c "import secrets; print(secrets.token_urlsafe(32))"

# CREATE LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


# USER LOADER - needed for user management.
@login_manager.user_loader
def load_user(user_id):
    return PmUser.query.get(int(user_id))

# CREATE DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///passwords.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# CREATE TABLE
class PmUser(UserMixin, db.Model):
    __tablename__ = "pm_users"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    # Create realtion One to Many with Password table
    entries = relationship("Password", back_populates="author")


class Password(db.Model):
    __tablename__ = "password_manager"
    id = db.Column(db.Integer, primary_key=True)

    site_name = db.Column(db.String(100), nullable=False)
    site_url = db.Column(db.String(250), nullable=False)
    login = db.Column(db.String(100),  nullable=False)
    password = db.Column(db.String(100), nullable=False)

    # Create relation to BlogUser table
    author = relationship("PmUser", back_populates="entries")
    # Create foreign key to identify author
    author_id = db.Column(db.Integer, db.ForeignKey("pm_users.id"))

# Run only once to create data base
# db.create_all()


# ROUTES
@app.route("/", methods=["GET", "POST"])
def home():
    logout_user()  # for hardcoded user - if user don't click Login button he will be treated like anonymous one.
    if request.method == "POST":
        selected_user = PmUser.query.filter_by(id=1).first()
        login_user(selected_user)
        passwords = Password.query.all()
        return render_template("show-all.html", all_passwords=passwords)
    return render_template("index.html")


@app.route('/show_all')
def get_all_passwords():
    passwords = Password.query.all()
    return render_template("show-all.html", all_passwords=passwords)


@app.route("/add", methods=["GET", "POST"])
def add_new_entry():
    if request.method == "POST":
        data = request.form
        enc_password = fernet.encrypt(data["password"].encode())
        new_password = Password(
            site_name=data["site"],
            site_url=data["site_url"],
            login=data["login"],
            password=enc_password
        )
        db.session.add(new_password)
        db.session.commit()
        return redirect(url_for("get_all_passwords"))
    return render_template("add-password.html")


@app.route("/show_details/<int:password_id>")
def show_details(password_id):
    entry_to_show = Password.query.get(password_id)
    password_to_show = fernet.decrypt(entry_to_show.password).decode()
    return render_template("show-details.html", data=entry_to_show, password=password_to_show)


@app.route("/edit/<int:password_id>", methods=["GET", "POST"])
def edit_entry(password_id):
    password_to_edit = Password.query.get(password_id)
    # Decrypt password to change it
    dec_password = fernet.decrypt(password_to_edit.password).decode()
    if request.method == "POST":
        data = request.form
        edit_password = Password.query.get(password_id)
        # Encrypt password
        edit_enc_password = fernet.encrypt(data["password"].encode())
        # Edit given details
        edit_password.site_name = data["site"]
        edit_password.site_url = data["site_url"]
        edit_password.login = data["login"]
        edit_password.password = edit_enc_password
        db.session.commit()
        return redirect(url_for("get_all_passwords"))
    return render_template("edit-password.html", data=password_to_edit, password=dec_password)


@app.route("/delete/<int:password_id>")
def delete_entry(password_id):
    password_to_delete = Password.query.get(password_id)
    db.session.delete(password_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_passwords'))


# MAIN
if __name__ == "__main__":
    app.run(debug=True)
