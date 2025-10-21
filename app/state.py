import reflex as rx
from typing import TypedDict, cast, Any, Literal
import asyncio
import zipfile
import io
import geopandas as gpd
from shapely.geometry import box
import os
import logging
from reflex_enterprise.components.map.types import LatLng, latlng


class DatasetSummary(TypedDict):
    filename: str
    feature_count: int
    crs: str | None
    bounds: tuple[float, float, float, float] | None
    schema: dict[str, str]


class SampleRow(TypedDict):
    id: int
    data: dict[str, str | int | float | None]


class PolygonGeometry(TypedDict):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class GeoJSONFeature(TypedDict):
    type: Literal["Feature"]
    properties: dict[str, str | int | float | None]
    geometry: PolygonGeometry


class GeoJSON(TypedDict):
    type: Literal["FeatureCollection"]
    features: list[GeoJSONFeature]


class PVResult(TypedDict):
    pv_potential_kwh: float
    pv_kwp: float
    yield_kwh_per_kwp: float
    confidence: float
    monthly_series: list[float]
    dev_mode: bool


class BuildingStatus(TypedDict):
    building_id: int
    status: str
    message: str


class AppState(rx.State):
    is_uploading: bool = False
    upload_progress: int = 0
    upload_error: str = ""
    dataset_summary: DatasetSummary | None = None
    geojson_data: GeoJSON | None = None
    sample_rows: list[SampleRow] = []
    current_page: int = 1
    rows_per_page: int = 10
    analysis_results: dict[int, PVResult] = {}
    analysis_cache: dict[str, PVResult] = {}

    @rx.var
    def is_data_loaded(self) -> bool:
        return self.dataset_summary is not None

    @rx.var
    def total_pages(self) -> int:
        if not self.sample_rows:
            return 1
        return (len(self.sample_rows) + self.rows_per_page - 1) // self.rows_per_page

    @rx.var
    def paginated_rows(self) -> list[SampleRow]:
        start = (self.current_page - 1) * self.rows_per_page
        end = start + self.rows_per_page
        return self.sample_rows[start:end]

    @rx.var
    def attribute_columns(self) -> list[str]:
        if not self.dataset_summary or not self.dataset_summary["schema"]:
            return []
        return list(self.dataset_summary["schema"].keys())

    @rx.var
    def geojson_features(self) -> list[GeoJSONFeature]:
        if not self.geojson_data:
            return []
        return self.geojson_data.get("features", [])

    @rx.event
    async def next_page(self):
        explore_state = await self.get_state(ExploreState)
        total_pages = self.total_pages
        if self.router.page.path == "/explore":
            total_pages = explore_state.explore_total_pages
        if self.current_page < total_pages:
            self.current_page += 1

    @rx.event
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            yield rx.toast.error("No file selected for upload.", duration=5000)
            return
        self.is_uploading = True
        self.upload_progress = 0
        self.upload_error = ""
        self.dataset_summary = None
        self.geojson_data = None
        self.sample_rows = []
        self.current_page = 1
        yield
        file = files[0]
        if not file.name.lower().endswith(".zip"):
            self.is_uploading = False
            self.upload_error = "Invalid file type. Please upload a .ZIP file."
            yield rx.toast.error(self.upload_error, duration=5000)
            return
        try:
            upload_data = await file.read()
            self.upload_progress = 20
            yield
            await asyncio.sleep(0.5)
            with zipfile.ZipFile(io.BytesIO(upload_data)) as zf:
                required_ext = {".shp", ".shx", ".dbf", ".prj"}
                found_ext = {os.path.splitext(f)[1].lower() for f in zf.namelist()}
                if not required_ext.issubset(found_ext):
                    missing = required_ext - found_ext
                    self.is_uploading = False
                    self.upload_error = (
                        f"ZIP is missing required files: {', '.join(missing)}"
                    )
                    yield rx.toast.error(self.upload_error, duration=5000)
                    return
                self.upload_progress = 40
                yield
                shp_path = next(
                    (f for f in zf.namelist() if f.lower().endswith(".shp"))
                )
                gdf = gpd.read_file(
                    f"zip://{file.name}!{shp_path}",
                    vfs="zip",
                    zipfile=io.BytesIO(upload_data),
                )
            self.upload_progress = 60
            yield
            await asyncio.sleep(0.5)
            gdf_reprojected = gdf.to_crs(epsg=4326)
            gdf_reprojected["id"] = range(len(gdf_reprojected))
            bounds = gdf_reprojected.total_bounds
            schema = {
                col: str(gdf_reprojected[col].dtype)
                for col in gdf_reprojected.columns
                if col != "geometry"
            }
            self.dataset_summary = {
                "filename": file.name,
                "feature_count": len(gdf_reprojected),
                "crs": str(gdf_reprojected.crs),
                "bounds": (
                    round(bounds[0], 4),
                    round(bounds[1], 4),
                    round(bounds[2], 4),
                    round(bounds[3], 4),
                ),
                "schema": schema,
            }
            self.upload_progress = 80
            yield
            explore_state = await self.get_state(ExploreState)
            explore_state.map_bounds = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]
            explore_state.selected_building_id = None
            self.geojson_data = cast(GeoJSON, gdf_reprojected.__geo_interface__)
            for i, feature in enumerate(self.geojson_data["features"]):
                feature["properties"]["id"] = i
            all_rows_df = gdf_reprojected.drop(columns="geometry")
            self.sample_rows = []
            for i, row in all_rows_df.iterrows():
                row_data = {k: str(v) for k, v in row.to_dict().items()}
                self.sample_rows.append({"id": int(row_data["id"]), "data": row_data})
            self.upload_progress = 100
            yield
            await asyncio.sleep(0.5)
        except Exception as e:
            logging.exception(f"File processing error: {e}")
            self.is_uploading = False
            self.upload_error = f"Processing failed: {e}"
            yield rx.toast.error(
                f"An unexpected error occurred during file processing.", duration=8000
            )
            return
        self.is_uploading = False
        yield rx.toast.success("Shapefile processed successfully!", duration=5000)

    @rx.event
    def open_map(self):
        self.current_page = 1
        return rx.redirect("/explore")


class SidebarState(rx.State):
    @rx.var
    def path(self) -> str:
        return self.router.page.path


class AnalysisState(rx.State):
    analysis_mode: Literal["all", "single"] = "all"
    selected_building_for_analysis: int | None = None
    tilt: float = 35.0
    azimuth: float = 180.0
    pv_kwp: float = 5.0
    losses: float = 14.0
    is_analyzing: bool = False
    analysis_progress: int = 0
    building_status: list[BuildingStatus] = []
    _stop_analysis_flag: bool = False

    @rx.var
    async def building_ids_for_dropdown(self) -> list[int]:
        app_state = await self.get_state(AppState)
        if not app_state.sample_rows:
            return []
        return [row["id"] for row in app_state.sample_rows]

    @rx.event
    def set_analysis_mode(self, mode: Literal["all", "single"]):
        self.analysis_mode = mode

    @rx.event
    def set_selected_building(self, building_id_str: str):
        if building_id_str:
            self.selected_building_for_analysis = int(building_id_str)

    def _get_cache_key(self, building_id: int) -> str:
        return f"{building_id}-{self.tilt}-{self.azimuth}-{self.pv_kwp}-{self.losses}"

    @rx.event(background=True)
    async def start_analysis(self):
        from app.pvgis_analyzer import analyze_building

        async with self:
            self.is_analyzing = True
            self.analysis_progress = 0
            self.building_status = []
            self._stop_analysis_flag = False
            app_state = await self.get_state(AppState)
            buildings_to_analyze = []
            if self.analysis_mode == "all":
                buildings_to_analyze = app_state.sample_rows
            elif self.selected_building_for_analysis is not None:
                building = next(
                    (
                        row
                        for row in app_state.sample_rows
                        if row["id"] == self.selected_building_for_analysis
                    ),
                    None,
                )
                if building:
                    buildings_to_analyze = [building]
            if not buildings_to_analyze:
                self.is_analyzing = False
                yield rx.toast.error("No buildings selected for analysis.")
                return
        total_buildings = len(buildings_to_analyze)
        for i, building_row in enumerate(buildings_to_analyze):
            async with self:
                if self._stop_analysis_flag:
                    self.is_analyzing = False
                    yield rx.toast.info("Analysis stopped by user.")
                    return
                building_id = building_row["id"]
                self.building_status.append(
                    {
                        "building_id": building_id,
                        "status": "Processing",
                        "message": "Starting...",
                    }
                )
            yield
            try:
                cache_key = self._get_cache_key(building_id)
                async with self:
                    app_state = await self.get_state(AppState)
                    if cache_key in app_state.analysis_cache:
                        result = app_state.analysis_cache[cache_key]
                        self.building_status[-1] = {
                            "building_id": building_id,
                            "status": "Cached",
                            "message": "Result from cache.",
                        }
                        app_state.analysis_results[building_id] = result
                        self.analysis_progress = int((i + 1) / total_buildings * 100)
                        yield
                        continue
                feature = next(
                    (
                        f
                        for f in app_state.geojson_data["features"]
                        if f["properties"]["id"] == building_id
                    ),
                    None,
                )
                if not feature or feature["geometry"]["type"] != "Polygon":
                    raise ValueError("Building geometry not found or invalid.")
                coords = feature["geometry"]["coordinates"][0]
                lon = sum((p[0] for p in coords)) / len(coords)
                lat = sum((p[1] for p in coords)) / len(coords)
                result = analyze_building(
                    lat, lon, self.tilt, self.azimuth, self.pv_kwp, self.losses
                )
                async with self:
                    app_state = await self.get_state(AppState)
                    app_state.analysis_results[building_id] = result
                    app_state.analysis_cache[cache_key] = result
                    self.building_status[-1] = {
                        "building_id": building_id,
                        "status": "Completed",
                        "message": f"{result['pv_potential_kwh']:,} kWh/yr",
                    }
            except Exception as e:
                logging.exception(f"Analysis for building {building_id} failed: {e}")
                async with self:
                    self.building_status[-1] = {
                        "building_id": building_id,
                        "status": "Error",
                        "message": str(e),
                    }
            finally:
                async with self:
                    self.analysis_progress = int((i + 1) / total_buildings * 100)
                yield
        async with self:
            self.is_analyzing = False
            yield rx.toast.success("Analysis complete!")

    @rx.event
    def stop_analysis(self):
        self._stop_analysis_flag = True


class ExploreState(rx.State):
    selected_building_id: int | None = None
    table_filter: str = ""
    layer_visibility: dict[str, bool] = {"buildings": True, "pv_potential": False}
    map_center: LatLng = latlng(lat=39.8283, lng=-98.5795)
    map_zoom: float = 4.0
    map_bounds: list[list[float]] | None = None
    table_sort_column: str | None = None
    table_sort_direction: str = "asc"

    @rx.var
    async def filtered_rows(self) -> list[SampleRow]:
        app_state = await self.get_state(AppState)
        rows = app_state.sample_rows
        if not self.table_filter:
            return rows
        search_term = self.table_filter.lower()
        return [
            row
            for row in rows
            if any((search_term in str(val).lower() for val in row["data"].values()))
        ]

    @rx.var
    async def sorted_and_filtered_rows(self) -> list[SampleRow]:
        rows = await self.get_var_value(self.filtered_rows)
        if not self.table_sort_column:
            return rows
        sort_column = self.table_sort_column

        @rx.event
        def sort_key(row):
            val = row["data"].get(sort_column)
            if val is None:
                return (
                    -float("inf")
                    if self.table_sort_direction == "asc"
                    else float("inf")
                )
            try:
                return float(val)
            except (ValueError, TypeError) as e:
                logging.exception(f"Could not convert to float for sorting: {e}")
                return str(val)

        try:
            return sorted(
                rows, key=sort_key, reverse=self.table_sort_direction == "desc"
            )
        except Exception as e:
            logging.exception(f"Error sorting table: {e}")
            return rows

    @rx.var
    async def current_page(self) -> int:
        app_state = await self.get_state(AppState)
        return app_state.current_page

    @rx.var
    async def rows_per_page(self) -> int:
        app_state = await self.get_state(AppState)
        return app_state.rows_per_page

    @rx.var
    async def paginated_explore_rows(self) -> list[SampleRow]:
        sorted_rows = await self.get_var_value(self.sorted_and_filtered_rows)
        page = await self.get_var_value(self.current_page)
        per_page = await self.get_var_value(self.rows_per_page)
        start = (page - 1) * per_page
        end = start + per_page
        return sorted_rows[start:end]

    @rx.var
    async def explore_total_pages(self) -> int:
        filtered_rows = await self.get_var_value(self.filtered_rows)
        per_page = await self.get_var_value(self.rows_per_page)
        if not filtered_rows:
            return 1
        return (len(filtered_rows) + per_page - 1) // per_page

    @rx.event
    async def next_page(self):
        app_state = await self.get_state(AppState)
        return app_state.next_page

    @rx.event
    async def prev_page(self):
        app_state = await self.get_state(AppState)
        return app_state.prev_page

    @rx.event
    def toggle_layer(self, layer_name: str):
        self.layer_visibility[layer_name] = not self.layer_visibility[layer_name]
        yield rx.toast.info(f"{layer_name.title()} layer toggled.")

    @rx.event
    def select_building_from_map(self, feature_id: int):
        self.selected_building_id = feature_id
        yield rx.toast.info(f"Building {feature_id} selected.")

    @rx.event
    async def select_building_from_table(self, row: SampleRow):
        self.selected_building_id = row["id"]
        app_state = await self.get_state(AppState)
        if app_state.geojson_data:
            feature = next(
                (
                    f
                    for f in app_state.geojson_data["features"]
                    if f["properties"].get("id") == row["id"]
                ),
                None,
            )
            if feature and feature["geometry"]["type"] == "Polygon":
                coords = feature["geometry"]["coordinates"][0]
                lats = [c[1] for c in coords]
                lons = [c[0] for c in coords]
                centroid_lat = sum(lats) / len(lats)
                centroid_lon = sum(lons) / len(lons)
                self.map_center = latlng(lat=centroid_lat, lng=centroid_lon)
                self.map_zoom = 18.0
                yield rx.toast.info(f"Zooming to Building {row['id']}")

    @rx.event
    async def sort_table(self, column_name: str):
        if self.table_sort_column == column_name:
            self.table_sort_direction = (
                "asc" if self.table_sort_direction == "desc" else "desc"
            )
        else:
            self.table_sort_column = column_name
            self.table_sort_direction = "asc"
        app_state = await self.get_state(AppState)
        app_state.current_page = 1
        yield