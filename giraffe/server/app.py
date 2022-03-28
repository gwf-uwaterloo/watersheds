from flask import Flask, request, jsonify
from flask_cors import CORS

import sys
# sys.path.insert(1, '../../pyserini')
# sys.path.insert(1, '../../watersheds')

from watersheds._base import Basin
from watersheds.search import get_geometries

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

basin = Basin()

@app.route("/", methods=['POST', 'GET'])
def rivers_search():
  if request.method == 'POST':
    req = request.json
    results = get_geometries(req['searchText'])
    return jsonify(results)
  
  elif request.method == 'GET':
    return "This is the endpoint for geo search."
