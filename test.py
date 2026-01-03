from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Annotated
from datetime import datetime

from formula import formula
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "form": formula.generate_form(formula.receipt, "/")
        } 
    )

@app.delete("/")
async def delete_root(request: Request):
    try:
        f = await request.form()
        r = formula.validate_form(formula.Receipt, f)
        print(r)
    except Exception as e:
        print("no form!", e)
        pass
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "form": formula.generate_form(formula.receipt, "/")
        } 
    )
@app.post("/")
async def post_root(request: Request):
    result = formula.receipt

    try:
        f = await request.form()
        r = formula.validate_form(formula.Receipt, f)
        print(r)
        if f.get("delete"):
            delete = f["delete"]
            print("deleting:", delete)
            result = r.delete(delete)
        else:
            print("true submit")
            result = r
    except Exception as e:
        print("no form!", e)
        pass
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "form": formula.generate_form(result, "/")
        } 
    )

@app.post("/upload")
async def upload(request: Request):
    f = await request.form()
    r = formula.validate_form(Receipt, f)
    print(r)
    return "ok"
