from flask import Flask, jsonify, request
import random
import firebase_admin
from firebase_admin import credentials, firestore
from auth import token_obrigatorio, gerar_token
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# CORS corrigido para aceitar local e produção
CORS(app, resources={r"/*": {
    "origins": [
        "https://academia-catraca.vercel.app", 
        "https://secretaria-academia.vercel.app",
        "http://127.0.0.1:5500", # Para testes locais com Live Server
        "http://localhost:5500"
    ]
}})

# Inicialização Firebase (Mantida a sua lógica)
if os.getenv("VERCEL"):
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
else:
    cred = credentials.Certificate("firebase.json")
    
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- ROTAS DE BUSCA ---

@app.route("/clientes", methods=['GET'])
def get_clientes():
    clientes = [item.to_dict() for item in db.collection('clientes').stream()]
    return jsonify(clientes), 200

@app.route("/clientes/<int:id>", methods=['GET'])
def get_cliente_by_id(id):
    # O Firestore 'where' precisa que o tipo do dado seja idêntico ao do BD
    docs = db.collection('clientes').where('id', '==', id).get()
    if not docs:
        return jsonify({"error": "Cliente não encontrado"}), 404
    return jsonify(docs[0].to_dict()), 200

@app.route("/clientes/cpf/<string:cpf>", methods=['GET'])
def get_cliente_by_cpf(cpf):
    # Garantimos que a busca seja feita como string
    docs = db.collection('clientes').where('cpf', '==', str(cpf)).get()
    if not docs:
        return jsonify({"error": "CPF não cadastrado"}), 404
    return jsonify(docs[0].to_dict()), 200

# --- ROTAS DE ESCRITA (COM TOKEN) ---

@app.route("/clientes", methods=['POST'])
@token_obrigatorio
def post_clientes():
    dados = request.get_json()
    if not all(k in dados for k in ("nome", "cpf", "autorizado")):
        return jsonify({"error": "Dados incompletos"}), 400
    
    try:
        contador_ref = db.collection('contador').document('controle_id')
        doc = contador_ref.get()
        
        # Se o contador não existir, ele começa do 0
        novo_id = (doc.to_dict().get('ultimo_id', 0) + 1) if doc.exists else 1
        contador_ref.set({"ultimo_id": novo_id})
        
        # Salvamos CPF sempre como STRING para evitar perda de zeros
        novo_cliente = {
            "id": novo_id,
            "nome": str(dados["nome"]),
            "cpf": str(dados["cpf"]),
            "autorizado": bool(dados["autorizado"])
        }
        
        db.collection('clientes').add(novo_cliente)
        return jsonify({"message": "Sucesso", "novo_id": novo_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rota DELETE corrigida (Busca por ID e deleta o documento interno)
@app.route("/clientes/<int:id>", methods=['DELETE'])
@token_obrigatorio
def delete_cliente(id):
    docs = db.collection('clientes').where('id', '==', id).get()
    if not docs:
        return jsonify({"error": "Não encontrado"}), 404
    
    for d in docs:
        db.collection('clientes').document(d.id).delete()
    return jsonify({"message": "Apagado"}), 200

if __name__ == "__main__":
    app.run(debug=True)