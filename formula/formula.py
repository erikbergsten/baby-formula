from pydantic import BaseModel
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
    tags: list[str]

def always(x):
    return True

class FormModel(BaseModel):

    def delete(self, path):
        expr = parse(path)
        dump = self.model_dump()
        updated = expr.filter(always, dump)
        return self.model_validate(updated)

class Receipt(FormModel):
    store: str
    date: datetime
    metadata: Metadata
    items: list[Item] = []

def empty(value):
    if isinstance(value, str):
        return value == ""
    elif isinstance(value, dict):
        # check all values
        for v in value.values():
            if value != "":
                return True
        return False
    elif isinstance(value, list):
        for v in value:
            if value != "":
                return True
        return False

def build_dict_from_form(form):
    d = {}
    for key, value in form.multi_items():
        path = parse(key)
        if value != "":
            path.update_or_create(d, value)
    return d

def validate_form(dataclass, form):
    d = build_dict_from_form(form)
    print("dict:", d)
    return dataclass.model_validate(d)

def generate_form(value, href):
    schema = value.model_json_schema()
    deref_schema = replace_refs(schema)
    return form_tpl.render(schema=deref_schema, value=value, href=href)

metadata=Metadata(category="food", total=13.37, tags=["groceries", "expense"])

items=[
    Item(name="foo", price=12.3),
    Item(name="bar", price=32.1),
]
receipt = Receipt(store="ica", date="2025-01-01",  metadata=metadata, items=items)
