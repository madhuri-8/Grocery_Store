import os
from flask import Flask , render_template ,request,redirect,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


current_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'your_secret_key'  
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+os.path.join(current_dir,"api_database.sqlite3")
db= SQLAlchemy()
db.init_app(app)





###########################   DATABASE DEFINED ##############################

class Category(db.Model):
    category_id = db.Column(db.Integer(),primary_key=True)
    category_name = db.Column(db.String(50), nullable=False, unique=True)
    category_product = db.relationship('Product',backref="prod")

class Product(db.Model):
    product_id = db.Column(db.Integer(),primary_key=True)
    product_name = db.Column(db.String(50),nullable = False, unique = True)
    product_price = db.Column(db.Integer(),nullable=False)
    product_quantity = db.Column(db.Integer(),nullable=False)
    product_category = db.Column(db.Integer(),db.ForeignKey(Category.category_id),nullable=False)
    expiry_date = db.Column(db.Date(),nullable=False)

class Login(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    name = db.Column(db.String(50),nullable=False,unique = True)
    password = db.Column(db.String(50),nullable = False, unique = True)
    type = db.Column(db.String(50),nullable = False)


class Cart(db.Model):
    c_id = db.Column(db.Integer(),primary_key= True)
    c_name = db.Column(db.String(50),nullable=False,unique=True)
    c_quantity = db.Column(db.Integer(),nullable=False)
    c_for = db.Column(db.Integer(),db.ForeignKey(Product.product_id),nullable=False)
    c_price= db.Column(db.Integer(),nullable = False)


################################## METHODS ##############################

################################## Home page ###################################

@app.route('/',methods=['GET','POST'])
def home():
    all_pro= Product.query.all()
    cate = Category.query.all()
    if request.method=='GET':
        meth='get'
        pro = Product.query.order_by(Product.product_id.desc()).limit(5).all()
        query = request.args.get('query', '')
        posts=[]
        cats=[]
        
        if query:
            search = "%{}%".format(query)
            posts = Product.query.filter(Product.product_name.like(search)).all()
            cats = Category.query.filter(Category.category_name.like(search)).all()
            meth='post'
        return render_template('home.html',cate=cate,pro=pro,all_pro=all_pro,meth=meth,posts=posts,cats=cats)
    
################################## USER LOGIN ##################################

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method=='GET':
        return render_template("login.html")
    if request.method=='POST':
        
        name1 = request.form['username']
        pwd = request.form['password']

        # Query the database for the user
        user = Login.query.filter_by(name=name1).first()
    
        if user is None or user.type=='Manager':
            return render_template('login.html', info='Invalid User')
        else:
            if user.password != pwd:
                return render_template('login.html', info='Invalid Password')
            else:
                session['username'] = user.name
                session['logged_in'] = True

                #db.session.query(Cart).delete()
                db.session.commit()
        
        return redirect('/')
    
@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='GET':
        return render_template("signup.html")
    
    if request.method=='POST':
        usr_name=request.form['username']
        usr_pass = request.form['password']
        L = Login.query.all()
        for logins in L:
            if logins.name==usr_name:
                return render_template('login.html',info='User Name already exists')

        new_login = Login(name=usr_name,password=usr_pass,type="User")
        db.session.add(new_login)
        db.session.commit()
        return redirect("/cart")
    

@app.route('/logout')
def logout():
    session.clear()
    db.session.query(Cart).delete()
    db.session.commit()
    return redirect("/")

########################################## ADMIN LOGIN #################################

@app.route('/admin/login', methods=['POST', 'GET'])
def admin():
    if request.method =='GET':
        return render_template("admin_login.html")
    if request.method=='POST':
        name1 = request.form['username']
        pwd = request.form['password']
        l = Login.query.get(1)
        if name1 == l.name and pwd == l.password:
            session['admin'] = True
            return redirect('/admin/home')
        else:
            return render_template('admin_login.html', info='Invalid Credentials')
        


############################# CRUD OPERATIONS ON CART ############################

@app.route('/cart',methods=['GET','POST'])
def display_cart():
    if request.method == 'GET':
        total=0
        c =  Cart.query.all()
        for items in c:
            price = items.c_quantity * items.c_price
            total=total+price
        return render_template('cart.html',c =c,total=total)
    

@app.route('/cart/<id>/add',methods=['GET','POST'])
def add_cart(id):
    C = Cart.query.get(id)
    P = Product.query.get(C.c_for)

    if C is not None:
        if P.product_quantity!=0:
            P.product_quantity = P.product_quantity-1
            
            C.c_quantity = C.c_quantity+1
            db.session.commit()
    

    return redirect('/cart')


@app.route('/cart/<id>/delete',methods=['GET','POST'])
def delete_cart(id):
    
    C = Cart.query.get(id)
    P = Product.query.get(C.c_for)
    
    while C.c_quantity > 1:
        P.product_quantity = P.product_quantity+1
        C.c_quantity =C.c_quantity - 1
        db.session.commit()
        return redirect('/cart')

    P.product_quantity = P.product_quantity+1
    Cart.query.filter_by(c_id=id).delete()
    db.session.commit()
    return redirect('/cart')


############################# CRUD OPERATIONS ON CATEGORY ########################
@app.route('/admin/home',methods=['GET','POST'])
def category():
    cat = Category.query.all()
    return render_template('admin_home.html',cat=cat)


@app.route('/admin/add',methods=['GET','POST'])
def add_category():
    if request.method=='GET':
        return render_template('add_category.html')


    if request.method == 'POST':
        cat_name = request.form.get('category_name')
        cate = Category.query.all()
        for cats in cate:
            if cats.category_name==cat_name:
                return render_template('already_exists.html')
        c = Category(category_name=cat_name)
        db.session.add(c)
        db.session.commit()
        image= request.files['the_image']
        filename = os.path.join('static/Category_image',image.filename)
        image.save(filename)

        return redirect('/admin/home')

@app.route('/admin/<id>/delete',methods=['GET','POST'])
def delete_category(id):
    del_cat = Category.query.get(id)
    image_filename = f'{del_cat.category_name}.jpg'
    p = Product.query.filter_by(product_category=id).first()
    if p is not None:
         Cart.query.filter_by(c_for=p.product_id).delete()
    Product.query.filter_by(product_category=id).delete()
    Category.query.filter_by(category_id=id).delete()
    db.session.commit()
    if image_filename:
        full_path = os.path.join('static/Category_image', image_filename)
        if os.path.exists(full_path):
            os.remove(full_path)

    return redirect('/admin/home')

@app.route('/admin/<id>/update',methods=['GET','POST'])
def update_category(id):
    if request.method=='GET':
        up = Category.query.get(id)
        return render_template('update_category.html',up =up)
    if request.method=='POST':
        update_cat = Category.query.get(id)

        ####################### removing the older image #############
        image_filename = f'{update_cat.category_name}.jpg'
        if image_filename:
            full_path = os.path.join('static/Category_image', image_filename)
            if os.path.exists(full_path):
                os.remove(full_path)
        
        ##################updating ########################
        name = request.form.get('category_name')
        update_cat.category_name = name
        db.session.commit()
        image= request.files['the_image']
        filename = os.path.join('static/Category_image',image.filename)
        image.save(filename)
        return redirect("/admin/home")

    
##################################### CRUD OPERATIONS ON PRODUCTS #################


@app.route('/products/<cat_id>',methods=['GET'])
def product_display(cat_id):
    c = Category.query.get(cat_id)
    p = c.category_product
    return render_template("products.html",p=p,name=c.category_name,cat_id=cat_id)


@app.route('/<int:cat_id>/add_product', methods=['GET','POST'])
def add_product(cat_id):
    if request.method=='GET':
        return render_template("add_product.html",cat_id=cat_id)
    if request.method=='POST':
        prod_name = request.form['name']
        prod_quantity= request.form['quantity']
        prod_price = request.form['price']
        prod_expiry = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d')
        image = request.files['the_image']
        cate = Product.query.all()
        for cats in cate:
            if cats.product_name==prod_name:
                return render_template('already_exists.html',name=prod_name)

        c = Category.query.get(cat_id)
        pr = c.category_product

        pro = Product.query.order_by(Product.product_id.desc()).limit(1).all()
        pr_id=pro[0].product_id +1
        for prods in pr:
            if prods.product_name==prod_name:
                return render_template('already_exists.html',name=prod_name)
        
        p = Product(product_id=pr_id,product_name=prod_name,product_price=prod_price,product_quantity=prod_quantity,expiry_date=prod_expiry,product_category=cat_id)
        db.session.add(p)
        db.session.commit()

        image= request.files['the_image']
        filename = os.path.join('static/Product_image',image.filename)
        image.save(filename)

        return redirect('/admin/home')


@app.route('/<prod_id>/delete_product',methods=['GET','POST'])
def delete_product(prod_id):
    delete_name = Product.query.get(prod_id)
    image_filename = f'{delete_name.product_name}.jpg'
    Cart.query.filter_by(c_for=prod_id).delete()
    db.session.commit()
    Product.query.filter_by(product_id=prod_id).delete()
    db.session.commit()
   

    ####################### deleting the image ####################

    print(image_filename)
    if image_filename:
        full_path = os.path.join('static/Product_image', image_filename)
        if os.path.exists(full_path):
            os.remove(full_path)

    return redirect('/admin/home')


@app.route('/<prod_id>/update_product',methods=['GET','POST'])
def update_product(prod_id):
    p = Product.query.get(prod_id)
    
    if request.method=='GET':
        
        return render_template('update_product.html',p=p)
    
    if request.method=='POST':
        image_filename = f'{p.product_name}.jpg'
        if image_filename:
            full_path = os.path.join('static/Product_image', image_filename)
            if os.path.exists(full_path):
                os.remove(full_path)
        p.product_name = request.form['name']
        p.product_quantity= request.form['quantity']
        p.product_price = request.form['price']
        image = request.files['the_image']
        filename = os.path.join('static/Product_image',image.filename)
        image.save(filename)
        db.session.commit()
        return redirect('/admin/home')
    


############################## ADD TO CART  ###########################################

@app.route('/add_to_cart/<int:id>', methods=['GET','POST'])
def add_to_cart(id):
    if session.get('logged_in'):
        if request.method=='GET':
            p = Product.query.get(id)    
            cart_item = Cart.query.filter_by(c_for=id).first()
            if cart_item is not None:
                cart_item.c_quantity =cart_item.c_quantity + 1
                p.product_quantity -=1
                db.session.commit()
            else:
                carts = Cart(c_name=p.product_name, c_for=id, c_price=p.product_price, c_quantity=1)
                p.product_quantity -=1
                db.session.add(carts)
                db.session.commit()
            return redirect("/")
    else:
        return redirect("/login")

@app.route('/checkout',methods=['GET'])
def checkout():
    if not session.get('logged_in'):
        return redirect('/login')
    c =  Cart.query.all()
    total=0
    for items in c:
        price = items.c_quantity * items.c_price
        total=total+price
    db.session.query(Cart).delete()
    db.session.commit()
    return render_template('checkout.html', username=session['username'],total=total)


@app.route('/<int:id>',methods=['GET'])
def category_product(id):
    c = Category.query.get(id)
    p = c.category_product
    return render_template("products_user.html",p=p,name=c.category_name,id=id)

       
if __name__ == "__main__":
    app.run(debug=True)       


    

