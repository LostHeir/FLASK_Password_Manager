import functools
import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from sqlalchemy.orm import relationship
from cryptography.fernet import Fernet
from itsdangerous import SignatureExpired, TimedJSONWebSignatureSerializer as Serializer


# I will be using Fernet to encrypt and decrypt password stored in database.
# Encryption key is needed, I will use Fernet to generate such key, it can be done by using other random key generators.
key = os.environ.get('FERNET_KEY').encode()  # key generated with: Fernet.generate_key()
fernet = Fernet(key)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')
# Generated from terminal: python -c "import secrets; print(secrets.token_urlsafe(32))"

# CREATE LOGIN MANAGER - needed for user management.
login_manager = LoginManager()
login_manager.init_app(app)


# USER LOADER - needed for user management.
@login_manager.user_loader
def load_user(user_id):
    return PmUser.query.get(int(user_id))


# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRESQL_DATABASE_URL', 'sqlite:///passwords.db')
# PostgreSQL DB on Heroku, alternatively use sqllite DB for local development
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# TIME SERALIZATION
def generate_auth_token():
    """Generates authentication token using Timed JSON Signature.
     Token is created with None object - there is no need to create any, only time stamp is important.
     Retrun time serialized token."""
    s = Serializer(app.config['SECRET_KEY'], expires_in=10)
    token = s.dumps(None)
    return token


def verify_auth_token(token):
    """Verify time stamped token. Return True till time is valid. After time expires return False."""
    s = Serializer(app.config['SECRET_KEY'])
    try:
        s.loads(token)
        return True
    except SignatureExpired:
        return False


# DECORATORS
def login_required(func):
    """Check if current user is loged in. If not return 403 - Access denied."""
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous or current_user.id != 1:
            return abort(403)
        else:
            return func(*args, **kwargs)
    return decorated_function


# CREATE TABLES
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
    """Home page with login form. Data in login form doesn't matter, there is only one hardcoded user in DB."""
    logout_user()  # for hardcoded user - if user don't click Login button he will be treated like anonymous one.
    if request.method == "POST":
        try:  # Try to log in.
            selected_user = PmUser.query.filter_by(id=1).first()
            login_user(selected_user)
        except:  # If there is no user, create one.
            new_user = PmUser(name="User1", password="GreatPassword2*")
            db.session.add(new_user)
            db.session.commit()
        passwords = Password.query.all()
        return render_template("show-all.html", all_passwords=passwords)
    return render_template("index.html")


@app.route('/show_all')
@login_required
def get_all_passwords():
    """Shows all sites sotred in DB. Displays only site name and login used for login,
     click for page name for more details. Passwords are decrypted and then displayed to the user."""
    passwords = Password.query.all()
    return render_template("show-all.html", all_passwords=passwords)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_new_entry():
    """Creates form to create new entry. Adds new entry to the DB. Passwords are encrypted using fernet library."""
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


@app.route('/share_entry/<token>/<int:password_id>')
def share_entry(token, password_id):
    """Displays shared entry details. After expire time redirect user to the home page with notification about this."""
    if verify_auth_token(token):
        entry_to_show = Password.query.get(password_id)
        password_to_show = fernet.decrypt(entry_to_show.password).decode()
        return render_template("share-password.html", data=entry_to_show, password=password_to_show)
    else:
        flash("Your URL has expird, ask for new one.")
        return redirect(url_for("home"))


@app.route("/show_details/<token>/<int:password_id>/<show_link>", methods=["GET", "POST"])
@app.route("/show_details/<int:password_id>", defaults={'show_link': None, 'token': 'nulltoken'})
@login_required
def show_details(token, password_id, show_link):
    """
    Shows details of given entry (password_id). Creates buttons: Edit, Back, Share.
    Edit button redirects user to the edit page.
    Back button redirects user to the show all page.
    Share button creates link, which can be sent to the guest_user.
    Guest will have limited access to the password manager:
    he will only be able to see given entry for a certain amount of time. (token with seralized time stamp is created)
    After that he will be redirected to the home page.
    """
    if request.method == "POST":
        token = generate_auth_token()
        entry_to_show = Password.query.get(password_id)
        password_to_show = fernet.decrypt(entry_to_show.password).decode()
        show_link = bool(show_link)
        return render_template("show-details.html", data=entry_to_show, password=password_to_show, token=token,
                               show_link=show_link)
    entry_to_show = Password.query.get(password_id)
    password_to_show = fernet.decrypt(entry_to_show.password).decode()
    return render_template("show-details.html", data=entry_to_show, password=password_to_show, token=token)


@app.route("/edit/<int:password_id>", methods=["GET", "POST"])
@login_required
def edit_entry(password_id):
    """Creates form to edit given entry. Saves changes to DB afterwards. Password is encrypted using fernet library"""
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
@login_required
def delete_entry(password_id):
    """Romoves given entry from DB."""
    password_to_delete = Password.query.get(password_id)
    db.session.delete(password_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_passwords'))


# MAIN
if __name__ == "__main__":
    app.run(debug=True)
