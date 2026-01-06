from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("baby_formula"),
    autoescape=select_autoescape()
)

form = env.get_template("form.html")

