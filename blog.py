# TODO: Search
# TODO: Tags badge
# TODO: Google Analistic
# TODO: Admin page
# TODO: Email sub
# TODO: Frontend fix
# TODO: Backend fix
# TODO: Contact
# TODO: Donation
# TODO: Responsive design
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, BooleanField, StringField, PasswordField, TextAreaField, DateTimeField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import time
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25), validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])

class PostForm(Form):
    title = StringField('Title', [validators.DataRequired()])
    category = StringField('Category', [validators.DataRequired()])
    content = TextAreaField('Content', [validators.DataRequired()])

class SearchForm(Form):
    query = StringField('search', [validators.DataRequired()])

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    real_name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __init__(self, real_name, username, password):
        self.real_name = real_name
        self.username = username
        self.password = password

class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    date = db.Column(db.String(), nullable=False, default=time.strftime('%d.%m.%Y'))
    author = db.Column(db.String(), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('posts', lazy=True)   )

    def __init__(self, title, category, content, author):
        self.title = title
        self.category = category
        self.content = content
        self.author = author

    def __repr__(self):
        return '<Post %r>' % self.title

class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Category %r>' % self.name

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You Are Not Permitted", "danger")
            return redirect(url_for("home"))
    return decorated_function

@app.route("/")
def home():
    #form = SearchForm(request.form)
    category = Category.query.all()
    if request.method == 'POST' and form.validate():
        query = form.query.data
        post = Post.query.whoosh_search(query).all()

        return render_template("home.html", posts = posts, category = category)
    else:
        posts = Post.query.all()
        return render_template("home.html", posts = posts, category = category)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user:
            if sha256_crypt.verify(password, user.password):
                session["logged_in"] = True
                session["username"] = username

                flash("Welcome", "success")
                return redirect(url_for("admin"))
            else:
                flash("Incorrect email address and / or password.", "danger")
        else:
            flash("Incorrect email address and / or password.", "danger")
    return render_template("login.html", form = form)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/admin")
@login_required
def admin():
    post = Post.query.all()
    return render_template("admin.html", post = post)

@app.route("/add", methods=['GET', 'POST'])
@login_required
def add():
    form = PostForm(request.form)
    if request.method == 'POST' and form.validate():
        #form data
        title = form.title.data
        category = form.category.data
        content = form.content.data

        saved_category = Category.query.filter_by(name=category).first()
        if saved_category:
            author = User.query.filter_by(username=session["username"]).first()
            post = Post(title=title, category=saved_category, content=content, author=author.real_name)
            saved_category.posts.append(post)

            db.session.add(saved_category)
            db.session.commit()

            flash("Success", "success")
            return redirect(url_for("home"))

        else:
            category = Category(name=category)
            author = User.query.filter_by(username=session["username"]).first()
            post = Post(title=title, category=category, content=content, author=author.real_name)

            db.session.add(category)
            db.session.commit()

            flash("Success", "success")
            return redirect(url_for("home"))

    return render_template("add.html", form = form)

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    post = Post.query.filter_by(id=id).first()

    db.session.delete(post)
    db.session.commit()
    flash("Success", "success")
    return redirect(url_for("admin"))

@app.route("/edit/<string:id>", methods=['POST', 'GET'])
@login_required
def edit(id):
    post = Post.query.filter_by(id=id).first()
    form = PostForm(request.form)
    if request.method == 'GET':
        if post:
            form.title.data = post.title
            form.category.data = post.category.name
            form.content.data = post.content
        else:
            flash("Post not found!", "danger")
            return redirect(url_for("admin"))
    else:
        newTitle = form.title.data
        newCategory = form.category.data
        newContent = form.content.data

        post = Category.posts.query.all(id=id)


        post.title = newTitle
        post.category = newCategory
        post.content = newContent

        db.session.commit()

    return render_template("edit.html", form=form)

@app.route("/post/<string:id>")
def post(id):
    post = Post.query.filter_by(id=id).first()
    category = Category.query.all()
    if post:
        return render_template("post.html", post = post, category = category)
    else:
        flash("Post not found :(", "danger")
        return redirect(url_for("home"))

@app.route("/categories/<string:name>")
def categories(name):
    category = Category.query.all()
    post = Post.query.all()
    return render_template("categories.html", post=post, category=category, name=name)



@app.route("/search")
def search():
    query = request.GET.get('query')
    if query:
        post = Post.query.filter_by(title=query)

        return render_template("home.html", post=post)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
