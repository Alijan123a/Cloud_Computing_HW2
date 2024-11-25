from flask import Flask, request, jsonify
import requests
import redis

app = Flask(__name__)
cache = redis.StrictRedis(host='redis', port=6379, db=0)

API_KEY = "7yrnhzcTJk3vFd07nzSROA==vRxkEynraZ3Flbyn"
BASE_URL = "https://api.api-ninjas.com/v1"

@app.route('/define', methods=['GET'])
def define_word():
    word = request.args.get('word')
    if not word:
        return jsonify({"error": "No word provided"}), 400

    cached_definition = cache.get(word)
    if cached_definition:
        return jsonify({"word": word, "definition": cached_definition.decode("utf-8")})

    headers = {'X-Api-Key': API_KEY}
    response = requests.get(f"{BASE_URL}/dictionary?word={word}", headers=headers)
    if response.status_code == 200:
        definition = response.json().get("definition", "No definition found")
        cache.setex(word, 300, definition)
        return jsonify({"word": word, "definition": definition})
    else:
        return jsonify({"error": "Failed to retrieve definition"}), 500


@app.route('/randomword', methods=['GET'])
def random_word():
    headers = {'X-Api-Key': API_KEY}
    response = requests.get(f"{BASE_URL}/randomword", headers=headers)
    if response.status_code == 200:
        word = response.json().get("word")
        return define_word()
    else:
        return jsonify({"error": "Failed to retrieve random word"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
