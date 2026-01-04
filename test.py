from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Annotated
from datetime import datetime

from formula.formula import Form, Receipt, f
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "form": f.render("/")
        } 
    )

@app.post("/")
async def post_root(request: Request):
    form, action = await Form.from_request(Receipt, request)
    if action == "delete":
        print("user deleted?")
    elif action == "submit":
        print("submit attemped!")
        if form.validate():
            # success - perform action
            print("very good!")
        else:
            # failed - render with errors
            print("very bad!")

    return templates.TemplateResponse(
        request=request, name="index.html", context={
            "form": form.render("/")
        } 
    )

@app.post("/upload")
async def upload(request: Request):
    f = await request.form()
    r = formula.validate_form(Receipt, f)
    print(r)
    return "ok"
