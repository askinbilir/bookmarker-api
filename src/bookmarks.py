from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import get_jwt_identity, jwt_required
from flasgger import swag_from
from src.constants.http_status_codes import *
from src.database import Bookmark, db

bookmarks = Blueprint("bookmarks", __name__, url_prefix="/api/v1/bookmarks/")


@bookmarks.route("/", methods=["GET", "POST"])
@jwt_required()
def handle_bookmarks():
    current_user = get_jwt_identity()
    
    if request.method == "POST":
        body = request.get_json().get("body", "")
        url = request.get_json().get("url", "")
        
        if not validators.url(url):
            return jsonify({
                "message": "Enter a valid URL",
            }), HTTP_400_BAD_REQUEST

        if Bookmark.query.filter_by(url=url).first():
            return jsonify({
                "message": "URL already exists"
            }), HTTP_409_CONFLICT
            
        bookmark = Bookmark(url=url, body=body, user_id=current_user)
        db.session.add(bookmark)
        db.session.commit()
        
        return jsonify({
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "visits": bookmark.visits,
            "body": bookmark.body,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at,
        }), HTTP_201_CREATED
        
    else: 
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 5, type=int)
        
        bookmarks = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)
        
        data = []
        
        for bookmark in bookmarks.items:
            data.append({
                "id": bookmark.id,
                "url": bookmark.url,
                "short_url": bookmark.short_url,
                "visits": bookmark.visits,
                "body": bookmark.body,
                "created_at": bookmark.created_at,
                "updated_at": bookmark.updated_at,
            })
            
        meta = {
            "current_page": bookmarks.page,
            "page_count": bookmarks.pages,
            "bookmark_count": bookmarks.total,
            "prev_page": bookmarks.prev_num,
            "next_page": bookmarks.next_num,
            "has_prev": bookmarks.has_prev,
            "has_next": bookmarks.has_next,
        }
            
        return jsonify({
            "data": data,
            "meta": meta,
        }), HTTP_200_OK
        
        
@bookmarks.get("/<int:id>")
@jwt_required()
def get_bookmark(id):
    current_user = get_jwt_identity()
    
    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()
    
    if not bookmark:
        return jsonify({
            "message": "Bookmark not found"
        }), HTTP_404_NOT_FOUND
    
    return jsonify({
        "id": bookmark.id,
        "url": bookmark.url,
        "short_url": bookmark.short_url,
        "visits": bookmark.visits,
        "body": bookmark.body,
        "created_at": bookmark.created_at,
        "updated_at": bookmark.updated_at,
    }), HTTP_200_OK
 
    
@bookmarks.put("/<int:id>")
@bookmarks.patch("/<int:id>")
@jwt_required()
def edit_bookmark(id):
    current_user = get_jwt_identity()
    
    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()
    
    if not bookmark:
        return jsonify({
            "message": "Bookmark not found",
        }), HTTP_404_NOT_FOUND
        
    body = request.get_json().get("body")
    url = request.get_json().get("url")
    
    if not validators.url(url):
        return jsonify({
            "message": "Enter a valid URL"
        }), HTTP_400_BAD_REQUEST
        
    bookmark.body = body
    bookmark.url = url
    
    db.session.commit()
    
    return jsonify({
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "visits": bookmark.visits,
            "body": bookmark.body,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at,
        }), HTTP_200_OK
    

@bookmarks.delete("/<int:id>")
@jwt_required()
def delete_bookmark(id):
    current_user = get_jwt_identity()
    
    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()
    
    if not bookmark:
        return jsonify({
            "message": "Bookmark not found",
        }), HTTP_404_NOT_FOUND
    
    db.session.delete(bookmark)
    db.session.commit()
    
    return jsonify({}), HTTP_204_NO_CONTENT


@bookmarks.get("/stats")
@jwt_required()
@swag_from("./docs/bookmarks/stats.yaml")
def get_stats():
    current_user = get_jwt_identity()

    data = []    
    
    bookmarks = Bookmark.query.filter_by(user_id=current_user).all()
    
    for bookmark in bookmarks:
        new_link = {
            "id": bookmark.id,
            "visits": bookmark.visits,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
        }
        
        data.append(new_link)
    
    return jsonify({
        "data": data,
    }), HTTP_200_OK
