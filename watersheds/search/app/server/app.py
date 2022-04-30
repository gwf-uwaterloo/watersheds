from flask import Flask, request, jsonify
from flask_cors import CORS

import sys
sys.path.insert(1, '../../..')

from _base import Basin, River
from search.search import search_river


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

basin = Basin()
river = River()

@app.route("/", methods=['POST', 'GET'])
def rivers_search():
  if request.method == 'POST':
    req = request.json
    results = search_river(req['searchText'], basin, river)
    return jsonify(results)
  
  elif request.method == 'GET':
    return "This is the endpoint for geo search."

@app.route('/test/')
def hello():
  return '<h1>Hello, World!</h1>'
  