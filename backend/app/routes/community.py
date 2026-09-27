from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Comment, Post, PostLike, User
from app.security import current_user

router = APIRouter(prefix="/community", tags=["community"])

COMMUNITY_CATEGORIES = [
    "Heritage Story", "Travel Experience", "Research", "Local Culture", "Traditional Art",
    "Food", "Indigenous Games", "Architecture", "Festivals",
]


class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=250)
    description: str = Field(min_length=10, max_length=5000)
    category: str
    location: str = Field(min_length=2, max_length=120)


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


def _to_dict(db: Session, p: Post) -> dict:
    comments = db.query(Comment).filter(Comment.post_id == p.id).order_by(Comment.id).all()
    return {
        "id": p.id, "title": p.title, "description": p.description, "author": p.author, "category": p.category,
        "location": p.location, "date": p.date, "likes": p.likes, "label": p.label, "related_heritage": p.related_heritage,
        "comments": [{"author": c.author, "text": c.text, "date": c.date} for c in comments],
    }


@router.get("")
def list_posts(category: str = "", location: str = "", content_type: str = "", db: Session = Depends(get_db)):
    q = db.query(Post)
    if category:
        q = q.filter(Post.category == category)
    if location:
        q = q.filter(Post.location.ilike(f"%{location}%"))
    if content_type:
        q = q.filter(Post.label == content_type)
    posts = q.order_by(Post.date.desc(), Post.id.desc()).all()
    return {"posts": [_to_dict(db, p) for p in posts], "categories": COMMUNITY_CATEGORIES}


@router.get("/{post_id}")
def post_detail(post_id: str, db: Session = Depends(get_db)):
    p = db.get(Post, post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    return _to_dict(db, p)


@router.post("")
def create_post(req: PostCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if req.category not in COMMUNITY_CATEGORIES:
        raise HTTPException(422, "Choose a valid category.")
    p = Post(
        id=f"u-{uuid4().hex[:8]}", title=req.title.strip(), description=req.description.strip(), author=user.name,
        category=req.category, location=req.location.strip(), date=date.today().isoformat(), likes=0,
        label="community", related_heritage=req.location.strip(), created_by=user.id,
    )
    db.add(p)
    db.commit()
    return _to_dict(db, p)


@router.post("/{post_id}/comments")
def add_comment(post_id: str, req: CommentCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.get(Post, post_id):
        raise HTTPException(404, "Post not found")
    db.add(Comment(post_id=post_id, author=user.name, text=req.text.strip(), date=date.today().isoformat()))
    db.commit()
    return _to_dict(db, db.get(Post, post_id))


@router.post("/{post_id}/like")
def like_post(post_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.get(Post, post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    db.add(PostLike(post_id=post_id, user_id=user.id))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "You already liked this post.")
    p.likes += 1
    db.commit()
    return _to_dict(db, p)
