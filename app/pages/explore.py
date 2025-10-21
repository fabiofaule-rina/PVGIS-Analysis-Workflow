import reflex as rx
import reflex_enterprise as rxe
from app.state import AppState, ExploreState, SampleRow, GeoJSONFeature

MAP_ID = "explore-map"


def kpi_card(title: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="w-8 h-8 text-emerald-500"),
        rx.el.div(
            rx.el.h3(
                title, class_name="text-sm font-medium text-gray-500 tracking-wider"
            ),
            rx.el.p(value, class_name="text-xl font-semibold text-gray-900"),
        ),
        class_name="flex items-center gap-4 p-4 bg-white rounded-2xl shadow-sm border border-gray-100/50",
    )


def map_section() -> rx.Component:
    return rx.el.div(
        rxe.map(
            rxe.map.tile_layer(
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            ),
            rx.cond(
                ExploreState.layer_visibility["buildings"],
                rx.cond(
                    AppState.is_data_loaded,
                    rx.foreach(
                        AppState.geojson_features.to(list[GeoJSONFeature]),
                        lambda feature: rxe.map.polygon(
                            positions=feature["geometry"]["coordinates"][0]
                            .to(list[list[float]])
                            .map(lambda p: (p[1], p[0])),
                            path_options={
                                "color": "#2B79D1",
                                "weight": 2,
                                "fillColor": rx.cond(
                                    ExploreState.selected_building_id
                                    == feature["properties"]["id"],
                                    "#F3340B",
                                    "#2B79D1",
                                ),
                                "fillOpacity": 0.6,
                            },
                            on_click=ExploreState.select_building_from_map(
                                feature["properties"]["id"]
                            ),
                            key=feature["properties"]["id"],
                        ),
                    ),
                    None,
                ),
                None,
            ),
            id=MAP_ID,
            center=ExploreState.map_center,
            zoom=ExploreState.map_zoom,
            max_bounds=ExploreState.map_bounds,
            width="100%",
            height="100%",
            class_name="rounded-2xl",
        ),
        class_name="h-[60vh] w-full bg-gray-100 rounded-2xl shadow-inner border",
    )


def attribute_table() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("search", class_name="h-5 w-5 text-gray-400"),
                rx.el.input(
                    placeholder="Filter rows...",
                    on_change=ExploreState.set_table_filter,
                    class_name="w-full bg-transparent focus:outline-none",
                ),
                class_name="flex items-center gap-3 px-4 py-2 bg-white border rounded-lg shadow-sm w-full max-w-sm",
            ),
            class_name="flex justify-between items-center mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.foreach(
                                AppState.attribute_columns,
                                lambda col: rx.el.th(
                                    rx.el.button(
                                        col,
                                        rx.icon(
                                            rx.cond(
                                                ExploreState.table_sort_column == col,
                                                rx.cond(
                                                    ExploreState.table_sort_direction
                                                    == "asc",
                                                    "arrow-up",
                                                    "arrow-down",
                                                ),
                                                "chevrons-up-down",
                                            ),
                                            class_name="ml-2 h-4 w-4",
                                        ),
                                        on_click=ExploreState.sort_table(col),
                                        class_name="flex items-center gap-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                                    ),
                                    scope="col",
                                    class_name="px-6 py-3",
                                ),
                            ),
                            class_name="bg-gray-50",
                        )
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            ExploreState.paginated_explore_rows,
                            lambda row: rx.el.tr(
                                rx.foreach(
                                    AppState.attribute_columns,
                                    lambda col: rx.el.td(
                                        row["data"][col].to_string(),
                                        class_name="px-6 py-4 whitespace-nowrap text-sm text-gray-700",
                                    ),
                                ),
                                on_click=ExploreState.select_building_from_table(row),
                                class_name=rx.cond(
                                    ExploreState.selected_building_id == row["id"],
                                    "bg-emerald-100/50 cursor-pointer",
                                    "hover:bg-gray-50 cursor-pointer",
                                ),
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
                on_click=ExploreState.prev_page,
                disabled=ExploreState.current_page <= 1,
                class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50",
            ),
            rx.el.span(
                f"Page {ExploreState.current_page} of {ExploreState.explore_total_pages}",
                class_name="text-sm text-gray-700",
            ),
            rx.el.button(
                "Next",
                on_click=ExploreState.next_page,
                disabled=ExploreState.current_page >= ExploreState.explore_total_pages,
                class_name="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50",
            ),
            class_name="flex items-center justify-between mt-4",
        ),
    )


def explore_page() -> rx.Component:
    return rx.el.div(
        rx.cond(
            AppState.is_data_loaded,
            rx.el.div(
                rx.el.h1(
                    "Explore Dataset",
                    class_name="text-4xl font-bold text-gray-800 mb-2",
                ),
                rx.el.p(
                    f"Visualizing {AppState.dataset_summary['filename']}",
                    class_name="text-gray-600 mb-6",
                ),
                rx.el.div(
                    kpi_card(
                        "Total Buildings",
                        AppState.dataset_summary["feature_count"].to_string(),
                        "building-2",
                    ),
                    kpi_card(
                        "Selected Building",
                        rx.cond(
                            ExploreState.selected_building_id != None,
                            ExploreState.selected_building_id.to_string(),
                            "None",
                        ),
                        "mouse-pointer-click",
                    ),
                    kpi_card("CRS", AppState.dataset_summary["crs"], "globe"),
                    class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-6",
                ),
                map_section(),
                rx.el.div(
                    rx.el.button(
                        rx.icon("layers", class_name="mr-2 h-4 w-4"),
                        "Buildings",
                        on_click=ExploreState.toggle_layer("buildings"),
                        class_name=rx.cond(
                            ExploreState.layer_visibility["buildings"],
                            "flex items-center px-4 py-2 text-sm font-semibold text-white bg-emerald-600 rounded-lg shadow-sm hover:bg-emerald-700",
                            "flex items-center px-4 py-2 text-sm font-semibold text-gray-700 bg-white border rounded-lg hover:bg-gray-100",
                        ),
                    ),
                    rx.el.button(
                        rx.icon("sun", class_name="mr-2 h-4 w-4"),
                        "PV Potential",
                        on_click=ExploreState.toggle_layer("pv_potential"),
                        class_name=rx.cond(
                            ExploreState.layer_visibility["pv_potential"],
                            "flex items-center px-4 py-2 text-sm font-semibold text-white bg-emerald-600 rounded-lg shadow-sm hover:bg-emerald-700",
                            "flex items-center px-4 py-2 text-sm font-semibold text-gray-700 bg-white border rounded-lg hover:bg-gray-100",
                        ),
                    ),
                    class_name="flex gap-4 my-4",
                ),
                attribute_table(),
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.h1(
                    "No Data Loaded", class_name="text-4xl font-bold text-gray-800 mb-4"
                ),
                rx.el.p(
                    "Please upload a shapefile on the Upload page to explore the data.",
                    class_name="text-gray-600 mb-6",
                ),
                rx.el.a(
                    "Go to Upload Page",
                    href="/",
                    class_name="px-6 py-3 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition",
                ),
                class_name="text-center",
            ),
        ),
        class_name="flex flex-col items-center justify-center p-4 md:p-8 font-['Poppins'] w-full min-h-screen",
    )