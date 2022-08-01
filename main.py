from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
app.secret_key = 'uma frase secreta'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Home page
@app.route("/")
def root():
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect('bicandi.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT id_mercadoria, nome, preco, descricao, imagem, estoque FROM mercadoria')
        itemData = cur.fetchall()
        print(itemData)
        cur.execute('SELECT id_categoria, categoria FROM categoria')
        categoryData = cur.fetchall()
    itemData = parse(itemData)
    return render_template('homeN3.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems,
                           categoryData=categoryData)


# Obtem detalhes do usuário se estiver logado
def getLoginDetails():
    with sqlite3.connect('bicandi.db') as conn:
        cur = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            cur.execute("SELECT cpf,  substr(nome, 1, instr(nome, ' ') - 1) AS firstName FROM usuario WHERE email = '" +
                        session['email'] + "'")
            userId, firstName = cur.fetchone()
            cur.execute("SELECT count(id_mercadoria) FROM pedido WHERE cpf = " + str(userId))
            noOfItems = cur.fetchone()[0]
    conn.close()
    return (loggedIn, firstName, noOfItems)


# Cadastra Produto
@app.route("/addItem", methods=["GET", "POST"])
def addItem():
    if request.method == "POST":
        idMercadoria = request.form['idMercadoria']
    nome = request.form['nome']
    preco = float(request.form['preco'])
    descricao = request.form['descricao']
    estoque = int(request.form['estoque'])
    idCategoria = int(request.form['idMercadoria'])

    # Upload imagem
    imagem = request.files['imagem']
    if imagem and allowed_file(imagem.filename):
        filename = secure_filename(imagem.filename)
        imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    imagemname = filename
    with sqlite3.connect('bicandi.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                '''INSERT INTO mercadoria (id_mercadoria,id_categoria,descricao,nome , preco,estoque, imagem ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (idMercadoria, idCategoria, descricao, nome, preco, estoque, imagem))
            conn.commit()
            msg = "Produto adiconado com sucesso!!!"
        except:
            msg = "Ocrreu um erro"
            conn.rollback()
    conn.close()
    print(msg)
    return redirect(url_for('root'))


# Remove item do carrinho
@app.route("/removeItem")
def removeItem():
    idMercadoria = request.args.get('idMercadoria')
    with sqlite3.connect('bicandi.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM mercadoria WHERE id_mercadoria = ' + idMercadoria)
            conn.commit()
            msg = "Produto deletado com sucesso!!!"
        except:
            conn.rollback()
            msg = "Ocrreu um erro"
    conn.close()
    print(msg)
    return redirect(url_for('root'))


# Mostra todos os itens da categoria
@app.route("/displayCategory")
def displayCategory():
    loggedIn, firstName, noOfItems = getLoginDetails()
    categoryId = request.args.get("categoryId")
    with sqlite3.connect('bicandi.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT m.id_mercadoria, m.nome, m.preco, m.imagem, m.id_categoria FROM mercadoria as m, categoria as c WHERE m.id_categoria = c.id_categoria AND c.id_categoria = " + categoryId)
        data = cur.fetchall()
    conn.close()
    categoryName = data[0][4]
    data = parse(data)
    return render_template('displayCategoryN3.html', itemData=data, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, categoryName=categoryName)

#Cadastro
@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template("profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

#Edição do cadastro
@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect('bicandi.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT email, nome , cpf , logradouro , endereco , numero , complemento , cep , cidade , estado , ddd, telefone FROM usuario WHERE email = '" +
            session['email'] + "'")
        profileData = cur.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems)


@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        with sqlite3.connect('bicandi.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT cpf, senha FROM usuario WHERE email = '" + session['email'] + "'")
            userId, password = cur.fetchone()
            if (password == oldPassword):
                try:
                    cur.execute("UPDATE usuario SET senha = ? WHERE cpf = ?", (newPassword, userId))
                    conn.commit()
                    msg = "Alteração feita com sucesso!!!"
                except:
                    conn.rollback()
                    flash("Ocorreu um erro na Alteração")
                    return render_template('changePassword.html')
            else:
                flash("Senha Incorreta")
        conn.close()
        return render_template("changePassword.html")
    else:
        return render_template("changePassword.html")

#atualiza o cadastro
@app.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        logradouro = request.form['logradouro']
        endereco = request.form['endereco']
        numero = request.form['numero']
        complemento = request.form['complemento']
        cep = request.form['cep']
        cidade = request.form['cidade']
        estado = request.form['estado']
        ddd = request.form['ddd']
        telefone = request.form['telefone']

    with sqlite3.connect('bicandi.db') as con:
        try:
            cur = con.cursor()
            cur.execute(
                'UPDATE usuario SET nome = ?, cpf = ?, logradouro = ?, endereco = ?, numero = ?, complemento = ?, cep = ?, cidade = ?, estado = ?, ddd = ?, telefone = ? WHERE email = ? ',
                (nome, cpf, logradouro, endereco, numero, complemento, cep, cidade, estado, ddd, telefone))

            con.commit()
            msg = "Salvo com sucesso"
        except:
            con.rollback()
            msg = "Ocorreu um errro"
    con.close()
    return redirect(url_for('editProfile'))


@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            flash('Usuário/Senha Inválido')
            return render_template('login.html')


@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    id_mercadoria = request.args.get('productId')
    with sqlite3.connect('bicandi.db') as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT id_mercadoria, nome, preco, descricao, imagem , estoque FROM mercadoria WHERE id_mercadoria = ' + id_mercadoria)
        productData = cur.fetchone()
    conn.close()
    return render_template("productDescription.html", data=productData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems)

#Adiciona o produto ao carrinho
@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        idMercadoria = int(request.args.get('productId'))
        with sqlite3.connect('bicandi.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT cpf FROM usuario WHERE email = '" + session['email'] + "'")
            userId = cur.fetchone()[0]
            try:
                cur.execute("INSERT INTO pedido (cpf, id_mercadoria, email) VALUES (?, ?, ?)",
                            (userId, idMercadoria, session['email']))
                conn.commit()
                msg = "Produto adicionado com sucesso"
            except:
                conn.rollback()
                msg = "Ocorreu um erro"
        conn.close()
        return redirect(url_for('root'))

#Desenha o carrinho
@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    with sqlite3.connect('bicandi.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT cpf FROM usuario WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute(
            "SELECT m.id_mercadoria, m.nome, m.preco, m.imagem FROM mercadoria as m , pedido as p WHERE m.id_mercadoria = p.id_mercadoria AND p.cpf = " + str(userId))
        products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
    return render_template("cartN.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems)


@app.route("/checkout")
def checkout():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    with sqlite3.connect('bicandi.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT cpf FROM usuario WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute(
            "SELECT m.id_mercadoria, m.nome, m.preco, m.imagem FROM mercadoria as m, pedido as p WHERE m.id_mercadoria = p.id_mercadoria AND p.cpf = " + str(
                userId))
        products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
    return render_template("checkout.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems)


@app.route("/instamojo")
def instamojo():
    return render_template("pagtoCartao.html")


@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    idMercadoria = int(request.args.get('productId'))
    with sqlite3.connect('bicandi.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT cpf FROM usuario WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        try:
            cur.execute("DELETE FROM pedido WHERE cpf = " + str(userId) + " AND id_mercadoria = " + str(idMercadoria))
            conn.commit()
            msg = "Item Removido com sucesso"
        except:
            conn.rollback()
            msg = "Ocorreu um erro"
    conn.close()
    return redirect(url_for('root'))


@app.route("/finaliza")
def finalizaPedido():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']

    with sqlite3.connect('bicandi.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT cpf FROM usuario WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        try:
            cur.execute("DELETE FROM pedido WHERE cpf = " + str(userId) )
            conn.commit()
            msg = "Pedido Enviado com sucesso"
        except:
            conn.rollback()
            msg = "Ocorreu um erro no pagamento do pedido"
    conn.close()
    return redirect(url_for('root'))



@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))


def is_valid(email, password):
    con = sqlite3.connect('bicandi.db')
    cur = con.cursor()
    cur.execute('SELECT email, senha FROM usuario')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Parse form data
        password = request.form['password']
        email = request.form['email']
        nome = request.form['nome']
        cpf = request.form['cpf']
        logradouro = request.form['logradouro']
        endereco = request.form['endereco']
        numero = request.form['numero']
        complemento = request.form['complemento']
        cep = request.form['cep']
        cidade = request.form['cidade']
        estado = request.form['estado']
        ddd = request.form['ddd']
        telefone = request.form['telefone']

    with sqlite3.connect('bicandi.db') as con:
        try:
            cur = con.cursor()
            cur.execute(
                'INSERT INTO usuario (senha, cpf, email, nome, logradouro, endereco, numero, complemento, cep,cidade, estado, ddd, telefone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                hashlib.md5(password.encode()).hexdigest(), cpf, email, nome, logradouro, endereco, numero, complemento,
                cep, cidade, estado, ddd, telefone))

            con.commit()

            msg = "Registrado com Successo"
        except:
            con.rollback()
            msg = "Ocorreu um erro"
    con.close()
    return render_template("login.html", error=msg)


@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans


if __name__ == '__main__':
    app.run(debug=True)
