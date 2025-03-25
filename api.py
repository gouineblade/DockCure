from flask import Flask, jsonify, request, abort, redirect, send_file
from flask_cors import CORS 
from flasgger import Swagger
import time
import subprocess
import json
import os
import threading
import re
from packaging.version import Version, InvalidVersion


swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

template = {
    "swagger": "2.0",
    "info": {
        "title": "🛡️ CVE Auto-Fix API",
        "description": "Scan, analyse et corrige automatiquement les images Docker vulnérables.",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": ["http"],
}

app = Flask(__name__)

CORS(app)
Swagger(app, config=swagger_config, template=template)
db_scan_results = {}  # Dictionnaire pour stocker les résultats des scans

# Route racine qui génère la documentation automatique des endpoints
@app.route('/')
def index():
  #redirige vers la documentation
  return redirect('/apidocs/')

def detect_package_manager(image_name):
  """Détecte le type de gestionnaire de paquets utilisé dans une image Docker"""
  try:
      cmd = f"docker run --rm {image_name} cat /etc/os-release"
      result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
      content = result.stdout.lower()

      if "alpine" in content:
          return "apk"
      elif "debian" in content or "ubuntu" in content:
          return "apt"
      elif "centos" in content or "fedora" in content or "rhel" in content:
          return "yum"
      else:
          return "unknown"
  except Exception as e:
      log(f"Erreur lors de la détection de l'OS: {e}")
      return "unknown"


# Vérifier si une version spécifique d'un package est disponible
def is_version_available(package, version):
    cmd = f"apt-cache madison {package} | grep '{version}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return bool(result.stdout.strip())

# Générer dynamiquement un Dockerfile sécurisé
def generate_secure_dockerfile(base_image, packages):
    os.makedirs("images/tmp", exist_ok=True)
    dockerfile_path = "images/tmp/Dockerfile.secure"

    pm = detect_package_manager(base_image)
    log(f"🧠 Gestionnaire de paquets détecté pour {base_image} : {pm}")

    with open(dockerfile_path, "w") as f:
        f.write(f"FROM {base_image}\n")

        if pm == "apt":
            f.write("RUN apt-get update && \\\n")
            commands = []
            for pkg in packages:
                name = pkg.get("libname")
                action = pkg.get("action")
                if action == "remove":
                    commands.append(f"apt-get remove -y {name}")
                elif action.startswith("upgrade"):
                    if action == "upgrade":
                        commands.append(f"apt-get install -y --only-upgrade {name}")
                    else:
                        version = action.split("_")[-1]
                        if is_version_available(name, version):
                            commands.append(f"apt-get install -y {name}={version}")
                else:
                    log(f"Action inconnue pour {name}: {action}")
            if not commands:
                commands.append("echo 'Aucune mise à jour requise'")
            commands.append("apt-get clean")
            f.write(" && \\\n".join(commands) + "\n")

        elif pm == "apk":
            f.write("RUN apk update && \\\n")
            commands = []
            for pkg in packages:
                name = pkg.get("libname")
                action = pkg.get("action")
                if action == "remove":
                    commands.append(f"apk del {name}")
                elif action.startswith("upgrade"):
                    # APK ne permet pas des upgrades ciblés par version facilement
                    commands.append(f"apk add --upgrade {name}")
                else:
                    log(f"Action inconnue pour {name}: {action}")
            if not commands:
                commands.append("echo 'Aucune mise à jour requise'")
            f.write(" && \\\n".join(commands) + "\n")

        elif pm == "yum":
            f.write("RUN yum update -y && \\\n")
            commands = []
            for pkg in packages:
                name = pkg.get("libname")
                action = pkg.get("action")
                if action == "remove":
                    commands.append(f"yum remove -y {name}")
                elif action.startswith("upgrade"):
                    commands.append(f"yum update -y {name}")
                else:
                    log(f"Action inconnue pour {name}: {action}")
            if not commands:
                commands.append("echo 'Aucune mise à jour requise'")
            f.write(" && \\\n".join(commands) + "\n")

        else:
            f.write("RUN echo '⚠️ Gestionnaire de paquets non reconnu. Aucun correctif appliqué.'\n")

    return f"Dockerfile sécurisé généré avec succès pour base {base_image} (PM: {pm})"


# Construire une image sécurisée
def build_secure_image(name):
    log("🚀 Construction de l'image sécurisée...")
    cmd = f"docker build --rm -t {name} -f images/tmp/Dockerfile.secure ."
    subprocess.run(cmd, shell=True)
    
    os.makedirs("images", exist_ok=True)
    cmd = f"docker save {name} > images/{name}.tar"
    subprocess.run(cmd, shell=True)
    log(f"✅ Image sécurisée créée : {name}")

@app.route('/autofix', methods=['POST'])
def auto_fix():
    """
    Analyse et génère automatiquement un Dockerfile sécurisé avec les corrections à appliquer.
    ---
    tags:
      - Fix Automatisé
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            image_name:
              type: string
              description: Nom de l'image Docker à analyser et corriger.
    responses:
      200:
        description: Dockerfile sécurisé généré avec succès.
      400:
        description: Paramètre manquant ou erreur d'analyse.
    """
    data = request.get_json()
    image_name = data.get("image_name")
    if not image_name:
        return jsonify({"error": "Paramètre 'image_name' requis"}), 400

    scan_result = db_scan_results.get(image_name)
    if scan_result is None:
        return jsonify({"error": "Aucun scan trouvé pour cette image"}), 404
    if scan_result.get("error"):
        return jsonify({"error": "Une erreur est survenue lors du scan"}), 400
    if "message" in scan_result:
        return jsonify({"error": "Le scan est encore en cours"}), 400

    analysis_data, packages_to_update = analyze_vulnerabilities(scan_result)

    package_list = []
    for pkg, version in packages_to_update.items():
        package_list.append({
            "libname": pkg,
            "action": f"upgrade_{version}"
        })

    # Génération et build
    new_name = image_name + "-secure"
    result = generate_secure_dockerfile(image_name, package_list)
    build_secure_image(new_name)

    return jsonify({
        "status": "success",
        "message": result,
        "secure_image": new_name,
        "download": f"/image/{new_name}",
        "applied_fixes": package_list
    })


@app.route('/fix/', methods=['POST'])
def fix_post():
    """
    Corrige une image Docker en mettant à jour ou en supprimant des paquets.
    ---
    tags:
        - Fix
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            image_name:
              type: string
              description: Nom de l'image Docker à corriger.
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
        image_name = data.get("image_name")
        new_name = data.get("new_name") or image_name + "-secure"
        packages = data.get("packages", []) or []
        
        result = generate_secure_dockerfile(image_name, packages)
        build_secure_image(new_name)
        return jsonify({"status": "success", "message": result, "secure_image": new_name, "download": f"/image/{new_name}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def build_secure_image(name):
    """Construit une nouvelle image sécurisée"""
    log("🚀 Construction de l'image sécurisée...")
    cmd = f"docker build --rm -t {name} -f images/tmp/Dockerfile.secure ."
    subprocess.run(cmd, shell=True)
    #quand c'est fini, on sauvegarde l'image dans le dossier images
    cmd = f"docker save {name} > images/{name}.tar"
    subprocess.run(cmd, shell=True)
    log(f"✅ Image sécurisée créée : {name}")

# Route pour récupérer l'image Docker sécurisée (lance le téléchargement)

@app.route('/image/', methods=['POST'])
def get_image():
    """
    Télécharge une image Docker sécurisée.
    ---
    tags:
        - Image
    parameters:
      - name: image_name
        in: body
        required: true
        schema:
          type: object
          properties:
            image_name:
              type: string
              description: Nom de l'image Docker sécurisée à télécharger.
    responses:
      200:
        description: Téléchargement de l'image Docker sécurisée.
      400:
        description: Requête invalide, entrée incorrecte.
      404:
        description: Image non trouvée.
    """
    if not request.json or "image_name" not in request.json:
        return jsonify({"error": "Paramètre 'image_name' manquant"}), 400

    image_name = request.args.get("image_name")

    image_path = f"images/{image_name}.tar"
    if not os.path.exists(image_path):
        return jsonify({"error": "Image non trouvée"}), 404
    
    return send_file(image_path, as_attachment=True)


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
              example: "nginx"
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
        example: "nginx"
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
              example: "nginx"
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
    """Analyse les vulnérabilités et retourne un tableau des actions mises en place en prenant la dernière version stable."""

    data = {}
    packages_to_update = {}

    for vuln in scan_results["matches"]:
        package = vuln["artifact"]["name"]
        current_version = vuln["artifact"]["version"]  # Version actuelle du package
        vuln_id = vuln["vulnerability"]["id"]
        severity = vuln["vulnerability"]["severity"].lower()  # Normaliser la gravité
        fix_info = vuln["vulnerability"]["fix"]
        purl = vuln["artifact"]["purl"]

        # Vérifier si une correction est disponible
        fixed_version = None
        if fix_info["state"] == "fixed" and fix_info["versions"]:
            # Filtrer les versions pour exclure RC, alpha, beta, preview
            valid_versions = [
                v for v in fix_info["versions"]
                if not re.search(r"(?:-|\.)(?:rc|alpha|beta|preview)", v, re.IGNORECASE)
            ]

            if valid_versions:
                try:
                    fixed_version = max(valid_versions, key=Version)
                    #log(f"Versions valides pour {package}: {valid_versions} | Meilleure: {fixed_version}")
                except InvalidVersion:
                    fixed_version = None  # Gestion des erreurs
                    #log(f"Erreur: Version invalide détectée pour {package}")

        action = f"Mise à jour vers {fixed_version}" if fixed_version else "Aucune correction disponible"

        # Initialiser la structure du package si elle n'existe pas encore
        if package not in data:
            data[package] = {
                "package": package,
                "master_package": purl,
                "version": current_version,
                "cve": {}  # Création d'un dictionnaire dynamique des niveaux de gravité
            }

        # Ajouter la CVE au bon niveau de gravité
        if severity not in data[package]["cve"]:
            data[package]["cve"][severity] = []
        data[package]["cve"][severity].append(vuln_id)

        #log(f"   - {package}: {vuln_id} | Gravité: {severity} | Action: {action}")

        # **Mise à jour du package uniquement si la version est plus récente que l'actuelle**
        if fixed_version:
            if package not in packages_to_update or Version(fixed_version) > Version(packages_to_update[package]):
                packages_to_update[package] = fixed_version

    return list(data.values()), packages_to_update

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