from flask import Flask, jsonify, request
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
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "chave_padrao_segura")

app.config["SWAGGER"] = {"openapi": "3.0.3"}
swagger = Swagger(app, template_file="openapi.yaml")

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://academia-catraca.vercel.app",
                "https://secretaria-academia.vercel.app",
            ]
        }
    },
)

ADM_USUARIO = os.getenv("ADM_USUARIO")
ADM_SENHA = os.getenv("ADM_SENHA")

# Firebase
if os.getenv("VERCEL"):
    firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")
    if not firebase_credentials:
        raise ValueError("FIREBASE_CREDENTIALS não definido no ambiente.")
    cred = credentials.Certificate(json.loads(firebase_credentials))
else:
    cred = credentials.Certificate("firebase.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()


@app.route("/", methods=["GET"])
def root():
    return jsonify({"api": "GymSystem", "version": "1.0", "author": "barros and joao pedro"}), 200


@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json(silent=True)

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


@app.route("/clientes", methods=["GET"])
def get_clientes():
    clientes = [item.to_dict() for item in db.collection("clientes").stream()]
    return jsonify(clientes), 200


@app.route("/clientes/<int:id>", methods=["GET"])
def get_cliente_by_id(id):
    docs = db.collection("clientes").where("id", "==", id).limit(1).get()

    if not docs:
        return jsonify({"error": "Cliente não encontrado"}), 404

    return jsonify(docs[0].to_dict()), 200


@app.route("/clientes/cpf/<string:cpf>", methods=["GET"])
def get_cliente_by_cpf(cpf):
    docs = db.collection("clientes").where("cpf", "==", cpf).limit(1).get()

    if not docs:
        return jsonify({"error": "Não encontrado"}), 404

    return jsonify(docs[0].to_dict()), 200


@app.route("/clientes", methods=["POST"])
@token_obrigatorio
def post_clientes():
    dados = request.get_json(silent=True)

    if not dados or "nome" not in dados or "cpf" not in dados or "autorizado" not in dados:
        return jsonify({
            "error": "Dados inválidos ou incompletos. Campos necessários: nome, cpf, autorizado."
        }), 400

    try:
        contador_ref = db.collection("contador").document("controle_id")
        contador_doc = contador_ref.get()

        if not contador_doc.exists:
            contador_ref.set({"ultimo_id": 1})
            novo_id = 1
        else:
            contador_data = contador_doc.to_dict() or {}
            ultimo_id = contador_data.get("ultimo_id", 0)
            novo_id = ultimo_id + 1
            contador_ref.update({"ultimo_id": novo_id})

        db.collection("clientes").add({
            "id": novo_id,
            "nome": dados["nome"],
            "cpf": dados["cpf"],
            "autorizado": dados["autorizado"]
        })

        return jsonify({"message": "Cliente criado com sucesso!", "novo_id": novo_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/clientes/<int:id>", methods=["PUT"])
@token_obrigatorio
def clientes_put(id):
    dados = request.get_json(silent=True)

    if not dados or "nome" not in dados or "cpf" not in dados or "autorizado" not in dados:
        return jsonify({"error": "Dados inválidos ou incompletos"}), 400

    try:
        query = db.collection("clientes").where("id", "==", id).limit(1).get()

        if not query:
            return jsonify({"error": "Cliente não encontrado"}), 404

        for doc in query:
            db.collection("clientes").document(doc.id).update({
                "nome": dados["nome"],
                "cpf": dados["cpf"],
                "autorizado": dados["autorizado"]
            })

        return jsonify({"message": "Cliente atualizado com sucesso!", "id": id}), 200

    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@app.route("/clientes/<int:id>", methods=["PATCH"])
@token_obrigatorio
def clientes_patch(id):
    dados = request.get_json(silent=True)

    if not dados or ("nome" not in dados and "cpf" not in dados and "autorizado" not in dados):
        return jsonify({"error": "Dados inválidos ou incompletos"}), 400

    try:
        query = db.collection("clientes").where("id", "==", id).limit(1).get()

        if not query:
            return jsonify({"error": "Cliente não encontrado"}), 404

        update_data = {}
        for campo in ["nome", "cpf", "autorizado"]:
            if campo in dados:
                update_data[campo] = dados[campo]

        for doc in query:
            db.collection("clientes").document(doc.id).update(update_data)

        return jsonify({"message": "Cliente atualizado!", "id": id}), 200

    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@app.route("/clientes/<int:id>", methods=["DELETE"])
@token_obrigatorio
def delete_cliente(id):
    docs = db.collection("clientes").where("id", "==", id).limit(1).get()

    if not docs:
        return jsonify({"error": "Cliente não encontrado"}), 404

    db.collection("clientes").document(docs[0].id).delete()
    return jsonify({"message": "Cliente apagado!", "id": id}), 200


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")