from pydantic import BaseModel, ValidationError, Field
from typing import Annotated
from jsonpath_ng import parse
from datetime import datetime
import io
from jinja2 import Environment, PackageLoader, select_autoescape
from jsonref import replace_refs


env = Environment(loader=PackageLoader("formula"), autoescape=select_autoescape())
form_tpl = env.get_template("form.html")

class Item(BaseModel):
    name: str
    price: float

class Metadata(BaseModel):
    category: str
    total: float
    tags: list[Annotated[str, Field(min_length=1)]] = []

def always(x):
    return True

def path_from_validation_error_location(loc):
    res = loc[0]
    for part in loc[1:]:
        if isinstance(part, str):
            res += "." + part 
        elif isinstance(part, int):
            res += f"[{part}]"
    return res

class Form:
    def __init__(self, dataclass, state={}):
        self.dataclass = dataclass
        self.state = state
        self.errors = {}
        self.value = None

    def from_request_body(dataclass, body):
        state = {}
        for key, value in body.multi_items():
            path = parse(key)
            path.update_or_create(state, value)
        return Form(dataclass, state)

    async def from_request(dataclass, request):
        request_body = await request.form()
        form = Form.from_request_body(Receipt, request_body)

        if request_body.get("delete"):
            path = request_body["delete"]
            form.delete(path)
            return (form, "delete")
        elif request_body.get("add"):
            path = request_body["add"]
            form.add(path)
            return (form, "add")

        return form, "submit"

    def validate(self):
        try:
            self.value = self.dataclass.model_validate(self.state)
            return True
        except ValidationError as validation_error:
            self.errors = {}
            for err in validation_error.errors():
                path = path_from_validation_error_location(err['loc'])
                self.errors[path] = err['msg']
            return False

    def delete(self, path):
        expr = parse(path)
        expr.filter(always, self.state)

    def add(self, path):
        expr = parse(path)
        values = expr.find(self.state)
        value = []
        if len(values) > 0:
            value = values[0].value
        value.append("")
        expr.update_or_create(self.state, value)

    def render(self, href):
        schema = self.dataclass.model_json_schema()
        deref_schema = replace_refs(schema)
        print("rendering value:", self.state)
        return form_tpl.render(
                schema=deref_schema,
                value=self.state,
                href=href,
                errors=self.errors)

class Receipt(BaseModel):
    store: Annotated[str, Field(min_length=1)]
    date: datetime
    metadata: Metadata
    items: list[Item] = []

def empty(value):
    if isinstance(value, str):
        return value == ""
    elif isinstance(value, dict):
        # check all values
        for v in value.values():
            if not empty(value):
                return False
        return True
    elif isinstance(value, list):
        for v in value:
            if not empty(value):
                return False
        return True

metadata=Metadata(category="food", total=13.37, tags=["groceries", "expense"])
items=[
    Item(name="foo", price=12.3),
    Item(name="bar", price=32.1),
]
receipt = Receipt(store="ica", date="2025-01-01",  metadata=metadata, items=items)
f = Form(Receipt, state=receipt.model_dump())
