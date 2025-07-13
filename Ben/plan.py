from fastapi import FastAPI
from fastapi import Query
import uvicorn

from fastapi import Request
from pydantic import BaseModel
from typing import List, Literal

app = FastAPI()

KINDS = ["Nouns", "numbers", "actions", "locations", "disciplines", "names"]
#处理关键词
def extract(string):
  count = 0
  keyword = {}
  while (count <= len(KINDS)):
    order = string.find("|")
    keyword[KINDS[count]] = string[0,order]
    string = string[order]
    count += 1
  return keyword

@app.post("/find")
def find(keywords:str = Query()):
  keyword = extract(keywords)
  return keyword

if __name__ == "__main__":
    uvicorn.run(
        "plan:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
