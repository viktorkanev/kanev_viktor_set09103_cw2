from flask import render_template,request,redirect, url_for, flash, abort
from app import app,db,bcrypt,mail
from app.forms import RegistrationForm, LoginForm, UpdateProfileForm, PostForm, CommentForm, RequestResetForm, ResetPasswordForm
from app.models import User,Post,Comment
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image
from flask_mail import Message
from sqlalchemy import or_

@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type = int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', title="Home", posts = posts)

@app.route('/search')
def search():
    query = request.args.get('query')
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter(or_(Post.content.like('%'+query+'%'),Post.title.like('%'+query+'%'))).paginate(page=page, per_page=5)
    return render_template('home.html',title="Home", posts=posts)

@app.route("/about")
def about():
    return  render_template('about.html', title= 'About')

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email = form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to login!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title ="Register", form = form)

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page)if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password.','danger')
    return render_template('login.html', title ="Login", form = form)

@app.route("/logout")
def logout():
    logout_user()

    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/avatars', picture_fn)

    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/profile", methods = ['POST', 'GET'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename ='avatars/' + current_user.image_file)
    return render_template('profile.html', title = 'Profile', image_file = image_file, form=form)

@app.route("/post/new", methods = ['POST', 'GET'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content = form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New post', form=form, legend = 'New Post')

@app.route("/post/<int:post_id>", methods = ['POST', 'GET'])
def post(post_id):
    form = CommentForm()
    post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, comment_author=current_user, post_id = post.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
        return redirect('/post/'+(str(post_id)))#render_template('post.html', title = post.title, post=post, form=form)
    return render_template('post.html', title = post.title, post=post, form=form)

# delete comment feature
# @app.route("/post/<int:post_id>/deletecomment", methods = ['POST'])
# @login_required
# def delete_comment(post_id):



@app.route("/post/<int:post_id>/update", methods = ['POST', 'GET'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return  redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title = 'Update Post', form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods = ['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route('/user/<string:username>')
def user_post(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('user_post.html', user=user, posts = posts)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='donotreply@set09103.ac.uk', recipients=[user.email])
    msg.body = f'''To reset your password follow the link provided:
{url_for('reset_token', token=token, _external=True)}
    
If you did not make this request please ignore this message.
'''
    mail.send(msg)

@app.route('/reset_passowrd', methods = ['POST', 'GET'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email with instructions to reset your password has been sent','success')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Rest Password', form=form)

@app.route('/reset_passowrd/<token>', methods = ['POST', 'GET'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Your token is invalid or expired','warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_pw
        db.session.commit()
        flash('Your password has been reset! You are now able to login!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title = 'Reset Password', form=form)

@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_500(error):
    return render_template('500.html'), 500

@app.errorhandler(403)
def error_403(error):
    return render_template('403.html'), 403



