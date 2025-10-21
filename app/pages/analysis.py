import reflex as rx
from app.state import AppState, AnalysisState, BuildingStatus


def parameter_input(
    label: str, default_value: rx.Var, on_change: rx.event.EventHandler, unit: str
) -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name="block text-sm font-medium text-gray-700 mb-1"),
        rx.el.div(
            rx.el.input(
                default_value=default_value,
                on_change=on_change,
                type="number",
                class_name="w-full p-2 border-gray-300 rounded-lg shadow-sm focus:ring-emerald-500 focus:border-emerald-500",
            ),
            rx.el.span(unit, class_name="text-sm text-gray-500 ml-2"),
            class_name="flex items-center",
        ),
    )


def analysis_controls() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Analysis Parameters", class_name="text-2xl font-bold text-gray-800 mb-4"
        ),
        rx.el.div(
            rx.el.fieldset(
                rx.el.legend(
                    "Analysis Mode", class_name="text-lg font-medium text-gray-900 mb-2"
                ),
                rx.el.div(
                    rx.el.label(
                        rx.el.input(
                            type="radio",
                            name="analysis_mode",
                            value="all",
                            on_change=AnalysisState.set_analysis_mode,
                            checked=AnalysisState.analysis_mode == "all",
                            class_name="mr-2 text-emerald-600 focus:ring-emerald-500",
                        ),
                        "All Buildings",
                        class_name="flex items-center text-sm font-medium text-gray-700",
                    ),
                    rx.el.label(
                        rx.el.input(
                            type="radio",
                            name="analysis_mode",
                            value="single",
                            on_change=AnalysisState.set_analysis_mode,
                            checked=AnalysisState.analysis_mode == "single",
                            class_name="mr-2 text-emerald-600 focus:ring-emerald-500",
                        ),
                        "Single Building",
                        class_name="flex items-center text-sm font-medium text-gray-700",
                    ),
                    class_name="flex gap-6",
                ),
            ),
            rx.cond(
                AnalysisState.analysis_mode == "single",
                rx.el.div(
                    rx.el.label(
                        "Select Building ID",
                        class_name="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    rx.el.select(
                        rx.foreach(
                            AnalysisState.building_ids_for_dropdown,
                            lambda bid: rx.el.option(bid, value=bid.to_string()),
                        ),
                        placeholder="Select a building...",
                        on_change=AnalysisState.set_selected_building,
                        class_name="w-full p-2 border-gray-300 rounded-lg shadow-sm focus:ring-emerald-500 focus:border-emerald-500",
                    ),
                    class_name="mt-4",
                ),
                None,
            ),
            class_name="p-6 bg-white rounded-2xl shadow-sm border border-gray-100/50",
        ),
        rx.el.div(
            parameter_input("Tilt", AnalysisState.tilt, AnalysisState.set_tilt, "°"),
            parameter_input(
                "Azimuth", AnalysisState.azimuth, AnalysisState.set_azimuth, "°"
            ),
            parameter_input(
                "PV System Size", AnalysisState.pv_kwp, AnalysisState.set_pv_kwp, "kWp"
            ),
            parameter_input(
                "System Losses", AnalysisState.losses, AnalysisState.set_losses, "%"
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6 p-6 bg-white rounded-2xl shadow-sm border border-gray-100/50",
        ),
        rx.el.button(
            rx.icon("play", class_name="mr-2"),
            "Start Analysis",
            on_click=AnalysisState.start_analysis,
            disabled=AnalysisState.is_analyzing,
            class_name="w-full mt-8 flex items-center justify-center px-8 py-4 text-lg font-semibold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed",
        ),
        class_name="w-full max-w-4xl",
    )


def progress_section() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Analysis in Progress...",
            class_name="text-2xl font-bold text-gray-800 mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Overall Progress", class_name="text-sm font-medium text-gray-700"
                ),
                rx.el.p(
                    f"{AnalysisState.analysis_progress}%",
                    class_name="text-sm font-semibold text-emerald-600",
                ),
                class_name="flex justify-between items-center mb-2",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="bg-emerald-500 h-2.5 rounded-full",
                    style={"width": f"{AnalysisState.analysis_progress}%"},
                ),
                class_name="w-full bg-gray-200 rounded-full h-2.5",
            ),
        ),
        rx.el.div(
            rx.el.h3(
                "Building Status",
                class_name="text-lg font-semibold text-gray-800 mt-6 mb-2",
            ),
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th(
                                "Building ID",
                                class_name="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase",
                            ),
                            rx.el.th(
                                "Status",
                                class_name="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase",
                            ),
                            rx.el.th(
                                "Message",
                                class_name="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase",
                            ),
                        )
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            AnalysisState.building_status,
                            lambda status: rx.el.tr(
                                rx.el.td(
                                    status["building_id"].to_string(),
                                    class_name="px-4 py-2 text-sm text-gray-800",
                                ),
                                rx.el.td(
                                    rx.el.span(
                                        status["status"],
                                        class_name=rx.match(
                                            status["status"],
                                            (
                                                "Completed",
                                                "px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full",
                                            ),
                                            (
                                                "Cached",
                                                "px-2 py-1 text-xs font-semibold text-blue-800 bg-blue-100 rounded-full",
                                            ),
                                            (
                                                "Error",
                                                "px-2 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full",
                                            ),
                                            "px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 rounded-full",
                                        ),
                                    ),
                                    class_name="px-4 py-2 text-sm",
                                ),
                                rx.el.td(
                                    status["message"],
                                    class_name="px-4 py-2 text-sm text-gray-600 font-mono",
                                ),
                                class_name="border-t border-gray-200",
                            ),
                        )
                    ),
                    class_name="min-w-full bg-white",
                ),
                class_name="w-full max-h-96 overflow-y-auto rounded-lg border border-gray-200 shadow-sm",
            ),
        ),
        rx.el.button(
            "Stop Analysis",
            on_click=AnalysisState.stop_analysis,
            class_name="mt-6 w-full flex items-center justify-center px-6 py-3 text-md font-semibold text-white bg-red-600 rounded-xl hover:bg-red-700 transition-all shadow-md",
        ),
        class_name="w-full max-w-4xl p-8 bg-gray-50 rounded-2xl border border-gray-200 animate-fade-in",
    )


def analysis_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1(
            "PV Analysis Dashboard", class_name="text-4xl font-bold text-gray-800 mb-2"
        ),
        rx.el.p(
            "Configure and run PV potential analysis on your dataset.",
            class_name="text-gray-600 mb-8",
        ),
        rx.cond(
            AppState.is_data_loaded,
            rx.cond(
                AnalysisState.is_analyzing, progress_section(), analysis_controls()
            ),
            rx.el.div(
                rx.el.h2(
                    "No Data Loaded", class_name="text-2xl font-bold text-gray-800 mb-4"
                ),
                rx.el.p(
                    "Please upload a shapefile on the Upload page to run analysis.",
                    class_name="text-gray-600 mb-6",
                ),
                rx.el.a(
                    "Go to Upload Page",
                    href="/",
                    class_name="px-6 py-3 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition",
                ),
                class_name="text-center p-8 bg-white rounded-2xl shadow-sm border",
            ),
        ),
        class_name="flex flex-col items-center p-4 md:p-8 font-['Poppins'] w-full min-h-screen",
    )