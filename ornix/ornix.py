from flask import render_template
from flask import Flask

app = Flask(__name__)

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/api', methods=['POST'])
def api():
    return 'ok'

if __name__ == '__main__':
    app.run(port=20000, debug=True)
