from flask import Flask, render_template, request, url_for, redirect, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import bcrypt
from dotenv import load_dotenv
import os

load_dotenv()

# Create a new client and connect to the server
client = MongoClient(os.getenv("MONGO_URI"), server_api=ServerApi('1'))
# add your mongodb uri to your credentials.py file!
# uri = "your_mongo_db_uri"

db = client.db
posts = db.posts
users = db.users
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")


@app.route('/')
def index():
    all_posts = posts.find()
    return render_template('index.html', posts=all_posts)


@app.route('/admin', methods=("GET", "POST"))
def admin():
    if 'username' in session and session['username'] == 'gerardo':
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            posts.insert_one({'title': title, 'content': content})
            return redirect(url_for('admin'))

        all_posts = posts.find()
        return render_template('admin.html', posts=all_posts, username=session['username'])

    else:
        return redirect(url_for('login'))


@app.route("/post", methods=("GET", "POST"))
def view_posts():
    title = request.args.get('title')
    query = {"title": title}
    content = posts.find_one(query)
    if content:
        return render_template('posts.html', content=content)
    else:
        return "Post no encontrado", 404


@app.route('/<id>/delete/', methods=("GET", "POST"))
def delete(id):
    posts.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin'))


@app.route('/<id>/edit/', methods=("GET", "POST"))
def edit(id):
    if 'username' in session and session['username'] == 'gerardo':
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            posts.update_one({"_id": ObjectId(id)}, {'$set': {'title': title, 'content': content}})
            return redirect(url_for('admin'))
        post = posts.find_one({"_id": ObjectId(id)})
        return render_template('edit.html', post=post)
    return redirect(url_for('login'))


@app.route('/process', methods=['POST'])
def process():
    search_query = request.form.get('search_query')
    
    query = {"title": {"$regex": search_query, "$options": "i"}}
    
    results = posts.find(query)

    search_results = [result for result in results]

    return render_template('search_results.html', search_results=search_results)

@app.route('/login', methods=("GET", "POST"))
def login():
    if request.method == 'POST':
        print("=== Login Attempt ===")
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt for username: {username}")

        if not username or not password:
            print("Error: Missing username or password")
            return render_template('login.html', error="Please fill in all fields")

        stored_user = users.find_one({'username': username})
        if not stored_user:
            print(f"Error: User {username} not found in database")
            return render_template('login.html', error="Invalid credentials")

        if username != 'gerardo':
            print(f"Error: Attempted login with non-gerardo user: {username}")
            return render_template('login.html', error="Invalid credentials")

        try:
            # Obtener la contraseña almacenada y asegurarnos de que sea bytes
            stored_password = stored_user['password']
            
            # Si es un string que comienza con b'$2b$', convertirlo a bytes
            if isinstance(stored_password, str):
                if stored_password.startswith("b'") and stored_password.endswith("'"):
                    # Eliminar b'' y evaluar como string literal
                    stored_password = eval(stored_password)
                else:
                    stored_password = stored_password.encode('utf-8')
            
            # Verificar la contraseña
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                print("Success: Password match for user 'gerardo'")
                session['username'] = username
                return redirect(url_for('admin'))
            else:
                print("Error: Password mismatch for user 'gerardo'")
                return render_template('login.html', error="Invalid credentials")
        except Exception as e:
            print(f"Error during password verification: {str(e)}")
            return render_template('login.html', error="An error occurred")
    
    print("=== Login Page Accessed ===")
    return render_template('login.html')

    
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
