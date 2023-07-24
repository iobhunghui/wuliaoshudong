from flask import Flask, request, render_template, session, redirect, url_for
from blueprints import user_bp
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import config
from form import LoginForm, RegisterForm, QaForm, CommentForm
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text(), nullable=False)
    author_name = db.Column(db.String(15), db.ForeignKey('user.name'))
    author = db.relationship('User', backref='comments')
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref='comments')

    def __init__(self, content):
        self.content = content


class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True)
    content = db.Column(db.Text())
    author_name = db.Column(db.String(15), db.ForeignKey('user.name'))
    author = db.relationship('User', backref='questions')

    def __init__(self, title, content):
        self.title = title
        self.content = content


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(20), unique=True)
    passwd = db.Column(db.Text())

    def __init__(self, name, passwd, email):
        self.name = name
        self.email = email
        self.passwd = generate_password_hash(passwd)


app.register_blueprint(user_bp)
with app.app_context():
    # db.drop_all()
    db.create_all()


@app.route('/test')
def test():
    user1 = User('test2', '123456789', 'test@2qq.com')
    qa = Question('123', '321')
    qa.author = user1
    db.session.add(qa)
    db.session.commit()
    print(qa.author_name)
    return "is ok"


@app.route('/search', methods=['GET', 'POST'])
def search():
    search = request.args.get('search')
    if search:
        questions = Question.query.filter(or_(Question.title.contains(search), Question.content.contains(search)))
        return render_template('list.html', questions=questions)
    else:
        return redirect('/')


def get_user():
    user_name = session.get('user_name')
    print(f"username:{user_name}")
    if not user_name:
        return None
    user = User.query.filter_by(name=user_name).first()
    return user

@app.route('/qa/comment/<int:question_id>', methods=['GET', 'POST'])
def comment(question_id):
    if request.method == "GET":
        return render_template('comment.html', question_id=question_id)
    user = get_user()
    if not user:
        return "Please Sign in first"
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return "no questions confrom limit condition were found"
    form = CommentForm(request.form)
    if not form.validate():
        return "the length of comments must be less than 800"
    comment = Comment(form.content.data)
    comment.author = user
    comment.question = question
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('detail', question_id=question_id))


@app.route('/qa/<int:question_id>')
def detail(question_id):
    question = Question.query.filter_by(id=question_id).first()
    if question:
        return render_template('detail.html', question=question)
    return f"issues were not found by id:{question_id}"


@app.route('/', methods=['GET'])
def show_qa():
    questions = Question.query.all()
    return render_template('list.html', questions=questions)


@app.route('/qa', methods=['GET', 'POST'])
def post_qa():
    user = get_user()
    if not user:
        return "Please Sign in first"
    if request.method == 'GET':
        return render_template('qa.html')
    form = QaForm(request.form)
    if not form.validate():
        return redirect(url_for('post_qa'))
    title = form.title.data
    content = form.content.data
    print(title)
    print(content)
    has_qa = Question.query.filter_by(title=title).first()
    if has_qa:
        return redirect(url_for('post_qa'))
    question = Question(title=title, content=content)
    question.author = user
    db.session.add(question)
    db.session.commit()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register_judge():
    if request.method == 'GET':
        return render_template('register.html')
    form = RegisterForm(request.form)
    if not form.validate():
        return redirect(url_for('register_judge'))
    username = form.username.data
    email_data = form.email.data
    user = User.query.filter_by(name=username).first()
    email = User.query.filter_by(email=email_data).first()
    if user or email:
        return redirect(url_for('register_judge'))
    print(form.passwd.data)
    passwd = form.passwd.data
    user = User(username, passwd, email_data)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('login_judge'))


@app.route('/login', methods=['GET', 'POST'])
def login_judge():
    if request.method == "GET":
        return render_template('login.html')
    form = LoginForm(request.form)
    if form.validate():
        username = form.username.data
        passwd = form.passwd.data
        print(username)
        print(passwd)
        user = User.query.filter_by(name=username).first()
        if user and check_password_hash(user.passwd, passwd):
            print(user.passwd)
            session["user_name"] = user.name
            return redirect('/')
        return redirect(url_for('login_judge'))
    return redirect(url_for('login_judge'))


@app.route('/logout')
def session_clear():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)