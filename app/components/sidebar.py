import reflex as rx
from app.state import AppState, SidebarState


def nav_item(text: str, href: str, icon: str, is_active: rx.Var[bool]) -> rx.Component:
    return rx.el.a(
        rx.el.li(
            rx.icon(icon, class_name="w-5 h-5"),
            rx.el.span(text, class_name="font-medium"),
            class_name=rx.cond(
                is_active,
                "flex items-center gap-3 rounded-lg px-3 py-2 text-emerald-600 bg-emerald-50 transition-all hover:text-emerald-700",
                "flex items-center gap-3 rounded-lg px-3 py-2 text-gray-500 transition-all hover:text-gray-900",
            ),
        ),
        href=href,
    )


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    rx.icon("wind", class_name="h-8 w-8 text-emerald-600"),
                    rx.el.span("SolarAnalyse", class_name="sr-only"),
                    href="/",
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1("SolarAnalyse", class_name="text-lg font-bold text-gray-800"),
                class_name="flex items-center gap-4 px-4 h-16 border-b",
            ),
            rx.el.nav(
                rx.el.ul(
                    nav_item("Upload", "/", "cloud_upload", SidebarState.path == "/"),
                    nav_item(
                        "Explore", "/explore", "map", SidebarState.path == "/explore"
                    ),
                    nav_item(
                        "Analysis",
                        "/analysis",
                        "activity",
                        SidebarState.path == "/analysis",
                    ),
                    nav_item(
                        "Results",
                        "/results",
                        "bar-chart-3",
                        SidebarState.path == "/results",
                    ),
                    class_name="grid gap-1 p-2 text-sm",
                ),
                class_name="flex-1 overflow-auto py-2",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h3("Admin", class_name="font-semibold"),
                    class_name="px-4 py-2 text-sm",
                ),
                rx.el.ul(
                    nav_item(
                        "Settings", "/admin", "settings", SidebarState.path == "/admin"
                    ),
                    class_name="grid gap-1 p-2 text-sm",
                ),
                class_name="mt-auto border-t",
            ),
            class_name="flex h-full max-h-screen flex-col gap-2",
        ),
        class_name="hidden border-r bg-gray-50/50 md:block w-64 font-['Poppins']",
    )