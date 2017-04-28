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

def signed(n):
    if n > 0:
        return '+' + str(n)
    elif n == 0:
        return '0'
    else:
        return str(n)

def modifier(n):
    if n > 0:
        return '+ ' + str(n)
    elif n == 0:
        return ''
    else:
        return '- ' + str(abs(n))


@app.route('/api/init', methods=['POST'])
def init():
    print(request.form)
    msg = request.form['text']

    username = request.form['user_name']
    user_id = request.form['user_id']
    splitted = msg.split(' ')

    character = get_character(username)
    contents = character.get_contents()
    contents['user_id'] = user_id
    name = character.name if not 'user_id' in contents else '<@{}|{}>'.format(contents['user_id'], character.name)

    if len(splitted[0]) == 0 or splitted[0] == 'roll':
        init_mod = int(contents['init_mod']) if 'init_mod' in contents else 0
        title = '{} rolls 1d20 {}'.format(name, modifier(init_mod))
        roll = random.randint(1, 20)
        last_init = roll + init_mod
        fields = [{ 'title': 'Rolls',
                    'value': '{}'.format(roll),
                    'short': True },
                  { 'title': 'Result',
                    'value': '{}'.format(last_init),
                    'short': True }]
        contents['last_init'] = last_init
        character.set_contents(contents)
        db.session.add(character)
        db.session.commit()
        if roll > 14:
            color = 'good'
        elif roll > 7:
            color = 'warning'
        else:
            color = 'danger'
        return make_response(fields, title, color=color)

    if splitted[0] == 'mod':
        if len(splitted) > 1:
            try:
                init_mod = int(splitted[1])
            except ValueError:
                init_mod = 0
            contents['init_mod'] = init_mod
        character.set_contents(contents)
        db.session.add(character)
        db.session.commit()
        fields = [{ 'value': signed(init_mod) }]
        return make_response(fields, '{}\'s Initiative modifier'.format(name), color='#439FE0')

    if splitted[0] == 'set':
        if len(splitted) > 1:
            try:
                last_init = int(splitted[1])
            except ValueError:
                last_init = 0
            contents['last_init'] = last_init
        character.set_contents(contents)
        db.session.add(character)
        db.session.commit()
        fields = [{ 'value': str(last_init) }]
        return make_response(fields, '{}\'s Initiative value'.format(name), color='#439FE0')

    if splitted[0] == 'party':
        characters = db.session.query(Character).all()

        char_inits = []
        for character in characters:
            contents = character.get_contents()
            if 'last_init' in contents:
                last_init = str(contents['last_init'])
                name = character.name if not 'user_id' in contents else '<@{}|{}>'.format(contents['user_id'], character.name)
                char_inits.append((name, last_init))
        sorted_inits = sorted(char_inits, key=lambda tup: tup[1])

        merged_inits = ['{} ({})'.format(name, init) for name, init in sorted_inits]
        formatted_inits = ' > '.join(merged_inits)

        fields = [{ 'value': formatted_inits }]
        return make_response(fields, 'Round initiatives', color='#439FE0')

    return process_unknown(username)


def process_unknown(username):
    emojis = (':grinning:', ':frowning:', ':astonished:', ':unamused:', ':sunglasses:', ':mask:', ':sleeping:', ':triumph:', ':innocent:')
    emoji = random.choice(emojis)
    if random.randint(0, 3) == 0:
        emoji = ''

    if random.randint(0, 1) == 0:
        characters = db.session.query(Character).all()
        character = random.choice(characters)
        character_scripts = ('그게 무슨 {} 같은 소리다요', '그건 {}에게 말하면 된다요...?', '어째서.. {}...다요?', '{}! 일어나라요! 죽었어...?', '{}! 일어나라요! 아침이다요?', '{}! 어째서다요!')
        script = random.choice(character_scripts)
        return make_response('{} {}'.format(script.format(character.name), emoji), username=username)
    else:
        scripts = ('내일 날씨는 맑음이다요 거짓말이다요', '알고있다요', '무슨말이다요?', '무슨 말 하고 있는건지 모르겠다요', '닉시코는 그런거 모른다요..', '알았다요', '아 미안하다요 잠깐 졸았다요')
        script = random.choice(scripts)
        return make_response('{} {}'.format(script, emoji), username=username)


def get_color(score):
    if score > 0.8:
        return 'good'
    elif score > 0.3:
        return 'warning'
    else:
        return 'danger'


@app.route('/api/hp', methods=['POST'])
def hp():
    print(request.form)
    msg = request.form['text']
    username = request.form['user_name']
    user_id = request.form['user_id']
    splitted = msg.split(' ')
    log.debug(splitted)

    character = get_character(username)
    contents = character.get_contents()
    contents['user_id'] = user_id
    name = character.name if not 'user_id' in contents else '<@{}|{}>'.format(contents['user_id'], character.name)

    if len(splitted[0]) == 0:
        hp = contents['hp'] if 'hp' in contents else 0
        max_hp = contents['max_hp'] if 'max_hp' in contents else 0
        fields = [{ 'value': '{}/{}'.format(hp, max_hp) }]
        score = hp/max_hp if max_hp > 0 else 0
        return make_response(fields, '{}\'s Current HP'.format(name), color=get_color(score))

    if splitted[0] == 'party':
        characters = db.session.query(Character).all()

        ratios = []
        fields = []
        for character in characters:
            contents = character.get_contents()
            if 'hp' in contents:
                hp = str(contents['hp'])
                max_hp = str(contents['max_hp']) if 'max_hp' in contents else hp
                name = character.name
                field = {
                        'title': name,
                        'value': '{}/{}'.format(hp, max_hp),
                        'short': True
                        }
                ratios.append(int(hp)/int(max_hp))
                fields.append(field)
        score = sum(ratios)/len(ratios) if len(ratios) > 0 else 0
        return make_response(fields, color=get_color(score))

    if splitted[0] == 'party_simple':
        characters = db.session.query(Character).all()

        msgs = []
        for character in characters:
            contents = character.get_contents()
            if 'hp' in contents:
                hp = str(contents['hp'])
                max_hp = str(contents['max_hp']) if 'max_hp' in contents else hp
                msgs.append('{}: {}/{}'.format(name, hp, max_hp))
        msg = '\n'.join(msgs)
        return make_response(msg)

    if splitted[0] == 'max':
        if len(splitted) > 1:
            try:
                max_hp = int(splitted[1])
            except ValueError:
                max_hp = 0
            hp = contents['hp'] if 'hp' in contents else max_hp
            contents['max_hp'] = max_hp
            contents['hp'] = hp
            character.set_contents(contents)
            db.session.add(character)
            db.session.commit()
        else:
            max_hp = contents['max_hp']
        fields = [{ 'value': '{}/{}'.format(hp, max_hp) }]
        score = hp/max_hp if max_hp > 0 else 0
        return make_response(fields, '{}\'s Current HP'.format(name), color=get_color(score))
    if splitted[0] == 'full':
        max_hp = int(contents['max_hp'])
        hp = max_hp
        contents['hp'] = hp
        character.set_contents(contents)
        db.session.add(character)
        db.session.commit()

        fields = [{ 'value': '{}/{}'.format(hp, max_hp) }]
        return make_response(fields, '{}\'s Current HP'.format(name), color=get_color(hp/max_hp))
    if splitted[0] == 'REMOVE':
        if 'max_hp' in contents:
            del(contents['max_hp'])
        if 'hp' in contents:
            del(contents['hp'])
        character.set_contents(contents)
        db.session.add(character)
        db.session.commit()
        return make_response('HP removed')

    try:
        hp = int(splitted[0])
    except ValueError:
        hp = 0

    current_hp = int(contents['hp']) if 'hp' in contents else hp
    max_hp = contents['max_hp'] if 'max_hp' in contents else current_hp

    if splitted[0].startswith('+') or splitted[0].startswith('-'):
        current_hp += hp
    else:
        current_hp = hp
    current_hp = min(current_hp, max_hp)
    current_hp = max(-10, current_hp)
    contents['hp'] = current_hp
    character.set_contents(contents)
    db.session.add(character)
    db.session.commit()
    if current_hp/max_hp > 0.8:
        color = 'good'
    elif current_hp/max_hp > 0.3:
        color = 'warning'
    else:
        color = 'danger'
    fields = [{ 'value': '{}/{}'.format(current_hp, max_hp) }]
    return make_response(fields, 'Current HP', color=color)


@app.route('/api', methods=['POST'])
def api():
    print(request.form)
    msg = request.form['text']
    username = request.form['user_name']

    return process_unknown(username)


def make_response(msg, title='Party HP', color='good', username=None):
    if type(msg) == list:
        raw_data = {
                'response_type': 'in_channel',
                'attachments': [
                    { 'title': title,
                    'color': color,
                    'fields': msg } ] }
    else:
        if username and msg:
            msg = '@' + username + ' ' + msg
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
