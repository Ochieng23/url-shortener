import os
import re
from flask_cors import CORS
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import base64

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})   # Adjust the origin as needed
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydb.db"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

class Url(db.Model):
    __tablename__ = 'urls'
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False, unique=True)
    short_code = db.Column(db.String(6), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=1))

    def save(self):
        db.session.add(self)
        db.session.commit()

def generate_unique_id():
    random_bytes = os.urandom(16)
    encoded_id = base64.urlsafe_b64encode(random_bytes).decode("utf-8")[:6]
    return encoded_id

def is_valid_url(url):
    regex = r"^(?:http|https)://\S+\.\S+$"
    return bool(re.match(regex, url))

@app.route('/<short_code>')
def redirect_to_original_url(short_code):
    url = Url.query.filter_by(short_code=short_code).first()
    if url:
        url.clicks += 1
        db.session.commit()
        return redirect(url.original_url)
    else:
        abort(404)

@app.route('/create', methods=['POST'])
def create_short_url():
    original_url = request.form.get('original_url')

    if not original_url or not is_valid_url(original_url):
        return jsonify({"error": "Invalid or missing URL provided."}), 400

    existing_url = Url.query.filter_by(original_url=original_url).first()
    if existing_url:
        return jsonify({"shortened_url": existing_url.short_code}), 200

    short_code = generate_unique_id()

    new_url = Url(original_url=original_url, short_code=short_code)
    new_url.save()

    return jsonify({"shortened_url": short_code}), 201

if __name__ == "__main__":
    app.run()
