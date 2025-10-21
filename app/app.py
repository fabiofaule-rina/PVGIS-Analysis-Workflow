import reflex as rx
import reflex_enterprise as rxe
from app.components.sidebar import sidebar
from app.pages.upload import upload_page
from app.pages.explore import explore_page
from app.pages.analysis import analysis_page
from app.pages.results import results_page
from app.pages.admin import admin_page


def index() -> rx.Component:
    return upload_page()


def base_layout(child_page: rx.Component) -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.main(child_page, class_name="flex-1 overflow-auto bg-gray-50"),
        class_name="flex h-screen w-screen bg-white",
    )


app = rxe.App(
    theme=rx.theme(appearance="light", accent_color="green", radius="large"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(lambda: base_layout(index()), route="/")
app.add_page(lambda: base_layout(explore_page()), route="/explore")
app.add_page(lambda: base_layout(analysis_page()), route="/analysis")
app.add_page(lambda: base_layout(results_page()), route="/results")
app.add_page(lambda: base_layout(admin_page()), route="/admin")