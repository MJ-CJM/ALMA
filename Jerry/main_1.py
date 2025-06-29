from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/add")
def add(a:int = Query(...), b: int = Query(...)):
    return {"operation": "add", "a": a, "b": b, "result": a + b}

@app.get("/sub")
def subtract(a: int = Query(...), b: int = Query(...)):
    return {"operation": "sub", "a": a, "b": b, "result": a - b}

@app.get("/mul")
def multiply(a: int = Query(...), b: int = Query(...)):
    return {"operation": "mul", "a": a, "b": b, "result": a * b}

@app.get("/div")
def divide(a: int = Query(...), b: int = Query(...)):
    return {"operation": "div", "a": a, "b": b, "result": a / b}

@app.get("/mod")
def modulo(a: int = Query(...), b: int = Query(...)):
    return {"operation": "mod", "a": a, "b": b, "result": a % b}