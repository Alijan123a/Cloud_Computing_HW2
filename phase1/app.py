from flask import Flask, request, jsonify
# from dotenv import load_dotenv
import requests
import redis
import os
from datetime import datetime
import json
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST



# load_dotenv()

class Config:
    API_KEY = os.getenv('API_NINJA_KEY',"7yrnhzcTJk3vFd07nzSROA==vRxkEynraZ3Flbyn")
    BASE_URL = os.getenv('BASE_URL','https://api.api-ninjas.com/v1')
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_CACHE_DURATION = int(os.getenv('REDIS_CACHE_DURATION', 300))
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))






app = Flask(__name__)
config = Config()
print(config.API_KEY)
print(config.REDIS_CACHE_DURATION)
cache = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)



REQUEST_COUNT = Counter('api_requests_total', 'Total API Requests', ['endpoint', 'method'])
CACHE_HITS = Counter('cache_hits_total', 'Total Cache Hits', ['endpoint'])
CACHE_MISSES = Counter('cache_misses_total', 'Total Cache Misses', ['endpoint'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency in seconds', ['endpoint'])

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
    endpoint = '/define'
    REQUEST_COUNT.labels(endpoint=endpoint, method='POST').inc()
    start_time = datetime.now()

    word = None
    if args:
        word = args[0]
    else:
        word = request.form["word"]
    if not word:
        return jsonify({"error": "No word provided"}), 400

    # GET DATA FROM CACHE
    print("word:",word)
    cached = cache.get(word)
    print(cached)
    if cached:
        CACHE_HITS.labels(endpoint=endpoint).inc()
        data = json.loads(cached)
        REQUEST_LATENCY.labels(endpoint=endpoint).observe((datetime.now() - start_time).total_seconds())
        return jsonify({
            "word": word,
            "definition": data['definition'], 
            "isCached": "TRUE",
            "time": data['time']
        })


    # GET DATA FROM URL
    CACHE_MISSES.labels(endpoint=endpoint).inc()
    headers = {'X-Api-Key': config.API_KEY}
    response = requests.get(f"{config.BASE_URL}/dictionary?word={word}", headers=headers)

    if response.status_code == 200:
        definition = response.json().get("definition", "No definition found")
        save_to_cach(word, definition)
        REQUEST_LATENCY.labels(endpoint=endpoint).observe((datetime.now() - start_time).total_seconds())
        return jsonify({
            "word": word,
            "definition": definition,
            "isCached":"FALSE"
        })
    
    else:
        REQUEST_LATENCY.labels(endpoint=endpoint).observe((datetime.now() - start_time).total_seconds())
        return jsonify({"error": "Failed to retrieve definition"}), 500


@app.route('/randomword', methods=['GET'])
def random_word():
    print("random")
    endpoint = '/randomword'
    REQUEST_COUNT.labels(endpoint=endpoint, method='GET').inc()
    start_time = datetime.now()

    headers = {'X-Api-Key': config.API_KEY}
    print(config.API_KEY)
    response = requests.get(f"{config.BASE_URL}/randomword", headers=headers)

    if response.status_code == 200:
        word = response.json().get("word")
        REQUEST_LATENCY.labels(endpoint=endpoint).observe((datetime.now() - start_time).total_seconds())
        return define_word(word[0])
    else:
        REQUEST_LATENCY.labels(endpoint=endpoint).observe((datetime.now() - start_time).total_seconds())
        return jsonify({"error": "Failed to retrieve random word"}), 500
    

@app.route('/metrics', methods=['GET'])
def metrics():
    data = generate_latest()
    print("req_count(1:): ",REQUEST_COUNT)
    print("req_lat(::): ",REQUEST_LATENCY)
    # print("cach_hit: ",CACHE_HITS)
    return data, 200, {'Content-Type': CONTENT_TYPE_LATEST}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.FLASK_PORT)
