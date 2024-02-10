from flask import Flask, request, jsonify, redirect
from flask_cors import CORS, cross_origin
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import base64
import re
import os
app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
CORS(app, support_credentials=True)
# Adjust the origin as needed
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydb.db"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

@app.after_request
def after_request(response):
    if response.status_code == 302 and response.location:
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response



@app.route('/<path:generatedKey>', methods=['GET'])
@cross_origin(supports_credentials=True)
def fetch_from_database(generatedKey):
    # Assuming `generatedKey` corresponds to the `short_code` in your database
    url = Url.query.filter_by(short_code=generatedKey).first()
    if not url:
        return '404 not found'

    response = redirect(url.original_url)
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'  # Allow requests from your frontend origin
    return response



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
