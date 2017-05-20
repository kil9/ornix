import collections
import math
import random
import re

Token = collections.namedtuple('Token', ['type', 'value', 'd'])


def tokenize(code):
    token_specification = [
            ('DICE', r'(?P<dnum>\d*)[d|D](?P<dtype>[\d|%]+)'),
            ('NUM', r'(\d*\.*\d+)'),
            ('ADD', r'\+'),
            ('SUB', r'\-'),
            ('MUL', r'\*'),
            ('SPLIT', r'\/'),
            ('SKIP', r'[ \t]+'),
            ('MISMATCH', r'.'),
    ]

    tok_regex = '|'.join('(?P<{}>{})'.format(key, value) for key, value in token_specification)

    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group(kind)
        d = mo.groupdict()
        if kind == 'SKIP':
            pass
        elif kind == 'MISMATCH':
            # raise RuntimeError(f'{value!r} unexpected')
            yield Token('DICE', '1d20', {'dnum': '1', 'dtype': '20'})
        else:
            yield Token(kind, value, d)


def parse_dice(dice_str):
    tokens = tokenize(dice_str)
    fields = []
    evaluates = []
    evaluated = []
    calculated = ''
    results = []
    field = []
    scores = []
    token_before = None
    for token in tokens:
        if token.type == 'DICE':
            if len(evaluated) > 10:
                break
            if token_before and token_before.type not in ('ADD', 'SUB', 'MUL'):
                fields.append(' '.join(field))
                field = []
                results.append(calculated)
                calculated = ''
                evaluated.append(evaluates)
                evaluates = []
            if len(token.d['dnum']) > 0:
                dnum = max(1, min(100, int(token.d['dnum'])))
            else:
                dnum = 1
            if token.d['dtype'].startswith('%'):
                dtype = 100
            else:
                dtype = max(1, min(100, int(token.d['dtype'])))
            rolls = [random.randint(1, dtype) for i in range(dnum)]
            scores.append(sum(rolls)/len(rolls)/dtype)
            evaluates += rolls
            calculated += str(sum(rolls))
            field.append(f'{dnum}d{dtype}')
        elif token.type == 'NUM':
            if token_before and token_before.type not in ('ADD', 'SUB', 'MUL'):
                results.append(calculated)
                calculated = ''
            field.append(token.value)
            calculated += str(token.value)
        elif token.type in ('ADD', 'SUB', 'MUL'):
            field.append(token.value)
            calculated += str(token.value)
        token_before = token
    fields.append(' '.join(field))
    results.append(calculated)
    results = list(map(math.floor, map(eval, results)))
    evaluated.append(evaluates)
    evaluates = []
    score = sum(scores)/len(scores) if len(scores) > 0 else 1
    return fields, evaluated, results, score


if __name__ == '__main__':
    print(parse_dice("2d6 * 1.5"))
    print(parse_dice("2d6"))
    print(parse_dice("1d20"))
    print(parse_dice("1d2008989"))
    print(parse_dice("2"))
    print(parse_dice("2+3 + 4 1d6"))
    print(parse_dice("d%"))
    print(parse_dice("2d%"))
    print(parse_dice("1d20+3"))
    print(parse_dice("1d4+1 1d4+1"))
    print(parse_dice("1d4+2d6+1/1d4+1"))
    print(parse_dice("1d4+1 / 1d4+1"))
    print(parse_dice("1d4+1+."))
