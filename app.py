import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# --- AULA 1: CONEXÃO E ESTRUTURA NoSQL ---
# O MongoDB permite armazenar dados sem esquema fixo (flexibilidade)

connection_string = "mongodb+srv://nickvininv_db_user:dOVYvl0mMblAxfJB@projetonasql.7hrhugw.mongodb.net/?appName=ProjetoNasql"
client = MongoClient(connection_string)
db = client["ecommerce"]
colecao = db["produtos"]

colecao.insert_one({
    "nome": "Teclado",
    "preco": 100
})


def configurar_banco():
    #Inicializa as coleções e limpa dados antigos para a atividade.
    db.produtos.drop()
    db.pedidos.drop()

    # Criando produtos iniciais (CRUD inicial)
    db.produtos.insert_many([
        {"nome": "Notebook", "preco": 3500.00, "estoque": 10},
        {"nome": "Mouse", "preco": 150.00, "estoque": 50},
        {"nome": "Monitor", "preco": 1200.00, "estoque": 5}
    ])

    print("Banco de dados configurado e produtos inseridos.")


# --- AULA 2: OTIMIZAÇÃO DE CONSULTAS ---
# Criação de índices para acelerar a busca e uso de projeções

def criar_indices():
    # Índices evitam a varredura total da coleção, melhorando a performance
    db.produtos.create_index([("nome", pymongo.ASCENDING)])
    print("Índice criado no campo 'nome'.")


def buscar_produto_otimizado(nome_produto):
    # Projeção: Retorna apenas os campos necessários para economizar memória e rede
    projecao = {"nome": 1, "preco": 1, "_id": 0}
    produto = db.produtos.find_one({"nome": nome_produto}, projecao)
    return produto


# --- AULA 3: TRANSAÇÕES E CONSISTÊNCIA ---
# Garante a atomicidade: ou tudo acontece, ou nada é gravado

def realizar_venda(nome_produto, quantidade):
    # Transações multi-documento garantem consistência entre produtos e pedidos
    with client.start_session() as session:
        with session.start_transaction():
            try:
                # 1. Verificar estoque
                produto = db.produtos.find_one(
                    {"nome": nome_produto},
                    session=session
                )

                if not produto or produto['estoque'] < quantidade:
                    print("Estoque insuficiente ou produto não encontrado.")
                    session.abort_transaction()  # Reverte se a condição falhar
                    return

                # 2. Atualizar estoque do produto
                db.produtos.update_one(
                    {"nome": nome_produto},
                    {"$inc": {"estoque": -quantidade}},
                    session=session
                )

                # 3. Registrar o pedido
                db.pedidos.insert_one({
                    "produto": nome_produto,
                    "quantidade": quantidade,
                    "total": produto['preco'] * quantidade
                }, session=session)

                print(f"Venda de {quantidade} {nome_produto}(s) realizada com sucesso!")

                # A transação é confirmada automaticamente ao sair do bloco 'with'

            except PyMongoError as e:
                print(f"Erro na transação: {e}. Abortando...")
                session.abort_transaction()


# --- EXECUÇÃO ---
if __name__ == "__main__":
    configurar_banco()
    criar_indices()

    # Exemplo de consulta otimizada
    print("Consultando produto (otimizado):",
          buscar_produto_otimizado("Notebook"))

    # Exemplo de transação segura
    realizar_venda("Notebook", 2)

    # Verificando estado final do estoque
    print("Estoque atualizado:",
          db.produtos.find_one({"nome": "Notebook"}, {"estoque": 1}))