from flask import Flask, jsonify, request, redirect, url_for
import random
import firebase_admin
from firebase_admin import credentials, firestore
from auth import token_obrigatorio, gerar_token
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from flasgger import Swagger

load_dotenv()

app = Flask(__name__)

# versão do openapi
app.config['SWAGGER'] = {'openapi': '3.0.3'}
# trazer openapi para o codigo
swagger = Swagger(app, template_file='openapi.yaml')

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

CORS(app, origins=["--CATRACA NA VERCEL--", "--ADMINSTRADOR NA VERCEL--"])
ADM_USUARIO = os.getenv("ADM_USUARIO")
ADM_SENHA = os.getenv("ADM_SENHA")

if os.getenv("VERCEL"):
    # se na vercel
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
else:  # se local
    cred = credentials.Certificate("firebase.json")
    
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/", methods=['GET'])
def root():
    return jsonify({"api": "GymSystem", "version": "1.0", "author": "barros and joao pedro"}), 200

#######################################__________Rota de login_________########################################

@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json()
    if not dados:
        return jsonify({"error": "envie os dados para login"}), 400
    
    usuario = dados.get("usuario")
    senha = dados.get("senha")

    if not usuario or not senha:
        return jsonify({"error": "usuario e senha são obrigatórios"}), 400
    
    if usuario == ADM_USUARIO and senha == ADM_SENHA:
        token = gerar_token(usuario)
        return jsonify({"message": "login realizado com sucesso", "token": token}), 200
    
    return jsonify({"error": "Credenciais inválidas"}), 401


############################################_____ROTAS ABERTAS_____###########################################

# rotas basicas - BUSCA GERAL #################################################
@app.route("/clientes", methods=['GET'])
def get_clientes():
    clientes = []
    lista = db.collection('clientes').stream()
    for item in lista:
        clientes.append(item.to_dict())
    return jsonify(clientes), 200


# rotas basicas - BUSCA POR ID #################################################
@app.route("/clientes/<int:id>", methods=['GET'])
def get_cliente_by_id(id):
    docs = db.collection('clientes').where('id', '==', id).limit(1).get()
    
    if not docs:
        return jsonify({"error": "Cliente não encontrado"}), 404
        
    return jsonify(docs[0].to_dict()), 200


# rotas basicas - BUSCA ALETÓRIA #################################################
@app.route("/clientes/random", methods=['GET'])
def get_cliente_random():
    lista = list(db.collection('clientes').stream())

    if not lista:
        return jsonify({"error": "Nenhum cliente encontrado"}), 404
    
    escolhido = random.choice(lista)
    return jsonify(escolhido.to_dict()), 200


############################################_____ROTAS FECHADAS_____###########################################
  
# adicionar cliente - +token #################################################
@app.route("/clientes", methods=['POST'])
@token_obrigatorio
def post_clientes():
    dados = request.get_json()
    if not dados or "nome" not in dados or "cpf" not in dados or "autorizado" not in dados:
        return jsonify({"error": "Dados inválidos ou incompletos. Campos necessários: nome, cpf, autorizado."}), 400
    
    # adicionar
    try:
        # contador
        contador_ref = db.collection('contador').document('controle_id')
        contador_doc = contador_ref.get()
        # add ID
        novo_id = contador_doc.to_dict()['ultimo_id'] + 1
        contador_ref.update({"ultimo_id": novo_id})
        
        # atualizar banco de clientes
        db.collection('clientes').add({
            "id": novo_id,
            "nome": dados["nome"],
            "cpf": dados["cpf"],
            "autorizado": dados["autorizado"]
        })
        return jsonify({"message": "Cliente criado com sucesso!", "novo_id": novo_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# alterar cliente completo - +token #################################################
@app.route("/clientes/<int:id>", methods=['PUT'])
@token_obrigatorio
def clientes_put(id):
    # dados
    dados = request.get_json()
    if not dados or "nome" not in dados or "cpf" not in dados or "autorizado" not in dados:
        return jsonify({"error": "Dados inválidos ou incompletos"}), 400
    
    try:
        # busca o documento pelo id
        query = db.collection("clientes").where("id", "==", id).limit(1).get()
        
        if not query:
            return jsonify({"error": "Cliente não encontrado"}), 404

        # atualiza o documento
        for doc in query:
            doc_ref = db.collection("clientes").document(doc.id)
            doc_ref.update({
                "nome": dados["nome"],
                "cpf": dados["cpf"],
                "autorizado": dados["autorizado"]
            })
        
        return jsonify({"message": "Cliente atualizado com sucesso!", "id": id}), 200
    
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
    

# alterar parte do cliente - +token #################################################
@app.route("/clientes/<int:id>", methods=['PATCH'])
@token_obrigatorio
def clientes_patch(id):
    # dados
    dados = request.get_json()
    if not dados or ("nome" not in dados and "cpf" not in dados and "autorizado" not in dados):
        return jsonify({"error": "Dados inválidos ou incompletos"}), 400
    
    try:
        # busca o documento pelo id
        query = db.collection("clientes").where("id", "==", id).limit(1).get()
        
        if not query:
            return jsonify({"error": "Cliente não encontrado"}), 404

        # Dicionário dinâmico para atualizar apenas o que foi enviado
        update_data = {}
        if "nome" in dados:
            update_data["nome"] = dados["nome"]
        if "cpf" in dados:
            update_data["cpf"] = dados["cpf"]
        if "autorizado" in dados:
            update_data["autorizado"] = dados["autorizado"]

        # atualiza o documento
        for doc in query:
            doc_ref = db.collection("clientes").document(doc.id)
            doc_ref.update(update_data)
        
        return jsonify({"message": "Cliente atualizado!", "id": id}), 200
    
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
    
# apaga cliente - +token #################################################
@app.route("/clientes/<int:id>", methods=['DELETE'])
@token_obrigatorio
def delete_cliente(id):
    docs = db.collection('clientes').where('id', '==', id).limit(1).get()
    
    if not docs:
        return jsonify({"error": "Cliente não encontrado"}), 404
        
    doc_ref = db.collection('clientes').document(docs[0].id)
    doc_ref.delete()
    return jsonify({"message": "Cliente apagado!", "id": id}), 200

#################################################################################################################################
if __name__ == "__main__":
    app.run(debug=True)