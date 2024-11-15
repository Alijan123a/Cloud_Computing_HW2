from flask import Flask, request, jsonify
import requests
import redis

app = Flask(__name__)
cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

API_KEY = "7yrnhzcTJk3vFd07nzSROA==vRxkEynraZ3Flbyn"
BASE_URL = "https://api.api-ninjas.com/v1"

@app.route('/define', methods=['POST'])
def define_word(*args):
    word = None
    if args:
        word = args[0]
    else:
        word = request.form["word"]
    
    if not word:
        return jsonify({"error": "No word provided"}), 400

    print(word)
    cached_definition = cache.get(word)
    if cached_definition:
        print(cached_definition)
        return jsonify({"word": word, "definition(cached)": cached_definition})

    headers = {'X-Api-Key': API_KEY}
    response = requests.get(f"{BASE_URL}/dictionary?word={word}", headers=headers)
    if response.status_code == 200:
        definition = response.json().get("definition", "No definition found")
        cache.setex(word, 300, definition)
        return jsonify({"word": word, "definition(url)": definition})
    else:
        return jsonify({"error": "Failed to retrieve definition"}), 500


@app.route('/randomword', methods=['GET'])
def random_word():
    headers = {'X-Api-Key': API_KEY}
    response = requests.get(f"{BASE_URL}/randomword", headers=headers)
    if response.status_code == 200:
        print(response.json())
        word = response.json().get("word")
        return define_word(word[0])
    else:
        return jsonify({"error": "Failed to retrieve random word"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
