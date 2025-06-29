from fastapi import FastAPI, Query
app = FastAPI()

@app.get("/add")
def add(a: int = Query(...), b: int = Query(...)):
 return {"operation": "add", "a": a, "b": b, "result": a + b}
@app.get("/sub")
def subtract(a: int = Query(...), b: int = Query(...)):
 return {"operation": "sub", "a": a, "b": b, "result": a - b}


@app.get("/time")
def time(a: int = Query(...), b: int = Query(...)):
 return {"operation": "time", "a": a, "b": b, "result": a * b}
@app.get("/divide")
def divide(a: int = Query(...), b: int = Query(...)):
 return {"operation": "divide", "a": a, "b": b, "result": a / b}

# @app.get("/modulo")
# def modulo(a: int = Query(...), b: int = Query(...)):
#  return {"operation": "modulo", "a": a, "b": b, "result": a % b}

@app.post("/modulo")
def modulo_post(a: int = Query(...), b: int = Query(...)):
 return {"operation": "modulo", "a": a, "b": b, "result": a % b}

@app.post("/divide")
def divide(a: int = Query(...), b: int = Query(...)):
 return {"operation": "divide", "a": a, "b": b, "result": a / b}

@app.post("/time")
def time(a: int = Query(...), b: int = Query(...)):
 return {"operation": "time", "a": a, "b": b, "result": a * b}

@app.post("/sub")
def sub(a: int = Query(...), b: int = Query(...)):
 return {"operation": "sub", "a": a, "b": b, "result": a - b}

@app.post("/add")
def add(a: int = Query(...), b: int = Query(...)):
 return {"operation": "add", "a": a, "b": b, "result": a + b}

@app.get("/modulo")
def modulo(a: int = Query(4), b: int = Query(2)):
 return {"operation": "modulo", "a": a, "b": b, "result": a % b}
