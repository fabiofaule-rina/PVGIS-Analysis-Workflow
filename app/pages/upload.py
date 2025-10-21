import reflex as rx
import reflex_enterprise as rxe
from app.state import AppState, SampleRow


def kpi_card(title: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                title, class_name="text-sm font-medium text-gray-500 tracking-wider"
            ),
            rx.el.p(value, class_name="text-2xl font-semibold text-gray-900"),
            class_name="flex-1",
        ),
        rx.icon(icon, class_name="w-8 h-8 text-emerald-500"),
        class_name="flex items-center p-6 bg-white rounded-2xl shadow-sm border border-gray-100/50",
    )


def summary_section() -> rx.Component:
    return rx.el.div(
        rx.el.h2("Dataset Summary", class_name="text-2xl font-bold text-gray-800 mb-4"),
        rx.el.div(
            kpi_card(
                "Features",
                AppState.dataset_summary["feature_count"].to_string(),
                "list-checks",
            ),
            kpi_card("CRS", AppState.dataset_summary["crs"], "globe"),
            rx.el.div(
                rx.el.h3(
                    "Bounding Box",
                    class_name="text-sm font-medium text-gray-500 tracking-wider",
                ),
                rx.el.p(
                    AppState.dataset_summary["bounds"].to_string(),
                    class_name="text-lg font-semibold text-gray-900 mt-2",
                ),
                class_name="col-span-1 md:col-span-2 p-6 bg-white rounded-2xl shadow-sm border border-gray-100/50",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-6",
        ),
        class_name="p-8 bg-gray-50 rounded-2xl border border-gray-200",
    )


def schema_table() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Attribute Schema", class_name="text-2xl font-bold text-gray-800 mb-4"
        ),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th(
                            "Field Name",
                            class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                        ),
                        rx.el.th(
                            "Data Type",
                            class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                        ),
                        class_name="bg-gray-50",
                    )
                ),
                rx.el.tbody(
                    rx.foreach(
                        AppState.dataset_summary["schema"].items(),
                        lambda item: rx.el.tr(
                            rx.el.td(
                                item[0],
                                class_name="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900",
                            ),
                            rx.el.td(
                                item[1],
                                class_name="px-6 py-4 whitespace-nowrap text-sm text-gray-500",
                            ),
                            class_name="border-b border-gray-200",
                        ),
                    ),
                    class_name="bg-white",
                ),
                class_name="min-w-full divide-y divide-gray-200",
            ),
            class_name="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg",
        ),
    )


def sample_rows_table() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Sample Rows (First 50)", class_name="text-2xl font-bold text-gray-800 mb-4"
        ),
        rx.el.div(
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.foreach(
                                AppState.attribute_columns,
                                lambda col: rx.el.th(
                                    col,
                                    scope="col",
                                    class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                                ),
                            ),
                            class_name="bg-gray-50",
                        )
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            AppState.paginated_rows,
                            lambda row: rx.el.tr(
                                rx.foreach(
                                    AppState.attribute_columns,
                                    lambda col: rx.el.td(
                                        row["data"][col].to_string(),
                                        class_name="px-6 py-4 whitespace-nowrap text-sm text-gray-700",
                                    ),
                                )
                            ),
                        ),
                        class_name="bg-white divide-y divide-gray-200",
                    ),
                    class_name="min-w-full divide-y divide-gray-200",
                ),
                class_name="overflow-x-auto",
            ),
            class_name="shadow border-b border-gray-200 sm:rounded-lg",
        ),
        rx.el.div(
            rx.el.button(
                "Previous",
                on_click=AppState.prev_page,
                disabled=AppState.current_page <= 1,
                class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50",
            ),
            rx.el.span(
                f"Page {AppState.current_page} of {AppState.total_pages}",
                class_name="text-sm text-gray-700",
            ),
            rx.el.button(
                "Next",
                on_click=AppState.next_page,
                disabled=AppState.current_page >= AppState.total_pages,
                class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50",
            ),
            class_name="flex items-center justify-between mt-4",
        ),
    )


@rx.memo
def drop_target_component() -> rx.Component:
    drop_params = rxe.dnd.DropTarget.collected_params
    is_over = drop_params.is_over
    can_drop = drop_params.can_drop
    return rxe.dnd.drop_target(
        rx.el.label(
            rx.el.div(
                rx.icon("cloud_upload", class_name="w-16 h-16 text-gray-400 mb-4"),
                rx.el.h3(
                    "Drag & drop a .zip file here",
                    class_name="text-lg font-semibold text-gray-700",
                ),
                rx.el.p(
                    "or click to select a file", class_name="text-sm text-gray-500 mt-1"
                ),
                rx.el.p("(Max 50MB)", class_name="text-xs text-gray-400 mt-2"),
                class_name="flex flex-col items-center justify-center p-12 text-center",
            ),
            rx.upload.root(
                rx.el.input(type="file", class_name="hidden"),
                id="zip_upload",
                accept={"application/zip": [".zip"]},
                max_files=1,
                max_size=50 * 1024 * 1024,
                class_name="hidden",
            ),
            class_name=rx.cond(
                is_over & can_drop,
                "relative block w-full rounded-2xl border-2 border-dashed border-emerald-400 bg-emerald-50 cursor-pointer",
                "relative block w-full rounded-2xl border-2 border-dashed border-gray-300 bg-white hover:border-gray-400 transition-colors cursor-pointer",
            ),
            html_for="zip_upload",
        ),
        accept=["Files"],
        on_drop=AppState.handle_upload(rx.upload_files(upload_id="zip_upload")),
    )


def upload_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1("Upload Dataset", class_name="text-4xl font-bold text-gray-800 mb-2"),
        rx.el.p(
            "Upload a zipped shapefile containing building footprints to begin analysis.",
            class_name="text-gray-600 mb-8",
        ),
        rx.cond(
            AppState.is_uploading,
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        "Processing your file...",
                        class_name="text-lg font-medium text-gray-700",
                    ),
                    rx.el.p(
                        f"{AppState.upload_progress}%",
                        class_name="text-sm text-emerald-600 font-semibold",
                    ),
                    class_name="flex justify-between items-center mb-2",
                ),
                rx.el.div(
                    rx.el.div(
                        class_name="bg-emerald-500 h-2.5 rounded-full",
                        style={"width": f"{AppState.upload_progress}%"},
                    ),
                    class_name="w-full bg-gray-200 rounded-full h-2.5",
                ),
                class_name="w-full max-w-md p-8 bg-white rounded-2xl shadow-lg border border-gray-200",
            ),
            rx.cond(
                AppState.is_data_loaded,
                rx.el.div(
                    summary_section(),
                    schema_table(),
                    sample_rows_table(),
                    rx.el.button(
                        "Proceed to Map",
                        rx.icon("arrow_right", class_name="ml-2"),
                        on_click=AppState.open_map,
                        class_name="mt-8 w-full flex items-center justify-center px-8 py-4 text-lg font-semibold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 transition-all shadow-md hover:shadow-lg",
                    ),
                    class_name="w-full space-y-8 animate-fade-in",
                ),
                rx.el.div(
                    drop_target_component(),
                    rx.foreach(
                        rx.selected_files("zip_upload"),
                        lambda file: rx.el.div(
                            rx.el.p(
                                file, class_name="text-sm text-gray-700 font-medium"
                            ),
                            rx.el.button(
                                "Process File",
                                on_click=AppState.handle_upload(
                                    rx.upload_files(upload_id="zip_upload")
                                ),
                                class_name="mt-4 px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition font-semibold",
                            ),
                            class_name="mt-4 text-center",
                        ),
                    ),
                    rx.cond(
                        AppState.upload_error != "",
                        rx.el.div(
                            rx.icon(
                                "flag_triangle_right",
                                class_name="w-5 h-5 text-red-500 mr-2",
                            ),
                            rx.el.p(
                                AppState.upload_error,
                                class_name="text-sm text-red-600 font-medium",
                            ),
                            class_name="flex items-center justify-center mt-4 p-3 bg-red-50 rounded-lg border border-red-200",
                        ),
                        None,
                    ),
                    class_name="w-full max-w-2xl",
                ),
            ),
        ),
        class_name="flex flex-col items-center justify-center p-4 md:p-8 font-['Poppins'] w-full",
    )