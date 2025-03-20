from flask import Flask, jsonify, request, abort, redirect
from flask_cors import CORS 
from flasgger import Swagger
import time
import subprocess
import json
import os
import threading

app = Flask(__name__)

CORS(app)
Swagger(app)
db_scan_results = {}  # Dictionnaire pour stocker les résultats des scans

# Route racine qui génère la documentation automatique des endpoints
@app.route('/')
def index():
  #redirige vers la documentation
  return redirect('/apidocs/')

# Fonction pour vérifier si une version spécifique d'un package est disponible
def is_version_available(package, version):
    cmd = f"apt-cache madison {package} | grep '{version}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return bool(result.stdout.strip())

# Fonction pour générer un Dockerfile sécurisé
def generate_secure_dockerfile(image_name, packages):
    with open("Dockerfile.secure", "w") as f:
        f.write(f"FROM {image_name}\n")
        f.write("RUN apt-get update\n")
        
        for pkg in packages:
            libname = pkg["libname"]
            action = pkg["action"]
            
            if action == "remove":
                f.write(f"RUN apt-get remove -y {libname}\n")
            elif action == "upgrade":
                f.write(f"RUN apt-get install -y --only-upgrade {libname}\n")
            elif action.startswith("upgrade_"):
                version = action.split("_")[1]
                if is_version_available(libname, version):
                    f.write(f"RUN apt-get install -y {libname}={version}\n")
                else:
                    f.write(f"# Version {version} not found, using standard upgrade\n")
                    f.write(f"RUN apt-get install -y --only-upgrade {libname}\n")
        
    return "Dockerfile.secure generated"

@app.route('/fix/<image_name>', methods=['POST'])
def fix_post(image_name):
    """
    Corrige une image Docker en mettant à jour ou en supprimant des paquets.
    ---
    tags:
        - Fix
    parameters:
      - name: image_name
        in: path
        type: string
        required: true
        description: Nom de l'image Docker à corriger.
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:  
            new_name:
              type: string
              description: (Optionnel) Nouveau nom pour l'image Docker corrigée.
            packages:
              type: array
              items:
                type: object
                properties:
                  libname:
                    type: string
                    description: Nom du paquet à modifier.
                  action:
                    type: string
                    enum: [remove, upgrade, upgrade_x.x.x]
                    description: Action à effectuer sur le paquet.
    responses:
      200:
        description: Dockerfile.secure généré avec succès.
      400:
        description: Requête invalide, entrée incorrecte.
    """
    try:
        data = request.get_json()
        new_name = data.get("new_name") or image_name + "-secure"
        packages = data.get("packages", [])
        
        result = generate_secure_dockerfile(new_name, packages)
        return jsonify({"status": "success", "message": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Route pour retourner les scans en cours et les scans terminés
@app.route('/scans', methods=['GET'])
def get_scans():
    """Retourne les scans en cours et les scans terminés
    ---
    tags:
      - Scans
    responses:
      200:
        description: Liste des images dans la base de données et leur état (en cours, fini, erreur)
        schema:
          type: object
      400:
        description: Erreur de requête
    """
    scans_en_cours = []
    scans_termines = []
    
    for image_name, result in db_scan_results.items():
        if "error" in result:
            scans_termines.append(image_name)
        elif "message" in result:
            scans_en_cours.append(image_name)
        else:
            scans_termines.append(image_name)
    
    return jsonify({
        "scans_en_cours": scans_en_cours,
        "scans_termines": scans_termines
    })

def scanner_image(image_name):
    """Exécute Grype pour scanner une image Docker"""
    cmd = f"grype {image_name} -o json"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    try:
        scan_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        scan_data = {"error": "Impossible de décoder la sortie JSON"}
    
    db_scan_results[image_name] = scan_data

# Route pour scanner une image Docker
@app.route('/scan', methods=['POST'])
def scan_post():
    """Lance un scan d'image Docker avec Grype
    ---
    tags:
      - Scan Docker
    parameters:
      - name: image_name
        in: body
        required: true
        schema:
          type: object
          properties:
            image_name:
              type: string
              example: "nginx:latest"
    responses:
      200:
        description: Message confirmant le lancement du scan
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Erreur de requête
    """
    data = request.json
    if not data or "image_name" not in data:
        return jsonify({"error": "Paramètre 'image_name' manquant"}), 400
    
    image_name = data["image_name"]
    
    # Lancer le scan dans un thread pour ne pas bloquer la requête
    scan_thread = threading.Thread(target=scanner_image, args=(image_name,))
    scan_thread.start()
    db_scan_results[image_name] = {"message": f"Scan de l'image {image_name} en cours..."}
    return jsonify({"message": f"Requête bien reçue, scan de l'image {image_name} en cours..."})

# Route pour récupérer le résultat du scan d'une image Docker
@app.route('/scan', methods=['GET'])
def scan_get():
    """Récupère le résultat d'un scan d'image Docker
    ---
    tags:
      - Scan Docker
    parameters:
      - name: image_name
        in: query
        type: string
        required: true
        example: "nginx:latest"
    responses:
      200:
        description: Résultat du scan
        schema:
          type: object
      400:
        description: Paramètre manquant
      404:
        description: Aucun scan trouvé
    """
    image_name = request.args.get("image_name")
    if not image_name:
        return jsonify({"error": "Paramètre 'image_name' requis"}), 400
    
    scan_result = db_scan_results.get(image_name)
    if scan_result is None:
        return jsonify({"message": "Aucun scan trouvé pour cette image ou le scan est encore en cours"}), 404
    
    return jsonify(scan_result)

# Route pour analyser les vulnérabilités d'un scan
@app.route('/analyze', methods=['POST'])
def analyze_post():
    """Analyse les vulnérabilités d'un scan d'image Docker
    ---
    tags:
      - Analyse de vulnérabilités
    parameters:
      - name: image_name
        in: body
        required: true
        schema:
          type: object
          properties:
            image_name:
              type: string
              example: "nginx:latest"
    responses:
      200:
        description: Résultat de l'analyse
        schema:
          type: object
      400:
        description: Erreur de requête
    """
    data = request.json
    if not data or "image_name" not in data:
        return jsonify({"error": "Paramètre 'image_name' manquant"}), 400
    
    image_name = data["image_name"]
    scan_result = db_scan_results.get(image_name)
    if scan_result is None:
        return jsonify({"error": "Aucun scan trouvé pour cette image"}), 404
    if scan_result.get("error"):
        return jsonify({"error": "Une erreur est survenue lors du scan"}), 400
    if "message" in scan_result:
        return jsonify({"error": "Le scan de cette image est encore en cours"}), 400
    analysis_data, packages_to_update = analyze_vulnerabilities(scan_result)
    return jsonify({"analysis": analysis_data, "packages_to_update": packages_to_update})

def analyze_vulnerabilities(scan_results):
    """Analyse les vulnérabilités et retourne un tableau des actions mises en place"""

    data = []
    packages_to_update = {}

    for vuln in scan_results["matches"]:
        package = vuln["artifact"]["name"]
        vuln_id = vuln["vulnerability"]["id"]
        severity = vuln["vulnerability"]["severity"]
        fix_info = vuln["vulnerability"]["fix"]

        # Vérifier si une correction est disponible
        if fix_info["state"] == "fixed" and fix_info["versions"]:
            fixed_version = fix_info["versions"][0]  # Prendre la première version corrigée
            action = f"Mise à jour vers {fixed_version}"
            packages_to_update[package] = fixed_version
        else:
            action = "Aucune correction disponible"

        log(f"   - {package}: {vuln_id} | Gravité: {severity} | Action: {action}")
        data.append([package, vuln_id, severity, action])

    return data, packages_to_update


def log(message):
    """Affiche un message avec un timestamp"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")


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