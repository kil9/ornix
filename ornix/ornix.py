import json
import random
from flask import render_template
from flask import Flask

app = Flask(__name__)

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/api', methods=['POST'])
def api():
    msg = { "attachments": [ {
                "title": "닉시코",
                "pretext": "포맷이 복잡해서",
                "text": "다이스 *귀찮고*",
                "mrkdwn_in": [ "text", "pretext" ] } ] }
    encoded = json.dumps(msg)
    return encoded

if __name__ == '__main__':
    app.run(port=20000, debug=True)
