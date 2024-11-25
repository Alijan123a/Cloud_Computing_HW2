from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import redis
import os
from datetime import datetime
import json


load_dotenv()

class Config:
    API_KEY = os.getenv('API_NINJA_KEY')
    BASE_URL = 'https://api.api-ninjas.com/v1'
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_CACHE_DURATION = int(os.getenv('REDIS_CACHE_DURATION', 300))
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))


app = Flask(__name__)
config = Config()
print(config.API_KEY)
print(config.REDIS_CACHE_DURATION)
cache = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

# API_KEY = "7yrnhzcTJk3vFd07nzSROA==vRxkEynraZ3Flbyn"
# BASE_URL = "https://api.api-ninjas.com/v1"


def save_to_cach(word, definition):
    data = {
        "definition" : definition,
        "time" :  datetime.now().isoformat()
    }
    cache.setex(word, config.REDIS_CACHE_DURATION, json.dumps(data))


@app.route('/define', methods=['POST'])
def define_word(*args):
    # print("define")
    word = None
    if args:
        word = args[0]
    else:
        word = request.form["word"]
    if not word:
        return jsonify({"error": "No word provided"}), 400

    # GET DATA FROM CACHE
    cached = cache.get(word)
    print(cached)
    if cached:
        data = json.loads(cached)
        return jsonify({
            "word": word,
            "definition": data['definition'], 
            "isCached": "TRUE",
            "time": data['time']
        })


    # GET DATA FROM URL
    headers = {'X-Api-Key': config.API_KEY}
    response = requests.get(f"{config.BASE_URL}/dictionary?word={word}", headers=headers)

    if response.status_code == 200:
        definition = response.json().get("definition", "No definition found")
        save_to_cach(word, definition)
        return jsonify({
            "word": word,
            "definition": definition,
            "isCached":"FALSE"
        })
    
    else:
        return jsonify({"error": "Failed to retrieve definition"}), 500


@app.route('/randomword', methods=['GET'])
def random_word():
    print("random")
    headers = {'X-Api-Key': config.API_KEY}
    print(config.API_KEY)
    response = requests.get(f"{config.BASE_URL}/randomword", headers=headers)
    if response.status_code == 200:
        word = response.json().get("word")
        return define_word(word[0])
    else:
        return jsonify({"error": "Failed to retrieve random word"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.FLASK_PORT)
