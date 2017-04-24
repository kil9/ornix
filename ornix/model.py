from datetime import datetime

from config import db

class Character(db.Model):
    __tablename__ = 'characters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    contents = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self, name):
        self.name = name
        self.contents = '{"hp": 0}'
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def __repr__(self):
        return '<Character [{}]>'.format(self.name)

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
