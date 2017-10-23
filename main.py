from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:root@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner_id = owner

class User(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = make_pw_hash(password)


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'list_blogs', 'index']
    if request.endpoint not in allowed_routes and 'user' not in session:
        flash('Please log in to post a new blog.', 'error')
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_pw_hash(password, user.password):
            session['user'] = username
            flash("Logged in")
            return redirect('/newpost')
        elif user and not check_pw_hash(password, user.password):
            flash('User password is incorrect', 'error')
            return render_template('login.html')
        else:
            flash('User does not exist', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify_password = request.form['verify']
        existing_user = User.query.filter_by(username=username).first()

        if not existing_user:
            username_error = ''
            password_error = ''
            verify_password_error = ''

            if len(username) < 3 or len(username) > 20 or " " in username:
                username = ''
                password = ''
                verify_password = ''
                username_error = 'Username is required: It must be between 3-20 charachters with no spaces.'
            if len(password) < 3 or len(password) > 20 or " " in password:
                password = ''
                verify_password = ''
                password_error = 'Password is required: It must be between 3-20 charachters with no spaces.'
            if verify_password != password:
                password = ''
                verify_password = ''
                verify_password_error = "Verify password is required: It must match your password exactly."
            if not username_error and not password_error and not verify_password_error:
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()
                user = User.query.filter_by(username=username).first()
                session['user'] = username
                return redirect('/newpost')
            else:
                return render_template('signup.html', username_error=username_error, 
                password_error=password_error, verify_password_error=verify_password_error, username=username, 
                password=password, verify_password=verify_password)
        else:
            flash('Duplicate username. Log In or use a different username.', 'error')
            return render_template('signup.html')
    else:
        return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['user']
    return redirect('/blog')


@app.route('/blog', methods=['GET'])
def list_blogs():
    if request.args.get('id') != None:
        id = request.args.get('id')
        blog = Blog.query.filter_by(id=id).first()
        return render_template('entry.html', blog=blog)
    elif request.args.get('user') != None:
        user = request.args.get('user')
        blog = Blog.query.filter_by(owner_id=user).all()
        author = User.query.filter_by(id=user).first()
        return render_template('blog.html', title=author.username, blogs=blog)
    else:
        blogs = Blog.query.all()
        return render_template('blog.html',title="Blogs", blogs = blogs)


@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    if request.method == 'POST':
        owner = User.query.filter_by(username=session['user']).first()
        blog_title= request.form['title']
        blog_body = request.form['blog']
        blog_owner = owner.id

        title_error=''
        body_error=''

        if len(blog_title) == 0:
            blog_title=''
            title_error='Blogs must have at least a 1 charachter in the title.'
        if len(blog_body) == 0:
            blog_body=''
            body_error='Blogs must have at least 1 charachter in the body.'
        if not title_error and not body_error:
            new_blog = Blog(blog_title, blog_body, blog_owner)
            db.session.add(new_blog)
            db.session.commit()
            return redirect('/blog?id=' + str(new_blog.id))
        else:
            return render_template('newpost.html', blog_title=blog_title, title_error=title_error,
        blog_body=blog_body, body_error=body_error)
    else:
        return render_template('newpost.html')

@app.route('/entry', methods=['GET'])
def entries():
    id = request.args.get('id')
    blog = Blog.query.filter_by(id=id).first()
    return render_template('entry.html', blog=blog)

@app.route('/', methods=['GET'])
def index():
        usernames = User.query.all()
        return render_template('index.html',title="Blog Authors", usernames=usernames)




if __name__ == '__main__':
    app.run()