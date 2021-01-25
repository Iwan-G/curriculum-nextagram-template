from flask import Blueprint, render_template, request, redirect, url_for, flash
from  models.image import Image
from flask_login import login_required, current_user
from instagram_web.util.helpers import upload_file_to_s3
from werkzeug import secure_filename


images_blueprint = Blueprint('images',
                            __name__,
                            template_folder='templates')

@images_blueprint.route("/new", methods=["GET"])
@login_required
def new():
    return render_template("images/new.html")

@images_blueprint.route("/", methods=["POST"])
@login_required
def create():
    if "user_image" not in request.files:
        flash("No image selected" , 'warning')
        return redirect(url_for('images.new'))
    
    file = request.files['user_image']

    file.filename = secure_filename(file.filename)

    image_path = upload_file_to_s3(file, current_user.username)

    image = Image(image_url = image_path, user = current_user.id)

    if image.save():
        flash("Image uploaded successfully!", 'success')
        return redirect(url_for('users.show', username = current_user.username))
    else:
        flash("Upload failes, try again please!", 'danger')
        return render_template("images/new.html")