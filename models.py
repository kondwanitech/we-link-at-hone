from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), default='user')
    must_change_password = db.Column(db.Boolean, default=False)
    account_approved = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    lost_items = db.relationship('LostItem', backref='user', lazy=True, cascade='all, delete-orphan')
    found_items = db.relationship('FoundItem', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    posts = db.relationship('Post', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    post_likes = db.relationship('PostLike', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.student_number}>'

class LostItem(db.Model):
    __tablename__ = 'lost_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    color = db.Column(db.String(50))
    model = db.Column(db.String(100))
    size = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    date_lost = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LostItem {self.item_name}>'

class FoundItem(db.Model):
    __tablename__ = 'found_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    color = db.Column(db.String(50))
    model = db.Column(db.String(100))
    size = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    date_found = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FoundItem {self.item_name}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.id}>'

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('PostLike', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def get_likes_count(self):
        return len(self.likes)
    
    def is_liked_by(self, user_id):
        return any(like.user_id == user_id for like in self.likes)
    
    def __repr__(self):
        return f'<Post {self.id}>'

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    reactions = db.relationship('CommentReaction', backref='comment', lazy=True, cascade='all, delete-orphan')
    
    def get_reactions_count(self):
        return len(self.reactions)
    
    def is_reacted_by(self, user_id):
        return any(reaction.user_id == user_id for reaction in self.reactions)
    
    def __repr__(self):
        return f'<Comment {self.id}>'

class PostLike(db.Model):
    __tablename__ = 'post_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_post_like'),)
    
    def __repr__(self):
        return f'<PostLike {self.id}>'

class CommentReaction(db.Model):
    __tablename__ = 'comment_reactions'
    
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('comment_id', 'user_id', name='unique_comment_reaction'),)
    
    def __repr__(self):
        return f'<CommentReaction {self.id}>'
