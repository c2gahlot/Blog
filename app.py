from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
# from data import Artcles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

# Articles = Artcles()

# Config MySQL Database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'blog'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MySQL
mysql = MySQL(app)

# Index
@app.route('/')
def index():
    return render_template('index.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Articles
@app.route('/articles')
def articles():
    # create cursor
    cur = mysql.connection.cursor()

    # execute
    results = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    # close connection
    cur.close()

    if results > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html')

# Single Article
@app.route('/article/<id>/')
def article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # execute
    results = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    # close connection
    cur.close()

    return render_template('article.html', article=article)

# Register Form Class
class RegisterForm(Form):
    name = StringField('First Name', validators=[validators.Length(min=1, max=50)])
    username = StringField('Username', validators=[validators.Length(min=4, max=25)])
    email = StringField('Email', validators=[validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# Register User
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()

        # execute query
        cur.execute("INSERT INTO users(name, username, email, password) VALUES (%s, %s, %s, %s)",
                    (name, username, email, password))

        # commit to DB
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('index'))

    return render_template('register.html', form=form)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' :

        # get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # create cursor
        cur = mysql.connection.cursor()

        # execute query
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:

            # get stored hash
            data = cur.fetchone()
            password = data['password']

            # close connection
            cur.close()

            # compare passwords
            if sha256_crypt.verify(password_candidate, password):

                # passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)

        else:

            # close connection
            cur.close()

            error = 'Username Not Found'
            return render_template('login.html', error=error)


    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return  redirect(url_for('login'))
    return wrap


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():

        # create cursor
        cur = mysql.connection.cursor()

        # execute
        results = cur.execute("SELECT * FROM articles")

        articles = cur.fetchall()

        # close connection
        cur.close()

        if results > 0:
            return render_template('dashboard.html', articles=articles)
        else:
            msg = 'No Articles Found'
            return render_template('dashboard.html')

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', validators=[validators.Length(min=1, max=200)])
    body = TextAreaField('body', validators=[validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if(request.method == 'POST' and form.validate()):
        title = form.title.data
        body = form.body.data

        # create cursor
        cur = mysql.connection.cursor()

        # exceute
        cur.execute("INSERT INTO articles (title, body, author) VALUES (%s, %s, %s)", (title, body, session['username']))

        # commit
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit Article
@app.route('/edit_article/<id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):

    # create cursor
    cur = mysql.connection.cursor()

    # exceute
    results = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    # commit
    article = cur.fetchone()

    # close connection
    cur.close()

    # Get Form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if(request.method == 'POST' and form.validate()):
        title = request.form['title']
        body = request.form['body']

        # create cursor
        cur = mysql.connection.cursor()

        # exceute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))

        # commit
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('Article Updates', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<id>', methods=['POST'])
@is_logged_in
def delete_article(id):

    # create cursor
    cur = mysql.connection.cursor()

    # exceute
    cur.execute("DELETE FROM articles WHERE id=%s", [id])

    # commit
    mysql.connection.commit()

    # close connection
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key='secret'
    app.run(debug=True)
