from fastapi import FastAPI
from fastapi import Query
app = FastAPI()
@app.get("/add")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "add", "a": a, "b": b, "result": a + b}
@app.get("/subtraction")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "subtraction", "a": a, "b": b, "result":a-b}
@app.get("/multiplication")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "multiplication", "a": a, "b": b, "result":a*b}
@app.get("/division")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "division", "a": a, "b": b, "result":a/b}
@app.get("/mod")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "mod", "a": a, "b": b, "result":a%b}
app = FastAPI()
@app.post("/add(post)")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "add", "a": a, "b": b, "result": a + b}
@app.post("/subtraction(post)")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "subtraction", "a": a, "b": b, "result":a-b}
@app.post("/multiplication(post)")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "multiplication", "a": a, "b": b, "result":a*b}
@app.post("/d(post)")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "d", "a": a, "b": b, "result":a/b}
@app.post("/mod(post)")
def greet(a:int = Query(),b:int = Query()):
  return{"operation": "mod", "a": a, "b": b, "result":a%b}


