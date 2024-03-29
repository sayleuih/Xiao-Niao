# Imports
import os 
import secrets
from PIL import Image
from flask import Flask, render_template, request, redirect, flash, abort, url_for 
from xiaoniao.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from xiaoniao.models import User, Post
from xiaoniao import app, db, bcrypt
from flask_login import login_user, logout_user, current_user, login_required

# Routing
@app.route('/', methods=['GET', 'POST'])
def index():
    all_posts = Post.query.order_by(Post.date_posted.desc()).all()

    return render_template('index.html', posts = all_posts)

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('/'))

    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@app.route('/post/delete/<int:id>', methods=['GET', 'POST'])
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.author != current_user:
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect('/')

@app.route('/post/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update_post(id):
    post = Post.query.get_or_404(id)

    if post.author != current_user:
        abort(403)
    
    form = PostForm() 
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('/'))
    elif request.method == 'GET':
        form.title.data = post.title 
        form.content.data = post.content
    return render_template('create_post.html', title=post.title, post=post, legend='Update Post')

@app.route('/post/<int:id>')
def post():
    post = Post.query.get_or_404(id)
    return render_template('post.html', title=post.title, post=post)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations. Your account has been successfully created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect('/') 
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')

    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('/'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/img/profile_pics', picture_fn)
    
    # Resize images before saved to save space in the file system.
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username 
        form.email.data = current_user.email 
        
    image_file = url_for('static', filename='img/profile_pics/' + current_user.image_file) 
    return render_template('account.html', title='Account', image_file=image_file, form=form)