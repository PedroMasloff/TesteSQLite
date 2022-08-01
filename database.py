import sqlite3

conn = sqlite3.connect('bicandi.db')

conn.execute('''CREATE TABLE USUARIO (nome STRING, cpf INTEGER PRIMARY KEY AUTOINCREMENT, logradouro STRING, endereco STRING, numero STRING, complemento STRING, cep INTEGER, cidade STRING, estado STRING, latitue STRING, longitude STRING, senha STRING)''')

conn.execute('''CREATE TABLE MERCADORIA (id_mercadoria INTEGER PRIMARY KEY, id_categoria INTEGER, descricao STRING, preco DECIMAL (14, 2), estoque INTEGER, imagem STRING)''')

conn.execute('''CREATE TABLE PEDIDO (id_pedido INTEGER PRIMARY KEY, cpf INTEGER, email STRING, data DATETIME, id_mercadoria INTEGER, valor_total DECIMAL, quantidade INTEGER, valor_item DECIMAL, status INTEGER)''')

conn.execute('''CREATE TABLE CATEGORIA (id_categoria INTEGER PRIMARY KEY AUTOINCREMENT, categoria STRING)''')



conn.close()

