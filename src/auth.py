from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import validators
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flasgger import swag_from
from src.constants.http_status_codes import *
from src.database import User, db

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth/")


@auth.post("/register")
@swag_from("./docs/auth/register.yaml")
def register():
    username = request.json["username"]
    email = request.json["email"]
    password = request.json["password"]

    if len(password) < 6:
        return (
            jsonify({"error": "Password must be at least 6 characters"}),
            HTTP_400_BAD_REQUEST,
        )
    if len(username) < 3:
        return (
            jsonify({"error": "Username must be at least 3 characters"}),
            HTTP_400_BAD_REQUEST,
        )
    if not username.isalnum() or " " in username:
        return (
            jsonify({"error": "Username must be alphanumeric and no spaces"}),
            HTTP_400_BAD_REQUEST,
        )
    if not validators.email(email):
        return (
            jsonify({"error": "Email is not valid"}),
            HTTP_400_BAD_REQUEST,
        )
    if User.query.filter_by(email=email).first() is not None:
        return (
            jsonify({"error": "Email is already in use"}),
            HTTP_409_CONFLICT,
        )
    if User.query.filter_by(username=username).first() is not None:
        return (
            jsonify({"error": "Username is already in use"}),
            HTTP_409_CONFLICT,
        )

    pwd_hash = generate_password_hash(password)

    user = User(username=username, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()

    return (    
        jsonify({
            "message": "User created",
            "user": {
                "username": username, 
                "email": email,
            },
        }), HTTP_201_CREATED
    )
    
@auth.post("/login")
@swag_from("./docs/auth/login.yaml")
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        is_pwd_correct = check_password_hash(user.password, password)
        
        if is_pwd_correct:
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
        
            return jsonify({
                "user": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "username": user.username,
                    "email": user.email,
                }
            }), HTTP_200_OK

    return jsonify({"message ": "Wrong credentials"}), HTTP_401_UNAUTHORIZED


@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    return jsonify({
        "username": user.username,
        "email": user.email,
    }), HTTP_200_OK


@auth.get("/token/refresh")
@jwt_required(refresh=True)
def refresh_user_token():
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    
    return jsonify({
        "access_token": new_access_token,
    }), HTTP_200_OK
    