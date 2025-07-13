from fastapi import FastAPI
from fastapi import Query

from fastapi import Request
from pydantic import BaseModel
from typing import List, Literal

class Step(BaseModel):
  type: Literal["add", "subtract", "multiply", "divide"]
  a: float
  b: float

class CalculationRequest(BaseModel):
  steps: List[Step]

app = FastAPI()

global tinydict
tinydict = {}
global count
count = 0

@app.get("/add")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a+b
  return{"operation": "add", "a": a, "b": b, "result":a+b,"every result":tinydict.values()}
  count += 1

@app.get("/subtraction")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a-b
  return{"operation": "subtraction", "a": a, "b": b, "result":a-b,"every result":tinydict.values()}
  count += 1
@app.get("/multiplication")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a*b
  return{"operation": "multiplication", "a": a, "b": b, "result":a*b,"every result":tinydict.values()}
  count += 1
@app.get("/division")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a/b
  return{"operation": "division", "a": a, "b": b, "result":a/b,"every result":tinydict.values()}
  count += 1
@app.get("/mod")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a%b
  return{"operation": "mod", "a": a, "b": b, "result":a%b,"every result":tinydict.values()}
  count += 1
app = FastAPI()
@app.post("/add(post)")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a+b
  return{"operation": "add", "a": a, "b": b, "result":a+b,"every result":tinydict.values()}
  count += 1
@app.post("/subtraction(post)")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a-b
  return{"operation": "subtraction", "a": a, "b": b, "result":a-b,"every result":tinydict.values()}
  count += 1
@app.post("/multiplication(post)")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a*b
  return{"operation": "multiplication", "a": a, "b": b, "result":a*b,"every result":tinydict.values()}
  count += 1
@app.post("/d(post)")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a/b
  return{"operation": "d", "a": a, "b": b, "result":a/b,"every result":tinydict.values()}
  count += 1
@app.post("/mod(post)")
def greet(a:int = Query(),b:int = Query()):
  tinydict[count] = a%b
  return{"operation": "mod", "a": a, "b": b, "result":a%b,"every result":tinydict.values()}
  count += 1


@app.post("/api/v1/calculate")
def calculate(req: CalculationRequest):

  result = None
  for step in req.steps:
    if step.type == "add":
      result = step.a + step.b
    elif step.type == "subtract":
      result = step.a - step.b
    elif step.type == "multiply":
      result = step.a * step.b
    elif step.type == "divide":
      result = step.a / step.b
  return {"result": result}