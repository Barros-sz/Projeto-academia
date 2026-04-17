
#  GymSystem API

O **GymSystem** é uma API robusta desenvolvida para o gerenciamento de clientes em academias. O sistema permite o controle de acesso e cadastro de alunos, integrando-se com bancos de dados NoSQL e oferecendo segurança via autenticação por tokens.

Este projeto faz parte do ecossistema de desenvolvimento do **SENAI**.

##  Tecnologias Utilizadas

* **Backend:** Python com o framework Flask.
* **Banco de Dados:** Google Firebase Firestore.
* **Segurança:** Autenticação via Token (JWT/Custom) e CORS configurado para ambientes específicos.
* **Documentação:** Swagger (Flasgger) para especificação OpenAPI.
* **Deployment:** Preparado para execução local ou na plataforma Vercel.

##  Funcionalidades

* **Autenticação:** Sistema de login para administradores com geração de token de acesso.
* **Gestão de Clientes:** * Listagem completa de alunos.
    * Busca individual por ID ou CPF.
    * Cadastro de novos clientes com geração automática de ID incremental.
    * Atualização total (PUT) ou parcial (PATCH) de dados.
    * Exclusão de registros.

##  Configuração e Instalação

### 1. Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto e configure as seguintes chaves:
```env
SECRET_KEY=sua_chave_secreta
ADM_USUARIO=seu_usuario_admin
ADM_SENHA=sua_senha_admin
FLASK_DEBUG=1
```

### 2. Firebase
Para rodar localmente, certifique-se de ter o arquivo `firebase.json` com suas credenciais de conta de serviço na raiz do projeto. No ambiente Vercel, utilize a variável `FIREBASE_CREDENTIALS` em formato JSON.

### 3. Instalação
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar a aplicação
python app.py
```

##  Endpoints Principais

| Método | Endpoint | Descrição | Protegido? |
| :--- | :--- | :--- | :--- |
| **POST** | `/login` | Realiza login e retorna o token | Não |
| **GET** | `/clientes` | Lista todos os clientes | Não |
| **GET** | `/clientes/cpf/<cpf>` | Busca cliente pelo CPF | Não |
| **POST** | `/clientes` | Cadastra um novo cliente | **Sim** |
| **PUT** | `/clientes/<id>` | Atualiza todos os dados do cliente | **Sim** |
| **DELETE** | `/clientes/<id>` | Remove um cliente do sistema | **Sim** |

##  Documentação (Swagger)
Com o servidor rodando, acesse a documentação interativa em:
`http://localhost:5000/apidocs`

---

**Desenvolvido por:** Barros e João Pedro.