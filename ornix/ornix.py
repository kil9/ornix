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
    if command.lower() == 'echo':
        return cmd


@app.route('/api/hp', methods=['POST'])
def hp():
    print(request.form)
    msg = request.form['text']
    username = request.form['user_name']
    splitted = msg.split(' ')
    log.debug(splitted)

    if len(splitted) > 0 and splitted[0]:
        if splitted[0] == 'party':
            characters = db.session.query(Character).all()

            fields = []
            for character in characters:
                contents = character.get_contents()
                hp = str(contents['hp'])
                max_hp = str(contents['max_hp']) if 'max_hp' in contents else hp
                field = {
                        'title': character.name,
                        'value': '{}/{}'.format(hp, max_hp),
                        'short': True
                        }
                fields.append(field)
            return make_response(username, fields)
        elif splitted[0] == 'max':
            character = get_character(username)
            contents = character.get_contents()
            if len(splitted) > 1:
                try:
                    max_hp = int(splitted[1])
                except ValueError:
                    max_hp = 0
                contents['max_hp'] = max_hp
                character.set_contents(contents)
                db.session.add(character)
                db.session.commit()
            else:
                max_hp = contents['max_hp']
            return make_response(username, 'Max HP: {}'.format(max_hp))




        try:
            hp = int(splitted[0])
        except ValueError:
            hp = 0
            
        character = get_character(username)
        contents = character.get_contents()
        current_hp = int(contents['hp'])
        max_hp = contents['max_hp']
        if splitted[0].startswith('+') or splitted[0].startswith('-'):
            current_hp += hp
        else:
            current_hp = hp
        current_hp = min(current_hp, max_hp)
        contents['hp'] = current_hp
        character.set_contents(contents)
        db.session.add(character)
        db.session.commit()
        return make_response(username, 'Current HP: {}'.format(current_hp))
    else:
        character = get_character(username)
        contents = character.get_contents()
        hp = contents['hp']
        return make_response(username, 'Current HP: {}'.format(hp))


@app.route('/api', methods=['POST'])
def api():
    print(request.form)
    msg = request.form['text']
    username = request.form['user_name']

    r_msg = parse_command(msg, username)
    return make_response(username, r_msg)


def make_response(username, msg):
    if type(msg) == list:
        raw_data = {
                "response_type": "in_channel",
                "attachments": [
                    { "text": '**Party HP**' },
                    {"fields": msg } ] }
    else:
        if msg:
            msg = '@' + username + ' ' + msg
        else:
            msg = '@' + username + ' 네?'
        raw_data = {
                "response_type": "in_channel",
                "text": msg
                }

    encoded = json.dumps(raw_data)
    log.info(encoded)
    resp = Response(encoded, content_type='application/json')

    return resp

if __name__ == '__main__':
    app.run(port=20000, debug=True)
