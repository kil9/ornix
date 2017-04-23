import json
import requests
import random
from flask import render_template
from flask import Flask
from flask import request

app = Flask(__name__)

URL='https://hooks.slack.com/services/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'


@app.route('/')
def main():
    return render_template('index.html')

@app.route('/event', methods=['POST'])
def event():
    token = request.form['body']['challenge']
    return token

@app.route('/api', methods=['POST'])
def api():
    msg = request.form['text']

    headers = {'Content-type': 'application/json'}
    raw_data = {"text": msg}
    encoded = json.dumps(raw_data)
    requests.post(URL, headers=headers, data=encoded)

    return ''

if __name__ == '__main__':
    app.run(port=20000, debug=True)
