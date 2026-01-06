from pydantic import BaseModel, ValidationError, Field
from typing import Annotated
from jsonpath_ng import parse
from datetime import datetime
import io
from jsonref import replace_refs
from . import tpl

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
    def __init__(self, dataclass, state={}, add="add", delete="delete"):
        self.dataclass = dataclass
        self.schema = self.dataclass.model_json_schema()
        self.deref_schema = replace_refs(self.schema)
        self.state = state
        self.errors = {}
        self.value = None
        self.add_button = add
        self.delete_button = delete

    def from_request_body(dataclass, body, **kwargs):
        state = {}
        for key, value in body.multi_items():
            path = parse(key)
            path.update_or_create(state, value)
        return Form(dataclass, state, **kwargs)

    async def from_request(dataclass, request, **kwargs):
        request_body = await request.form()
        form = Form.from_request_body(dataclass, request_body, **kwargs)

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
        value.append(None)
        expr.update_or_create(self.state, value)

    def render(self, href):
        print("rendering value:", self.state)
        return tpl.form.render(
                form=self,
                href=href)
