import reflex as rx


def results_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1("Results Page", class_name="text-4xl font-bold text-gray-800"),
        rx.el.p(
            "Charts and KPIs will be implemented in Phase 4.",
            class_name="text-gray-600 mt-4",
        ),
        class_name="flex flex-col items-center justify-center h-full p-8",
    )