import peewee as pw
from models.user import User
from models.image import Image
from models.donation import Donation
from werkzeug import secure_filename
from instagram_web.util.helpers import upload_file_to_s3
from flask_login import login_required, login_user, current_user
from flask import Blueprint, render_template, request, redirect, url_for, flash

users_blueprint = Blueprint('users',
                            __name__,
                            template_folder='templates')

@users_blueprint.route('/new', methods=['GET'])
def new():
    return render_template('users/new.html')


@users_blueprint.route('/', methods=['POST'])
def create():
    params = request.form

    new_user = User(username = params.get("username"), email=params.get("email"), password=params.get("password"))

    if new_user.save():
        flash("Sign Up Successful", 'success')
        login_user(new_user) #login new user after sign up
        return redirect(url_for('users.show', username=new_user.username)) # redirect user to profile page
    else:
        flash(new_user.errors)
        return redirect(url_for("users.new"))

@users_blueprint.route('/<username>', methods=["GET"])
@login_required
def show(username):
    user = User.select().where(User.username == username).limit(1)
    if user:
        user = pw.prefetch(user, Image, Donation)[0]
        return render_template("users/show.html", user=user)
    else:
        flash("No user found")
        return redirect(url_for('home'))


@users_blueprint.route('/', methods=["GET"])
def index():
    return "USERS"


@users_blueprint.route('/<id>/edit', methods=['GET'])
@login_required
def edit(id):
    user = User.get_or_none(User.id == id)
    if user:
        if current_user.id == int(id):
            return render_template("users/edit.html", user=user)
        else:
            flash("Cannot edit someone else's profile")
            return redirect(url_for('users.show', username=user.username))
    else:
        flash("No user found")
        return redirect(url_for("home"))



@users_blueprint.route('/<id>', methods=['POST'])
@login_required
def update(id):
    user = User.get_or_none(User.id == id)
    if user:
        if current_user.id == int(id):
            params = request.form

            user.is_private = True if params.get("private") == "on" else False

            user.username = params.get("username")
            user.email = params.get("email")
           
            password = params.get("password")
            
            if len(password) > 0:
                user.password = password
            
            if user.save():
                
                flash("Successfully updated details.")
                return redirect(url_for("users.show", username=user.username))
            else:
                flash("Failed to edit the details. Try again")
                for err in user.errors:
                    flash(err)
                return redirect(url_for("users.edit", id=user.id))
        else:
            flash("You cannot edit details of another user")
            return redirect(url_for("home"))
    else:
        flash("No such user found")
        return redirect(url_for("home"))

@users_blueprint.route('/<id>/upload', methods=['POST'])
@login_required
def upload(id):
    user = User.get_or_none(User.id == id)
    if user:
        if current_user.id == int(id):
            # Upload image
            if "profile_image" not in request.files:
                flash("No file selected")
                return redirect(url_for("users.edit", id=id))

            file = request.files["profile_image"]

            file.filename = secure_filename(file.filename)

            image_path = upload_file_to_s3(file, user.username)

            user.image_path = image_path

            if user.save():
                return redirect(url_for("users.show", username = user.username))
            else:
                flash("Upload failed, try again!")
                return redirect(url_for("user.edit", id=id))
        else:
            flash("You cannot edit other profiles")
            return redirect(url_for("users.show", username = user.username))
    else:
        flash("No such user found")
        return redirect(url_for("home"))
@users_blueprint.route('<idol_id>/follow', methods = ['POST'])
@login_required
def follow(idol_id):
    idol = User.get_by_id(idol_id)

    if current_user.follow(idol):
        if current_user.follow_status(idol).is_approved:
            flash(f"You are now following {idol.username}", "info")
        else:
            flash(f"Your request to follow {idol.username} is sent", "info")
        return redirect(url_for('users.show', username=idol.username))
    else:
        flash("Unable to follow this user, try again", "danger")
        return render_template(url_for('users.show', username = idol.username))

@users_blueprint.route('<idol_id>/unfollow', methods = ['POST'])
@login_required
def unfollow(idol_id):
    idol = User.get_byid(idol_id)

    if current_user.unfollow(idol):
        flash(f"You no longer follow {idol.username}", "primary")
        return redirect(url_for('users.show', username=idol.username))
    else:
        flash(f"Failed to unfollow, try again", "danger")
        return redirect(url_for('users.show', username=idol.username))

@users_blueprint.route('/request', methods=['GET'])
@login_required
def show_request():
    return render_template("users/request.html")

@users_blueprint.route('<fan_id>/approve', methods=["POST"])
@login_required
def approve(fan_id):
    fan = User.get_by_id(fan_id)

    if current_user.approve_request(fan):
        flash("Request approved", "info")
        return redirect(url_for('users.show', username=current_user.username))
    else:
        flash("Unable to approve the request, try again","info")
        return redirect(url_for('users.show', username=current_user.username))

@users_blueprint.route('/<fan_id>delete_request', methods=['POST'])
@login_required
def delete_request(fan_id):
    fan = User.get_by_id(fan_id)

    if fan.unfollow(User.get_by_id(current_user.id)):
        flash(f"You have deleted {fan.username}'s request!", "primary")
        return redirect(url_for('users.show', username=current_user.username))
    else:
        flash("Unable to delete the request, try again","info")
        return redirect(url_for('users.show', username=current_user.username))
