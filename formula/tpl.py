from jinja2 import Environment, PackageLoader, select_autoescape
from pydantic import BaseModel
from jsonref import replace_refs

env = Environment(
    loader=PackageLoader("formula"),
    autoescape=select_autoescape()
)

form = env.get_template("form.html")
