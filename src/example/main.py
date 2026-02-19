from panel.template import Template
from panel import extension, serve  # pyright: ignore[reportUnknownVariableType]

from jinja2 import Environment, PackageLoader
from example.widgets import OrangeProductionWidget


def create_orange_production_page() -> Template:
    env = Environment(loader=PackageLoader("example", ""))
    template = Template(env.get_template("orange-production.html"))

    widget = OrangeProductionWidget()

    for name, root in widget.roots().items():
        template.add_panel(name, root)

    return template

extension("echarts", "tabulator")
serve(
    panels={ "/": create_orange_production_page },
    static_dirs={"/assets": "./src/example/assets"}
)
