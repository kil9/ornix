import json

from datetime import datetime

from config import db


def get_character(username):
    character = db.session.query(Character).filter_by(name=username).one_or_none()
    if character is None:
        character = Character(username)
    return character


class Team(db.Model):
    __tablename__ = 'globals'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.String(16), unique=True)
    contents = db.Column(db.Text)

    def __init__(self, team_id):
        self.team_id = team_id
        self.contents = '{}'
    
    def __repr__(self):
        return '<Character [{}]>'.format(self.name)

    def get_contents(self):
        return json.loads(self.contents)

    def set_contents(self, contents):
        self.contents = json.dumps(contents)

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

    def get_contents(self):
        return json.loads(self.contents)

    def set_contents(self, contents):
        self.updated_at = datetime.now()
        self.contents = json.dumps(contents)


if __name__ == '__main__':
    #db.drop_all()
    db.create_all()
