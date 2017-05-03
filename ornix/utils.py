from config import db

BLUE = '#439FE0'


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


def get_int(n, default):
    try:
        return int(n)
    except ValueError:
        return default


def get_color(score):
    if score > 0.8:
        return 'good'
    elif score > 0.3:
        return 'warning'
    else:
        return 'danger'


def set_and_commit(character, contents):
    character.set_contents(contents)
    db.session.add(character)
    db.session.commit()
