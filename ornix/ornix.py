import json
import random

from flask import Response
from flask import render_template
from flask import request

from config import app, db, log
from dice import parse_dice
from model import Team, Character, get_character
from utils import signed, modifier, get_int, set_and_commit, get_color, BLUE


@app.route('/')
def main():
    return render_template('index.html')

@app.route('/api/heal', methods=['POST'])
def heal():
    msg = request.form['text']
    username = request.form['user_name']
    user_id = request.form['user_id']
    commands = msg.split(' ')
    target = commands[0].replace('@', '')
    amount = ' '.join(commands[1:])
    character = get_character(target)
    contents = character.get_contents()
    contents['user_id'] = user_id

    hp = int(contents.get('hp', 0))
    max_hp = int(contents.get('max_hp', 0))

    titles, evaluated, results, score = parse_dice(amount)
    log.info(titles)
    log.info(evaluated)
    log.info(results)
    log.info(score)

    hp += sum(results)
    hp = min(hp, max_hp)
    contents['hp'] = hp
    set_and_commit(character, contents)

    fields = []
    for i in range(len(titles)):
        if len(evaluated[i]) == 0:
            continue
        str_eval = map(str, evaluated[i])
        field = {'title': 'Rolls ({})'.format(titles[i]),
                 'value': ' '.join(str_eval),
                 'short': True}
        fields.append(field)
        field = {'title': 'Result',
                 'value': str(results[i]),
                 'short': True}
        fields.append(field)
    fields.append({
        'title': f'{target}\'s Current HP',
        'value': f'{hp}/{max_hp}'})

    return make_response(fields, f'{username} healed {target}({amount})', color=get_color(hp/max_hp))


@app.route('/api/round', methods=['POST'])
def round():
    msg = request.form['text']
    commands = msg.split(' ')
    team_id = request.form['team_id']
    team = db.session.query(Team).filter(Team.team_id == team_id).one_or_none()
    team = Team(team_id) if team is None else team
    contents = team.get_contents()
    round = contents.get('round', 0)
    if commands[0] == 'start':
        round = 1
    elif commands[0] == 'end':
        round = 0
    elif len(commands[0]) == 0:
        round += 1
    else:
        round = get_int(commands[0], 1)
    contents['round'] = round
    team.set_contents(contents)
    db.session.add(team)
    db.session.commit()
    if commands[0] == 'end':
        characters = db.session.query(Character).all()
        for character in characters:
            contents = character.get_contents()
            if 'last_init' in contents:
                del(contents['last_init'])
                character.set_contents(contents)
                db.session.add(character)
        db.session.commit()
        return make_response('*Rounds cleared!*')

    attachments = [{'title': f'Round {round}',
                    'color': '#f48704'}]
    attachments += stat(True)
    raw_data = {'response_type': 'in_channel',
                'attachments': attachments}
    encoded = json.dumps(raw_data)
    resp = Response(encoded, content_type='application/json')
    return resp


@app.route('/api/stat', methods=['POST'])
def stat(dict_form=False):
    # msg = request.form['text']
    attachments = []
    characters = db.session.query(Character).all()
    if not dict_form:
        team_id = request.form['team_id']
        team = db.session.query(Team).filter(Team.team_id == team_id).one_or_none()
        team = Team(team_id) if team is None else team
        contents = team.get_contents()
        round = contents.get('round', 1)
        if round > 0:
            attachments = [{'title': f'Round {round}',
                            'color': '#f48704'}]

    # read hp
    ratios = []
    fields = []
    for character in characters:
        contents = character.get_contents()
        if 'hp' in contents:
            hp = str(contents['hp'])
            max_hp = str(contents.get('max_hp', hp))
            name = character.name
            field = {
                    'title': name,
                    'value': f'{hp}/{max_hp}',
                    'short': True
                    }
            score = int(hp)/int(max_hp) if int(max_hp) != 0 else 1.0
            ratios.append(score)
            fields.append(field)
    score = sum(ratios)/len(ratios) if len(ratios) > 0 else 0

    attach_hp = {'title': 'Party HP',
                 'fields': fields,
                 'color': get_color(score)}

    attachments.append(attach_hp)

    # read initiatives
    characters = db.session.query(Character).all()

    char_inits = []
    for character in characters:
        contents = character.get_contents()
        if 'last_init' in contents:
            last_init = int(contents['last_init'])
            if 'user_id' not in contents:
                name = character.name
            else:
                name = f'<@{contents["user_id"]}|{character.name}>'
            char_inits.append((name, last_init))
    sorted_inits = sorted(char_inits, key=lambda tup: tup[1], reverse=True)

    merged_inits = [f'{name} ({init})' for name, init in sorted_inits]
    formatted_inits = ' > '.join(merged_inits)

    fields = [{'value': formatted_inits}]

    if len(formatted_inits) > 0:
        attach_init = {'title': 'Round initiatives',
                       'fields': fields,
                       'color': BLUE}

        attachments.append(attach_init)
    if dict_form:
        return attachments

    raw_data = {'response_type': 'in_channel',
                'attachments': attachments}
    encoded = json.dumps(raw_data)
    log.info(encoded)
    resp = Response(encoded, content_type='application/json')
    return resp


@app.route('/api/dice', methods=['POST'])
def dice():
    msg = request.form['text']
    username = request.form['user_name']
    user_id = request.form['user_id']
    commands = msg.split(' ')
    log.debug(commands)

    character = get_character(username)
    contents = character.get_contents()
    contents['user_id'] = user_id
    if 'user_id' not in contents:
        name = character.name
    else:
        name = f'<@{contents["user_id"]}|{character.name}>'

    try:
        titles, evaluated, results, score = parse_dice(msg)
    except:
        return process_unknown(username)

    color = get_color(score)
    roll_title = ' / '.join(titles)
    title = f'{name} rolled {roll_title}'
    fields = []
    for i in range(len(titles)):
        if len(evaluated[i]) == 0:
            continue
        str_eval = map(str, evaluated[i])
        field = {'title': 'Rolls ({})'.format(titles[i]),
                 'value': ' '.join(str_eval),
                 'short': True}
        fields.append(field)
        field = {'title': 'Result',
                 'value': str(results[i]),
                 'short': True}
        fields.append(field)

    return make_response(fields, title, color=color)


@app.route('/api/spell', methods=['POST'])
def spell():
    print(request.form)
    msg = request.form['text']
    username = request.form['user_name']
    user_id = request.form['user_id']
    commands = msg.split(' ')
    log.debug(commands)

    character = get_character(username)
    contents = character.get_contents()
    contents['user_id'] = user_id
    if 'user_id' not in contents:
        name = character.name
    else:
        name = f'<@{contents["user_id"]}|{character.name}>'

    # contents - 'spell' - 'per day' - [...]
    #                    - 'left'    - [...]

    if len(commands[0]) == 0 or commands[0] == 'book':
        if 'spell' not in contents:
            return make_response('Spells should be set first', username=username)

        per_days = contents['spell']['per day']
        lefts = contents['spell']['left']

        fields = [{'title': 'Spells per day',
                   'value': ' / '.join(map(str, per_days))},
                  {'title': 'Spells Left',
                   'value': ' / '.join(map(str, lefts))}]
        return make_response(fields, f'{name}\'s Spellbook')

    if len(commands) > 1 and commands[0] in ('set', 'per day'):
        raw_spells = commands[1].split('/')
        spells = list(map(lambda x: get_int(x, 0), raw_spells))[:10]
        spells += (10 - len(spells)) * [0]

        if 'spell' not in contents:
            contents['spell'] = {'per day': spells,
                                 'left': spells}
        else:
            contents['spell']['per day'] = spells
        set_and_commit(character, contents)
        fields = [{'title': 'Spells per day',
                   'value': ' / '.join(map(str, spells))},
                  {'title': 'Spells left',
                   'value': ' / '.join(map(str, contents['spell']['left']))}]
        return make_response(fields, f'{name}\'s Spellbook')

    if len(commands) > 1 and commands[0] == 'left':
        if 'spell' not in contents:
            return make_response('Spells per day should be set first', username=username)

        raw_spells = commands[1].split('/')
        spells = list(map(lambda x: get_int(x, 0), raw_spells))[:10]
        spells += (10 - len(spells)) * [0]

        contents['spell']['left'] = spells
        set_and_commit(character, contents)
        fields = [{'title': 'Spells per day',
                   'value': ' / '.join(map(str, contents['spell']['per day']))},
                  {'title': 'Spells left',
                   'value': ' / '.join(map(str, spells))}]
        return make_response(fields, f'{name}\'s Spellbook')

    if len(commands) > 1 and commands[0] in ('use', 'cast'):
        if 'spell' not in contents:
            return make_response('Spells should be set first', username=username)

        if len(commands) > 2:
            spell_name = ': ' + ' '.join(commands[2:])
        else:
            spell_name = ''

        used_level = get_int(commands[1], 0)
        if used_level < 0 or used_level > 9:
            return make_response(
                    f'There are no {used_level}-level spells', username=username)

        per_day = contents['spell']['per day']
        lefts = contents['spell']['left']
        if lefts[used_level] <= 0:
            fields = [{'title': 'Spells left',
                       'value': ' / '.join(map(str, lefts))}]
            return make_response(
                    fields, f'No {used_level}-level spells left!', color='danger')
        lefts[used_level] -= 1
        contents['spell']['left'] = lefts
        set_and_commit(character, contents)
        score = lefts[used_level]/per_day[used_level] if per_day[used_level] != 0 else 0
        color = get_color(score)
        fields = [{'title': 'Spells left',
                   'value': ' / '.join(map(str, lefts))}]
        return make_response(
                fields,
                f'{name} casted a {used_level}-level spell{spell_name}', color=color)

    if commands[0] in ('full', 'memorize'):
        if 'spell' not in contents:
            return make_response('Spells should be set first', username=username)
        spells = contents['spell']['left'] = contents['spell']['per day']
        set_and_commit(character, contents)
        fields = [{'title': 'Spells per day',
                   'value': ' / '.join(map(str, spells))},
                  {'title': 'Spells Left',
                   'value': ' / '.join(map(str, spells))}]
        return make_response(fields, f'{name}\'s spell slots are now fully recovered')

    return process_unknown(username)


@app.route('/api/ac', methods=['POST'])
def ac():
    print(request.form)
    msg = request.form['text']
    username = request.form['user_name']
    user_id = request.form['user_id']
    commands = msg.split(' ')
    log.debug(commands)

    character = get_character(username)
    contents = character.get_contents()
    contents['user_id'] = user_id
    if 'user_id' not in contents:
        name = character.name
    else:
        name = f'<@{contents["user_id"]}|{character.name}>'

    if len(commands[0]) == 0:
        ac = contents['ac']['normal'] if 'ac' in contents else 0
        ac_flatfooted = contents['ac']['flatfooted'] if 'ac' in contents else 0
        ac_touch = contents['ac']['touch']

        fields = [{'value': f'{ac}/{ac_flatfooted}/{ac_touch}'}]
        return make_response(fields, f'{name}\'s Current normal/flat-footed/touch AC')

    if len(commands) > 1 and commands[0] == 'set':
        raw_acs = commands[1].split('/')
        acs = list(map(lambda x: get_int(x, 0), raw_acs))[:3]
        contents['ac'] = {'normal': acs[0],
                          'flatfooted': acs[1],
                          'touch': acs[2]}
        set_and_commit(character, contents)
        fields = [{'value': '{}/{}/{}'.format(acs[0], acs[1], acs[2])}]
        return make_response(fields, f'{name}\'s Current normal/flat-footed/touch AC')

    if len(commands) > 1 and commands[0] in ('flat', 'flatfooted', 'flat-footed'):
        if 'ac' not in contents:
            return make_response('Input normal AC first!')

        ac = contents['ac']['normal']
        ac_flatfooted = get_int(commands[1], 0)
        contents['ac']['flatfooted'] = ac_flatfooted
        ac_touch = contents['ac']['touch']
        set_and_commit(character, contents)
        fields = [{'value': f'{ac}/{ac_flatfooted}/{ac_touch}'}]
        return make_response(fields, f'{name}\'s Current normal/flat-footed/touch AC')

    if len(commands) > 1 and commands[0] in ('touch', 'touched'):
        if 'ac' not in contents:
            return make_response('Input normal AC first!')
        ac = contents['ac']['normal']
        ac_flatfooted = contents['ac']['flatfooted']
        ac_touch = get_int(commands[1], 0)
        contents['ac']['touch'] = ac_touch
        set_and_commit(character, contents)
        fields = [{'value': f'{ac}/{ac_flatfooted}/{ac_touch}'}]
        return make_response(fields, f'{name}\'s Current normal/flat-footed/touch AC')

    if commands[0] in ('party', 'all'):
        characters = db.session.query(Character).all()

        fields = []
        for character in characters:
            contents = character.get_contents()
            if 'ac' in contents:
                ac = contents['ac']['normal']
                ac_flatfooted = contents['ac']['flatfooted']
                ac_touch = contents['ac']['touch']
                formatted = '{}/{}/{}'.format(ac, ac_flatfooted, ac_touch)
            else:
                continue
            field = {'title': character.name,
                     'value': formatted,
                     'short': True}
            fields.append(field)

        return make_response(fields, 'Party AC (normal/flat-footed/touch)')

    ac = get_int(commands[0], 0)

    if 'ac' in contents:
        contents['ac']['normal'] = ac
        ac_flatfooted = contents['ac']['flatfooted']
        ac_touch = contents['ac']['touch']
    else:
        contents['ac'] = {
                'normal': ac,
                'flatfooted': ac,
                'touch': ac}
        ac_flatfooted = ac
        ac_touch = ac
    set_and_commit(character, contents)

    fields = [{'value': f'{ac}/{ac_flatfooted}/{ac_touch}'}]
    return make_response(fields, f'{name}\'s Current AC (normal/flat-footed/touch)')


@app.route('/api/init', methods=['POST'])
def init():
    print(request.form)
    msg = request.form['text']

    username = request.form['user_name']
    user_id = request.form['user_id']
    commands = msg.split(' ')

    character = get_character(username)
    contents = character.get_contents()
    contents['user_id'] = user_id
    if 'user_id' not in contents:
        name = character.name
    else:
        name = f'<@{contents["user_id"]}|{character.name}>'

    if len(commands[0]) == 0 or commands[0] == 'roll' or commands[0][0] in ('+', '-'):
        if len(commands[0]) > 0 and commands[0][0] in ('+', '-'):
            init_mod = get_int(commands[0], 0)
        else:
            init_mod = int(contents.get('init_mod', 0))
        title = '{} rolls 1d20 {}'.format(name, modifier(init_mod))
        roll = random.randint(1, 20)
        last_init = roll + init_mod
        fields = [{'title': 'Rolls',
                   'value': f'{roll}',
                   'short': True},
                  {'title': 'Result',
                   'value': f'{last_init}',
                   'short': True}]
        contents['last_init'] = last_init
        set_and_commit(character, contents)
        color = get_color(roll/20)
        return make_response(fields, title, color=color)

    if len(commands) > 1 and commands[0] == 'mod':
        init_mod = get_int(commands[1], 0)
        contents['init_mod'] = init_mod
        set_and_commit(character, contents)
        fields = [{'value': signed(init_mod)}]
        return make_response(fields, f'{name}\'s Initiative modifier')

    if commands[0] == 'set':
        if len(commands) > 1:
            last_init = get_int(commands[1], 0)
            contents['last_init'] = last_init
        set_and_commit(character, contents)
        fields = [{'value': str(last_init)}]
        return make_response(fields, f'{name}\'s Initiative value')

    if commands[0] in ('party', 'all'):
        characters = db.session.query(Character).all()

        char_inits = []
        for character in characters:
            contents = character.get_contents()
            if 'last_init' in contents:
                last_init = int(contents['last_init'])
                if 'user_id' not in contents:
                    name = character.name
                else:
                    name = f'<@{contents["user_id"]}|{character.name}>'
                char_inits.append((name, last_init))
        sorted_inits = sorted(char_inits, key=lambda tup: tup[1], reverse=True)

        merged_inits = [f'{name} ({init})' for name, init in sorted_inits]
        formatted_inits = ' > '.join(merged_inits)

        fields = [{'value': formatted_inits}]
        return make_response(fields, 'Round initiatives')
    if commands[0] in ('CLEAR', 'REMOVE'):
        if 'last_init' in contents:
            del(contents['last_init'])
            character.set_contents(contents)
            db.session.add(character)
        db.session.commit()
        return make_response('Your initiative is removed')

    if commands[0] in ('ALLCLEAR', 'ALLREMOVE', 'CLEARALL', 'REMOVEALL'):
        characters = db.session.query(Character).all()
        for character in characters:
            contents = character.get_contents()
            if 'last_init' in contents:
                del(contents['last_init'])
                character.set_contents(contents)
                db.session.add(character)
        db.session.commit()
        return make_response('All initiatives are removed')

    return process_unknown(username)


@app.route('/api/hp', methods=['POST'])
def hp():
    print(request.form)
    msg = request.form['text']
    username = request.form['user_name']
    user_id = request.form['user_id']
    commands = msg.split(' ')
    log.debug(commands)

    character = get_character(username)
    contents = character.get_contents()
    contents['user_id'] = user_id
    if 'user_id' not in contents:
        name = character.name
    else:
        name = f'<@{contents["user_id"]}|{character.name}>'

    if len(commands[0]) == 0:
        hp = contents.get('hp', 0)
        max_hp = contents.get('max_hp', 0)
        fields = [{'value': f'{hp}/{max_hp}'}]
        score = hp/max_hp if max_hp > 0 else 0
        return make_response(fields, f'{name}\'s Current HP', color=get_color(score))

    if commands[0] == 'party' or commands[0] == 'all':
        characters = db.session.query(Character).all()

        ratios = []
        fields = []
        for character in characters:
            contents = character.get_contents()
            if 'hp' in contents:
                hp = str(contents['hp'])
                max_hp = str(contents.get('max_hp', hp))
                name = character.name
                field = {'title': name,
                         'value': '{}/{}'.format(hp, max_hp),
                         'short': True}
                score = int(hp)/int(max_hp) if int(max_hp) != 0 else 1.0
                ratios.append(score)
                fields.append(field)
        score = sum(ratios)/len(ratios) if len(ratios) > 0 else 0
        return make_response(fields, color=get_color(score))

    if commands[0] in ('party_simple', 'simple', 'allsimple', 'all_simple'):
        characters = db.session.query(Character).all()

        msgs = []
        for character in characters:
            contents = character.get_contents()
            if 'hp' in contents:
                hp = str(contents['hp'])
                max_hp = str(contents.get('max_hp', hp))
                msgs.append(f'@{character.name} : {hp}/{max_hp}')
        msg = '\n'.join(msgs)
        return make_response(msg)

    if commands[0] == 'max':
        if len(commands) > 1:
            if commands[1][0] in ('+', '-') and 'max_hp' in contents:
                max_hp = get_int(commands[1], 0) + contents['max_hp']
            else:
                max_hp = get_int(commands[1], 0)
            hp = contents.get('hp', max_hp)
            contents['max_hp'] = max_hp
            contents['hp'] = hp
            set_and_commit(character, contents)
        else:
            max_hp = contents.get('max_hp', 0)
            hp = contents.get('hp', max_hp)
        fields = [{'value': f'{hp}/{max_hp}'}]
        score = hp/max_hp if max_hp > 0 else 0
        return make_response(fields, f'{name}\'s Current HP', color=get_color(score))

    if commands[0] == 'full':
        max_hp = int(contents['max_hp'])
        hp = max_hp
        contents['hp'] = hp
        set_and_commit(character, contents)

        fields = [{'value': f'{hp}/{max_hp}'}]
        return make_response(fields, f'{name}\'s Current HP', color=get_color(hp/max_hp))

    if commands[0] in ('REMOVE', 'CLEAR'):
        if len(commands) > 1:
            target = commands[1].replace('@', '')
            character = get_character(target)
            contents = character.get_contents()
        if 'max_hp' in contents:
            del(contents['max_hp'])
        if 'hp' in contents:
            del(contents['hp'])
        set_and_commit(character, contents)
        return make_response('HP removed')

    hp = get_int(commands[0], 0)

    current_hp = int(contents.get('hp', hp))
    max_hp = contents.get('max_hp', current_hp)

    if commands[0].startswith('+') or commands[0].startswith('-'):
        current_hp += hp
    else:
        current_hp = hp
    #current_hp = min(current_hp, max_hp)
    #current_hp = max(-10, current_hp)
    contents['hp'] = current_hp
    contents['max_hp'] = max_hp
    set_and_commit(character, contents)
    score = current_hp/max_hp if max_hp != 0 else 1
    color = get_color(score)
    fields = [{'value': f'{current_hp}/{max_hp}'}]
    return make_response(fields, 'Current HP', color=color)


def process_unknown(username):
    emojis = (':grinning:',
              ':frowning:',
              ':astonished:',
              ':unamused:',
              ':sunglasses:',
              ':mask:',
              ':sleeping:',
              ':triumph:',
              ':innocent:')
    emoji = random.choice(emojis)
    if random.randint(0, 3) == 0:
        emoji = ''

    if random.randint(0, 1) == 0:
        characters = db.session.query(Character).all()
        character = random.choice(characters)
        character_scripts = (
            '피해라요 {} 의 공격이다요',
            '그게 무슨 {} 같은 소리다요',
            '그건 {} 에게 말하면 된다요...?',
            '어째서.. {} ...다요?',
            '{} ! 일어나라요! 죽었어...?',
            '{} ! 일어나라요! 아침이다요?',
            '{} ! 어째서다요!',
            '{} 의 파워어택이다요! 효과는 굉장했다요..?')
        script = random.choice(character_scripts)
        return make_response(
                '{} {}'.format(script.format(f'@{character.name}'), emoji), username=username)
    else:
        scripts = (
            '그렇다요',
            '내일 날씨는 맑음이다요 거짓말이다요',
            '알고있다요',
            '무슨말이다요?',
            '무슨 말 하고 있는건지 모르겠다요',
            '닉시코는 그런거 모른다요..',
            '알았다요',
            '아 미안하다요 잠깐 졸았다요')
        script = random.choice(scripts)
        return make_response(f'{script} {emoji}', username=username)


@app.route('/api', methods=['POST'])
def api():
    print(request.form)
    # msg = request.form['text']
    username = request.form['user_name']
    return process_unknown(username)


def make_response(msg, title=None, color=BLUE, username=None):
    if type(msg) == list:
        raw_data = {'response_type': 'in_channel',
                    'attachments': [{'title': title,
                                     'color': color,
                                     'fields': msg}]}
    else:
        if username and msg:
            msg = f'@{username} {msg}'
        raw_data = {'response_type': 'in_channel',
                    'text': msg}

    encoded = json.dumps(raw_data)
    log.info(encoded)
    resp = Response(encoded, content_type='application/json')

    return resp


if __name__ == '__main__':
    app.run(port=20000, debug=True)
