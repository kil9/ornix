import re
import random

regex_dice = re.compile('(?P<num>\d*)[d|D](?P<type>[\d|%]+)')

def calculate_dice(dices_str):
    dice_strs = re.split('[ \t\/]+', dices_str)
    result = []
    fields = []
    scores = []
    for dice_str in dice_strs:
        dices, fields_added, scores_added = parse_dice(dice_str)
        fields += fields_added
        scores += (scores_added)
        result.append(dices)
    score = sum(scores)/len(scores) if len(scores) > 0 else 1
    return list(map(eval, result)), fields, score

def parse_dice(dices):
    scores = []
    fields = []
    while True:
        matched = regex_dice.search(dices)
        if matched is None:
            fields.append({'title': 'Result',
                           'value': int(eval(dices)),
                           'short': True })
            break
        dice = matched.groupdict()
        dice['num'] = 1 if len(dice['num']) == 0 else int(dice['num'])
        dice['type'] = 100 if dice['type'].startswith('%') else int(dice['type'])

        rolls = []
        for i in range(dice['num']):
            roll = random.randint(1, dice['type'])
            scores.append(roll / dice['type'])
            rolls.append(roll)

        fields.append({'title': 'Rolls ({})'.format(matched[0]),
                       'value': ' '.join(map(str, rolls)),
                       'short': True })
        dices = dices.replace(matched[0], str(sum(rolls)))
    return dices, fields, scores
