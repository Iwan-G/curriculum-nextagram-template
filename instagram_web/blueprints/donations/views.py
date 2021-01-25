import os
import requests
from decimal import Decimal
from models.image import Image
from models.donation import Donation
from flask_login import current_user
from instagram_web.util.helpers import gateway
from flask import Blueprint, render_template, request, redirect, url_for, flash

donations_blueprint = Blueprint('donations',
                            __name__,
                            template_folder='templates')

@donations_blueprint.route("/<image_id>/donations/new")
def new(image_id):
    token = gateway.client_token.generate()
    return render_template("donations/new.html", token=token, image_id=image_id)

@donations_blueprint.route("/donations/<image_id>", methods=["POST"])
def create(image_id):
    nonce = request.form["nonce"]
    amount = request.form["amount"]
    result = gateway.transaction.sale({
        "amount": amount,
        "payment_method_nonce": nonce,
        "options": {
            "submit_for_settlement": True
        }
    })
    if result.is_success:
        image = Image.get_by_id(image_id)
        donation = Donation(image=image, amount=Decimal(amount))
        donation.save()
        requests.post(
            f"https://api.mailgun.net/v3/{os.environ['MAILGUN_DOMAIN']}/messages",
            auth=("api", os.environ["MAILGUN_API"]),
            data={
                "from": f"Me <mailgun@{os.environ['MAILGUN_DOMAIN']}>",
                "to": ["gerbersyn@gmail.com"],
                "subject": "Donated",
                "text": f"You have donated ${amount}!"
            }
        )
        flash("Payment successful")
    else:
        flash("Payment not successful")
    return redirect(url_for("users.show", username=current_user.username))