from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>EL NUEVO APP.PY ESTA FUNCIONANDO</h1>"