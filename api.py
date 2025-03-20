from flask import Flask, jsonify, request, abort, redirect
from flask_cors import CORS 
from flasgger import Swagger
from datetime import datetime
import os
app = Flask(__name__)

CORS(app)
Swagger(app)

# Route racine qui génère la documentation automatique des endpoints
@app.route('/')
def index():
  #redirige vers la documentation
  return redirect('/apidocs/')

# Route pour scanner une images docker
@app.route('/scan', methods=['POST'])
def scan():
    data = request.json
    image_name = data["image_name"]
    return jsonify({"message": f"Requete bien reçu, Scan de l'image {image_name} en cours..."})




@app.before_request
def block_https():
    if request.is_secure:
        abort(400, description="HTTPS not supported, use HTTP instead.")

@app.before_request
def handle_options_request():
    if request.method == "OPTIONS":
        response = jsonify({'message': 'OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        return response, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=44880, debug=True)