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

#versão do openapi
app.config['SWAGGER'] = {'openapi':'3.0.3'}
#trazer openapi para o codigo
swagger = Swagger(app, template_file='openapi.yaml')


app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

CORS(app, origins=["--CATRACA NA VERCEL--","--ADMINSTRADOR NA VERCEL--"])
ADM_USUARIO = os.getenv("ADM_USUARIO")
ADM_SENHA = os.getenv("ADM_SENHA")


if os.getenv("VERCEL"):
    #se na vercel
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
else:#se local
    cred = credentials.Certificate("firebase.json")
    
firebase_admin.initialize_app(cred)
db = firestore.client()



@app.route("/", methods=['GET'])
def root():
    return jsonify({"api": "GymSystem", "version": "1.0", "author": "barros and joão pedro"}), 200


#######################################__________Rota de login_________########################################

@app.route("/login", methods=["POST"])
def login():
    dados =request.get_json()
    if not dados:
        return jsonify({"error":"envie os dados para login"}), 400
    
    usuario = dados.get("usuario")
    senha = dados.get("senha")

    if not usuario or not senha:
        return jsonify({"error":"usuario e senha são obrigatórios"}), 400
    
    if usuario == ADM_USUARIO and senha == ADM_SENHA:
        token = gerar_token(usuario)
        return jsonify({"message":"login realizado com sucesso", "token":token}), 200



############################################_____ROTAS ABERTAS_____###########################################


# rotas basicas - BUSCA GERAL #################################################
@app.route("/charadas", methods=['GET'])
def get_charadas():
    clientes = []
    lista = db.collection('clientes').stream()
    for item in lista:
        clientes.append(item.to_dict())
    return jsonify(clientes), 200


# rotas basicas - BUSCA POR ID #################################################
@app.route("/charadas/<int:id>", methods=['GET'])
def get_charada_by_id(id):
    docs = db.collection('charadas').where('id', '==', id).limit(1).get()
    
    if not docs:
        return jsonify({"error": "Charada não encontrada"}), 404
        
    return jsonify(docs[0].to_dict()), 200


# rotas basicas - BUSCA ALETÓRIA #################################################
@app.route("/charadas/random", methods=['GET'])
def get_charada_random():
    lista = list(db.collection('charadas').stream())

    if not lista:
        return jsonify({"error": "Nenhuma charada encontrada"}), 404
    
    escolhida = random.choice(lista)
    return jsonify(escolhida.to_dict()), 200


############################################_____ROTAS FECHADAS_____###########################################
  

# adicionar charada - +token #################################################
@app.route("/charadas", methods=['POST'])
@token_obrigatorio
def post_charadas():
    
    dados = request.get_json()
    if not dados or "pergunta" not in dados or "resposta" not in dados:
        return jsonify({"error": "Dados inválidos ou incompletos"}), 400
    
    # adicionar
    try:
        # contador
        contador_ref = db.collection('contador').document('controle_id')
        contador_doc = contador_ref.get()
        # add ID
        novo_id = contador_doc.to_dict()['ultimo_id'] + 1
        contador_ref.update({"ultimo_id": novo_id})
        # atualizar
        db.collection('charadas').add({
            "id": novo_id,
            "pergunta": dados["pergunta"],
            "resposta": dados["resposta"]
        })
        return jsonify({"message": "Criada com sucesso!", "novo_id": novo_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# alterar charada completa - +token #################################################
@app.route("/charadas/<int:id>", methods=['PUT'])
@token_obrigatorio

def charadas_put(id):
    
    # dados
    dados = request.get_json()
    if not dados or "pergunta" not in dados or "resposta" not in dados:
        return jsonify({"error": "Dados inválidos ou incompletos"}), 400
    
    try:
        # busca o documento pelo id
        query = db.collection("charadas").where("id", "==", id).limit(1).get()
        
        if not query:
            return jsonify({"error": "Charada não encontrada"}), 404

        # atualiza o documento
        for doc in query:
            doc_ref = db.collection("charadas").document(doc.id)
            doc_ref.update({
                "pergunta": dados["pergunta"],
                "resposta": dados["resposta"]
            })
        
        return jsonify({
            "message": "charada atualizada!", "id": id}), 200
    
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
    

# alterar parte da charada - +token #################################################
@app.route("/charadas/<int:id>", methods=['PUT'])
@token_obrigatorio

def charadas_patch(id):
    
    # dados
    dados = request.get_json()
    if not dados or ("pergunta" not in dados and "resposta" not in dados):
        return jsonify({"error": "Dados inválidos ou incompletos"}), 400
    
    #redireciona para o put se mudar tudo
    if "pergunta" in dados and "resposta" in dados:
        return redirect(url_for('charadas_put', id=id))
    

    try:
        # busca o documento pelo id
        query = db.collection("charadas").where("id", "==", id).limit(1).get()
        
        if not query:
            return jsonify({"error": "Charada não encontrada"}), 404

        # atualiza o documento
        for doc in query:
            doc_ref = db.collection("charadas").document(doc.id)
            doc_ref.update({
                "pergunta": dados["pergunta"],
                "resposta": dados["resposta"]
            })
        
        return jsonify({"message": "charada atualizada!", "id": id}), 200
    
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
    
# apaga a charada - +token #################################################
@app.route("/charadas/<int:id>", methods=['DELETE'])
@token_obrigatorio

def delete_charada(id):
    
    
    docs = db.collection('charadas').where('id', '==', id).limit(1).get()
    
    if not docs:
        return jsonify({"error": "Charada não encontrada"}), 404
        
    doc_ref = db.collection('charadas').document(docs[0].id)
    doc_ref.delete()
    return jsonify({"message": "charada apagada!", "id": id}), 200
#################################################################################################################################
if __name__ == "__main__":
    app.run(debug=True)