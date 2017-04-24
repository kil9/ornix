import json
import random
import requests

from flask import Flask, Response
from flask import render_template
from flask import request

from config import *
from model import *

@app.route('/')
def main():
    return render_template('index.html')

def get_character(username):
    character = db.session.query(Character).filter_by(name=username).one_or_none()
    if character is None:
        character = Character(username)
    return character

def parse_command(cmd, username):
    
    command, *splitted = cmd.split(' ')
    if command.lower() == 'hp' and len(splitted) > 0:
        hp = splitted[0]
        character = get_character(username)
        contents = json.loads(character.contents)
        contents['hp'] = hp
        character.contents = json.dumps(contents)
        db.session.add(character)
        db.session.commit()
        return '현재 HP를 저장했습니다.'
    elif command.lower() == 'hp' and len(splitted) == 0:
        character = get_character(username)
        contents = json.loads(character.contents)
        hp = contents['hp']
        return '{}의 현재 HP는 {}입니다.'.format(character.name, hp)
    elif command.lower() == 'partyhp':
        characters = db.session.query(Character).all()

        fields = []
        for character in characters:
            contents = json.loads(character.contents)
            field = {
                    'title': character.name,
                    'value': contents['hp'],
                    'short': True
                    }
            fields.append(field)
        return fields


@app.route('/api', methods=['POST'])
def api():
    print(request.form)
    msg = request.form['text']
    username = request.form['user_name']

    r_msg = parse_command(msg, username)
    if type(r_msg) == list:
        raw_data = {
                "response_type": "in_channel",
                "attachments": [
                    { "text": 'HP list' },
                    {"fields": r_msg }
                    ]
                }
    else:
        raw_data = {
                "response_type": "in_channel",
                "text": '@' + username + ' ' + r_msg,
                }

    encoded = json.dumps(raw_data)
    log.info(encoded)
    resp = Response(encoded, content_type='application/json')

    return resp

if __name__ == '__main__':
    app.run(port=20000, debug=True)
