import json
import requests
import random
from flask import render_template
from flask import Flask
from flask import request
from flask import Response

app = Flask(__name__)

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/api', methods=['POST'])
def api():
    print(request.form)
    msg = request.form['text']
    username = request.form['user_name']

    '''
    raw_data = {
            "response_type": "in_channel",
            "text": '@' + username + ': ' + msg,
            "attachments": [
                { "text": '2d4+2' },
                {"fields": [
                    {
                        "title": "Roll",
                        "value": "2 4",
                        "short": True
                        },
                    {
                        "title": "Result",
                        "value": "8",
                        "short": True
                        }
                    ]
                    }
                ]
            }
            '''
    raw_data = {
            "response_type": "in_channel",
            "text": '@' + username + ' ' + msg,
            }

    encoded = json.dumps(raw_data)
    resp = Response(encoded, content_type='application/json')

    return resp

if __name__ == '__main__':
    app.run(port=20000, debug=True)
