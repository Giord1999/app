import json
import base64
import io
from loan import DbManager
from loan_crm import LoanCRM
from loan_report import LoanReport
import time
import threading
import matplotlib.pyplot as plt
from matplotlib import cm
from dataclasses import dataclass
from typing import Dict, Any, Optional
from functools import lru_cache
import concurrent.futures
import threading
import time
import json
from typing import Dict, Any, Optional, Callable
import os
from folium.plugins import Fullscreen, MousePosition, Draw

@dataclass
class CacheItem:
    """Data structure to hold cached items with expiration time"""
    data: Any
    timestamp: float
    ttl: int  # Time to live in seconds

class DashboardData:
    """
    Classe per aggregare e preparare tutte le metriche e i dati utili per la dashboard.
    """
    def __init__(self, db_manager: DbManager):
        self.db_manager = db_manager
        self.loan_crm = LoanCRM(db_manager)
        self.loan_report = LoanReport(db_manager, self.loan_crm)
        self._cache = {}  # Component-specific cache
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        # Configure cache TTLs (in seconds)
        self.cache_ttls = {
            "loan_metrics": 300,  # 5 minutes
            "crm_metrics": 600,   # 10 minutes
            "client_segmentation": 3600,  # 1 hour (rarely changes)
            "forecasting_data": 3600,     # 1 hour
            "charts": 3600         # 15 minutes
        }
        self._chart_cache = {}  # Cache for generated charts
        self._thread_local = threading.local()  # For thread-local DB connections
        self._temp_files = []  # List to keep track of temporary files for cleanup
        
        # Check for required packages on initialization
        self._check_required_packages()
        
        # Try to preload shapefile paths to cache them
        try:
            self._resolve_shapefile_path("georef-italy-provincia-millesime.shp", required=False)
            self._resolve_shapefile_path("Com01012025_g_WGS84.shp", required=False)
        except:
            pass  # Ignore errors during initialization
        
    def get_all_data(self, priority_only=False, render_charts=True):
        """
        Get all dashboard data with prioritization option
        
        Args:
            priority_only: If True, returns only high-priority metrics for initial load
        """
        # Force a cache reset to ensure fresh data
        self.clear_cache()
        
        # Basic error data
        error_data = {"error": "No data available", "is_error": True}
        
        # Rather than using concurrent execution, fetch sequentially to avoid cursor issues
        try:
            # First, get critical metrics
            loan_metrics = self.get_loan_metrics() or error_data.copy()
                        
            # Normalize metrics from report format to dashboard format
            if "Total Loans" in loan_metrics:
                loan_metrics["Total Loan Count"] = loan_metrics["Total Loans"]
                loan_metrics["total_loans"] = loan_metrics["Total Loans"]

            if "Average Loan Amount" not in loan_metrics and "Total Loan Amount" in loan_metrics and "Total Loans" in loan_metrics and loan_metrics["Total Loans"] > 0:
                loan_metrics["Average Loan Amount"] = loan_metrics["Total Loan Amount"] / loan_metrics["Total Loans"]
                loan_metrics["average_loan_amount"] = loan_metrics["Average Loan Amount"]

            # Add missing amortization counts if needed
            if "French Amortization Count" not in loan_metrics:
                loan_metrics["French Amortization Count"] = 0
            loan_metrics["french_amortization_count"] = loan_metrics["French Amortization Count"]

            if "Italian Amortization Count" not in loan_metrics:
                loan_metrics["Italian Amortization Count"] = 0
            loan_metrics["italian_amortization_count"] = loan_metrics["Italian Amortization Count"]

            if "Average Loan Term" not in loan_metrics:
                loan_metrics["Average Loan Term"] = 0
            loan_metrics["average_loan_term"] = loan_metrics["Average Loan Term"]   
                     
            if priority_only:
                return {"loan_metrics": loan_metrics}
            
            # Then get the rest
            try:
                crm_metrics = self.get_crm_metrics() or error_data.copy()
                
                # Normalizzazione e duplicazione delle chiavi CRM
                if "total_clients" in crm_metrics:
                    crm_metrics["Total Clients"] = crm_metrics["total_clients"]
                    
                if "total_interactions" in crm_metrics:
                    crm_metrics["Total Interactions"] = crm_metrics["total_interactions"]
                    
            except Exception as e:
                print(f"Error getting CRM metrics: {e}")
                crm_metrics = error_data.copy()
                
            try:
                client_segmentation = self.get_client_segmentation() or error_data.copy()
            except Exception as e:
                print(f"Error getting client segmentation: {e}")
                client_segmentation = error_data.copy()
                
            try:
                forecasting_data = self.get_forecasting_data() or error_data.copy()
            except Exception as e:
                print(f"Error getting forecasting data: {e}")
                forecasting_data = error_data.copy()
            
            # Prepare result
            data = {
                "loan_metrics": loan_metrics,
                "crm_metrics": crm_metrics,
                "client_segmentation": client_segmentation,
                "forecasting_data": forecasting_data,
            }
            
            # Add charts if we have valid data
            if not loan_metrics.get("is_error", False) and "Total Loan Amount" in loan_metrics and "Total Interest to be Paid" in loan_metrics:
                try:
                    chart_data = {
                        "Capitale": loan_metrics["Total Loan Amount"],
                        "Interessi": loan_metrics["Total Interest to be Paid"]
                    }
                    portfolio_chart = self.get_chart_image(chart_data, 
                                                "Distribuzione Capitale vs Interessi", "pie")
                    data["portfolio_chart"] = portfolio_chart
                except Exception as e:
                    print(f"Error generating portfolio chart: {e}")
            
            # Add charts if we have valid data AND we should render charts
            if render_charts and not loan_metrics.get("is_error", False) and "Total Loan Amount" in loan_metrics and "Total Interest to be Paid" in loan_metrics:
                try:
                    chart_data = {
                        "Capitale": loan_metrics["Total Loan Amount"],
                        "Interessi": loan_metrics["Total Interest to be Paid"]
                    }
                    portfolio_chart = self.get_chart_image(chart_data, 
                                                "Distribuzione Capitale vs Interessi", "pie")
                    data["portfolio_chart"] = portfolio_chart
                except Exception as e:
                    print(f"Error generating portfolio chart: {e}")
            
            return data

            
        except Exception as e:
            print(f"Error in get_all_data: {str(e)}")
            return {"error": f"Failed to retrieve dashboard data: {str(e)}", "is_error": True}
        

    def _get_thread_connection(self):
        """Get a thread-local database connection to prevent cursor conflicts"""
        # Check if this thread already has a connection
        if not hasattr(self._thread_local, 'conn'):
            # Create a new connection for this thread
            try:
                # Modifica: usando get_connection invece di get_new_connection
                self._thread_local.conn = self.db_manager.get_connection()
            except Exception as e:
                print(f"Error creating thread-local connection: {e}")
                # Fall back to db_manager's connection
                return None
        return self._thread_local.conn

    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve data from cache if valid"""
        cache_item = self._cache.get(key)
        if cache_item and (time.time() - cache_item.timestamp) < cache_item.ttl:
            return cache_item.data
        return None

    def _set_cached_data(self, key: str, data: Any) -> None:
        """Store data in cache with appropriate TTL"""
        ttl = self.cache_ttls.get(key, 300)
        self._cache[key] = CacheItem(data=data, timestamp=time.time(), ttl=ttl)

    def _check_required_packages(self):
        """Check if all required packages for mapping are installed"""
        required_packages = {
            "matplotlib": "Basic plotting",
            "geopandas": "Map rendering",
            "folium": "Interactive maps",
            "shapely": "Geographic operations"
        }
        
        missing = []
        for package, purpose in required_packages.items():
            try:
                __import__(package)
            except ImportError:
                missing.append(f"{package} ({purpose})")
        
        if missing:
            print(f"WARNING: Missing required packages: {', '.join(missing)}")
            
            # Attempt to install missing packages
            try:
                import subprocess
                import sys
                
                print("Attempting to install missing packages...")
                for package in missing:
                    package_name = package.split(" ")[0]  # Extract just the package name
                    print(f"Installing {package_name}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                    print(f"Successfully installed {package_name}")
                    
                print("All required packages installed successfully")
                return True
            except Exception as e:
                print(f"Failed to install packages: {e}")
                return False
        return True

    @lru_cache(maxsize=32)
    def get_loan_metrics(self):
        """Get loan portfolio metrics with caching"""
        cached = self._get_cached_data("loan_metrics")
        if cached:
            return cached
            
        try:
            # Utilizziamo solo il report già esistente
            data = self.loan_report.generate_portfolio_summary()
            
            # Tutte le metriche dovrebbero essere già nel report, ma aggiungiamo valori default
            # in caso questi non fossero presenti
            defaults = {
                "Total Loan Count": 0,
                "French Amortization Count": 0,
                "Italian Amortization Count": 0,
                "Average Loan Amount": 0,
                "Average Loan Term": 0
            }
            
            # Assicuriamoci che tutte le metriche necessarie siano disponibili
            for key, default_value in defaults.items():
                if key not in data:
                    data[key] = default_value
                
            self._set_cached_data("loan_metrics", data)
            return data
        except Exception as e:
            # Return empty data with error flag for graceful degradation
            print(f"Loan metrics error: {str(e)}")
            return {"error": f"Metrics retrieval error: {str(e)}", "is_error": True}
        
    @lru_cache(maxsize=32)
    def get_crm_metrics(self):
        """Get CRM metrics with caching"""
        cached = self._get_cached_data("crm_metrics")
        if cached:
            return cached
            
        try:
            # Utilizzo diretto del loan_report esistente senza creare nuove connessioni
            data = self.loan_report.generate_crm_performance_report()
                
            # Aggiunta delle metriche mancanti calcolate dal database
            try:
                # Ottieni una connessione al database
                thread_conn = self._get_thread_connection()
                if thread_conn:
                    conn = thread_conn
                else:
                    # Uso di get_connection invece di get_new_connection
                    conn = self.db_manager.get_connection()
                
                cursor = conn.cursor()
                
                # Total Clients
                cursor.execute("SELECT COUNT(*) FROM clients")
                data["total_clients"] = cursor.fetchone()[0]
                
                # Client Interactions
                cursor.execute("SELECT COUNT(*) FROM client_interactions")
                data["total_interactions"] = cursor.fetchone()[0]
                
                # Assicurati che altre metriche siano presenti con valori predefiniti
                if "active_clients" not in data:
                    # Consideriamo attivi i clienti che hanno avuto interazioni negli ultimi 90 giorni
                    cursor.execute("""
                        SELECT COUNT(DISTINCT client_id) FROM client_interactions 
                        WHERE interaction_date >= NOW() - INTERVAL '90 days'
                    """)
                    data["active_clients"] = cursor.fetchone()[0]
                    
                if "new_clients_last_30_days" not in data:
                    cursor.execute("""
                        SELECT COUNT(*) FROM clients 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                    data["new_clients_last_30_days"] = cursor.fetchone()[0]
                
                # Close the connection if we created a new one
                if not thread_conn:
                    conn.close()
                    
            except Exception as e:
                print(f"Error calculating additional CRM metrics: {e}")
                # Set default values if calculation fails
                data["total_clients"] = data.get("total_clients", 0)
                data["total_interactions"] = data.get("total_interactions", 0)
                data["active_clients"] = data.get("active_clients", 0)
                data["new_clients_last_30_days"] = data.get("new_clients_last_30_days", 0)
                    
            self._set_cached_data("crm_metrics", data)
            return data
        except Exception as e:
            print(f"CRM metrics error: {str(e)}")
            return {"error": f"CRM metrics error: {str(e)}", "is_error": True}
        
                        
    @lru_cache(maxsize=32)
    def get_client_segmentation(self):
        """Get client segmentation with caching (changes infrequently)"""
        cached = self._get_cached_data("client_segmentation")
        if cached:
            return cached
            
        try:
            # Utilizzo diretto del loan_report esistente senza creare nuove connessioni
            data = self.loan_report.generate_client_segmentation_report()
                    
            self._set_cached_data("client_segmentation", data)
            return data
        except Exception as e:
            print(f"Segmentation error: {str(e)}")
            return {"error": f"Segmentation error: {str(e)}", "is_error": True}
                                
    def _resolve_shapefile_path(self, filename, required=True):
        """
        Resolve shapefile path with robust fallback mechanisms
        
        Args:
            filename: The name of the shapefile
            required: If True, raises FileNotFoundError when file not found
        
        Returns:
            Full path to the shapefile or None if not found and not required
        """
        # Common search locations in priority order
        search_paths = [
            filename,  # Current directory
            os.path.join(os.path.dirname(__file__), filename),  # Module directory
            os.path.join(os.path.dirname(__file__), "data", filename),  # Data subdirectory
            os.path.join(os.path.dirname(__file__), "..", filename),  # Parent directory
            os.path.abspath(filename),  # Absolute path
            os.path.join("c:\\Users\\User\\Desktop\\APP MIA\\Corporations and banks", filename),  # Known project location
        ]
        
        # Try all paths in sequence
        for path in search_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        # If we get here, file wasn't found
        if required:
            raise FileNotFoundError(f"Required shapefile not found: {filename}")
        return None

    def _load_province_shapefile(self, data):
        """Carica lo shapefile delle province e prepara i dati"""
        import geopandas as gpd
        
        # Use our improved path resolver
        shapefile_path = self._resolve_shapefile_path("georef-italy-provincia-millesime.shp")
        
        try:
            # Load the shapefile
            gdf = gpd.read_file(shapefile_path)
            
            # Normalize province names
            normalized_data = {province.lower().strip(): count for province, count in data.items()}
            
            # Determine the province name column
            geometry_name_column = 'prov_name'
            if geometry_name_column not in gdf.columns:
                # Try alternative column names 
                for col in ['provincia', 'name', 'nome', 'prov_acr']:
                    if col in gdf.columns:
                        geometry_name_column = col
                        break
            
            # Add client count column
            gdf['client_count'] = 0
            
            # Match provinces using lookup
            if geometry_name_column in gdf.columns:
                province_lookup = {str(name).lower().strip(): idx for idx, name in 
                                gdf[geometry_name_column].items()}
                
                # Direct matching first
                for db_province, count in normalized_data.items():
                    if db_province in province_lookup:
                        idx = province_lookup[db_province]
                        gdf.at[idx, 'client_count'] = count
                
                # Try partial matching for unmatched provinces
                for db_province, count in normalized_data.items():
                    if db_province not in province_lookup:
                        for province_name, idx in province_lookup.items():
                            if (db_province in province_name or province_name in db_province):
                                gdf.at[idx, 'client_count'] = count
                                break
            
            return gdf, geometry_name_column, normalized_data
            
        except Exception as e:
            import traceback
            print(f"Error loading province shapefile: {e}")
            print(traceback.format_exc())
            
            # Create a simplified fallback map
            return self._create_fallback_geodataframe(data, 'province')


    def _load_commune_shapefile(self, data, kwargs=None):
            """Carica lo shapefile dei comuni e prepara i dati"""
            import geopandas as gpd
            
            # Ensure kwargs is a dictionary
            if kwargs is None:
                kwargs = {}
            
            # Use our improved path resolver
            shapefile_path = self._resolve_shapefile_path("Com01012025_g_WGS84.shp")
            
            try:
                # Load the shapefile
                gdf = gpd.read_file(shapefile_path)
                
                # Se data non proviene dalla tabella clients/corporations, estraiamo i dati dalla colonna city di entrambe
                if not data or kwargs.get('force_db_query', False):
                    # Esegui query per ottenere il conteggio dei clienti per città
                    clients_query = """
                        SELECT city, COUNT(*) as count
                        FROM clients
                        WHERE city IS NOT NULL AND city != ''
                        GROUP BY city
                    """
                    
                    # Esegui query per ottenere il conteggio delle corporations per città
                    corporations_query = """
                        SELECT city, COUNT(*) as count
                        FROM corporations
                        WHERE city IS NOT NULL AND city != ''
                        GROUP BY city
                    """
                    
                    # Esegui entrambe le query
                    cursor_clients = self.db_manager.execute_db_query(clients_query)
                    rows_clients = cursor_clients.fetchall()
                    
                    cursor_corps = self.db_manager.execute_db_query(corporations_query)
                    rows_corps = cursor_corps.fetchall()
                    
                    # Combina i risultati in un unico dizionario
                    data = {}
                    
                    # Aggiungi dati clients
                    for city, count in rows_clients:
                        if city:
                            data[city] = count
                    
                    # Aggiungi o aggiorna i dati corporations
                    for city, count in rows_corps:
                        if city:
                            if city in data:
                                data[city] += count  # Aggiungi al conteggio esistente
                            else:
                                data[city] = count
                    
                    print(f"Dati città caricati dal database: {len(data)} comuni (clients + corporations)")
                
                # Normalize commune names
                normalized_data = {city.lower().strip(): count for city, count in data.items()}
                
                # Find the commune name column
                commune_column_candidates = ['COMUNE', 'comune', 'COMUNE_NOM', 'NOME_COM', 'denominazi', 'name']
                geometry_name_column = None
                for col in commune_column_candidates:
                    if col in gdf.columns:
                        geometry_name_column = col
                        break
                
                if not geometry_name_column:
                    geometry_name_column = gdf.columns[0]  # Fallback to first column
                
                # Add client count column
                gdf['client_count'] = 0
                
                # Match communes using lookup
                if geometry_name_column in gdf.columns:
                    commune_lookup = {str(name).lower().strip(): idx for idx, name in 
                                    gdf[geometry_name_column].items()}
                    
                    # Direct matching first
                    for db_city, count in normalized_data.items():
                        if db_city in commune_lookup:
                            idx = commune_lookup[db_city]
                            gdf.at[idx, 'client_count'] = count
                    
                    # Try partial matching for unmatched communes
                    for db_city, count in normalized_data.items():
                        if db_city not in commune_lookup:
                            for commune_name, idx in commune_lookup.items():
                                if db_city in commune_name or commune_name in db_city:
                                    gdf.at[idx, 'client_count'] = count
                                    break
                
                return gdf, geometry_name_column, normalized_data
                
            except Exception as e:
                import traceback
                print(f"Error loading commune shapefile: {e}")
                print(traceback.format_exc())
                
                # Create a simplified fallback map
                return self._create_fallback_geodataframe(data, 'commune')
            
        
    def _create_fallback_geodataframe(self, data, level='province'):
        """Create a simplified GeoDataFrame as a fallback when shapefile loading fails"""
        import geopandas as gpd
        from shapely.geometry import Polygon
        
        print(f"Creating fallback {level} map")
        
        if level == 'province':
            # Define simplified polygon data for major Italian provinces
            regions = {
                'Roma': Polygon([(12.4, 41.9), (12.6, 41.9), (12.6, 41.8), (12.4, 41.8)]),
                'Milano': Polygon([(9.1, 45.5), (9.3, 45.5), (9.3, 45.4), (9.1, 45.4)]),
                'Napoli': Polygon([(14.2, 40.9), (14.4, 40.9), (14.4, 40.8), (14.2, 40.8)]),
                'Torino': Polygon([(7.6, 45.1), (7.8, 45.1), (7.8, 45.0), (7.6, 45.0)]),
                'Palermo': Polygon([(13.3, 38.2), (13.5, 38.2), (13.5, 38.1), (13.3, 38.1)])
            }
            geometry_name_column = 'prov_name'
        else:
            # For communes, create some example municipalities
            regions = {
                'Roma': Polygon([(12.4, 41.9), (12.5, 41.9), (12.5, 41.8), (12.4, 41.8)]),
                'Milano': Polygon([(9.1, 45.5), (9.2, 45.5), (9.2, 45.4), (9.1, 45.4)]),
                'Napoli': Polygon([(14.2, 40.9), (14.3, 40.9), (14.3, 40.8), (14.2, 40.8)]),
                'Firenze': Polygon([(11.2, 43.8), (11.3, 43.8), (11.3, 43.7), (11.2, 43.7)]),
                'Bologna': Polygon([(11.3, 44.5), (11.4, 44.5), (11.4, 44.4), (11.3, 44.4)])
            }
            geometry_name_column = 'COMUNE'
        
        # Add any data points we have
        for name in list(data.keys()):
            if name.lower() not in [r.lower() for r in regions.keys()]:
                # Create a placeholder polygon for this data point
                # Position it based on hash of name for consistency
                import hashlib
                h = int(hashlib.md5(name.encode()).hexdigest(), 16)
                x_base, y_base = 12.5, 42.0  # Central Italy
                x_offset = ((h % 1000) / 1000 - 0.5) * 6  # +/- 3 degrees
                y_offset = ((h // 1000 % 1000) / 1000 - 0.5) * 4  # +/- 2 degrees
                
                regions[name] = Polygon([
                    (x_base + x_offset, y_base + y_offset),
                    (x_base + x_offset + 0.1, y_base + y_offset),
                    (x_base + x_offset + 0.1, y_base + y_offset + 0.1),
                    (x_base + x_offset, y_base + y_offset + 0.1)
                ])
        
        # Create GeoDataFrame
        geometry = [regions[name] for name in regions.keys()]
        gdf = gpd.GeoDataFrame({
            geometry_name_column: list(regions.keys()),
            'geometry': geometry
        })
        
        # Add client count
        gdf['client_count'] = 0
        for idx, name in enumerate(gdf[geometry_name_column]):
            for data_name, count in data.items():
                if data_name.lower() == name.lower():
                    gdf.at[idx, 'client_count'] = count
                    break
        
        # Set CRS
        gdf.crs = "EPSG:4326"  # WGS84
        
        normalized_data = {name.lower(): count for name, count in data.items()}
        
        return gdf, geometry_name_column, normalized_data


    def _create_interactive_map(self, data, title, kwargs):
        """Crea una mappa interattiva folium in modo thread-safe e ottimizzato"""
        try:
            # Check if we have the required libraries
            import geopandas as gpd
            import folium
            from folium.plugins import Fullscreen, MousePosition, Draw, MeasureControl
            import tempfile
            import uuid
            import os
            
            # Get map detail level
            map_detail = kwargs.get('map_detail', 'province').lower()
            
            # Load shapefile based on detail level
            if map_detail == 'province':
                gdf, geometry_name_column, normalized_data = self._load_province_shapefile(data)
            else:
                gdf, geometry_name_column, normalized_data = self._load_commune_shapefile(data)
            
            # Get map center (Italy centered or calculated from data)
            bounds = gdf.geometry.total_bounds
            center_x = (bounds[0] + bounds[2]) / 2
            center_y = (bounds[1] + bounds[3]) / 2
            center = [center_y, center_x]  # Latitude, longitude
            
            # Fallback to Italy center if calculation fails
            if not all([isinstance(x, (int, float)) and -180 <= x <= 180 for x in center]):
                center = [41.9028, 12.4964]  # Rome coordinates
            
            # Configure tooltip and popup
            tooltip_cols = ['client_count']
            popup_cols = [geometry_name_column, 'client_count']
            
            # Create the map with improved options
            m = folium.Map(
                location=center,
                zoom_start=6,
                tiles='CartoDB positron',
                control_scale=True
            )
            
            # Add choropleth layer
            choropleth = folium.Choropleth(
                geo_data=gdf,
                name='choropleth',
                data=data,
                columns=[geometry_name_column, 'client_count'],
                key_on=f'feature.properties.{geometry_name_column}',
                fill_color='YlGnBu',
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name='Numero Clienti',
                highlight=True
            ).add_to(m)
            
            # Add tooltips to the choropleth layer
            folium.GeoJsonTooltip(
                fields=[geometry_name_column, 'client_count'],
                aliases=[f'{"Provincia" if map_detail == "province" else "Comune"}:', 'Clienti:'],
                style=('background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;')
            ).add_to(choropleth.geojson)
            
            # Add additional controls
            Fullscreen(
                position='topleft',
                title='Visualizza a schermo intero',
                title_cancel='Esci da schermo intero',
                force_separate_button=True
            ).add_to(m)
            
            folium.LayerControl().add_to(m)
            MousePosition().add_to(m)
            
            # Add drawing tools
            Draw(
                position='topleft',
                draw_options={
                    'polyline': False,
                    'rectangle': True,
                    'polygon': True,
                    'circle': True,
                    'marker': True,
                    'circlemarker': False
                },
                edit_options={'edit': True}
            ).add_to(m)
            
            # Add measurement control
            MeasureControl(
                position='bottomleft',
                primary_length_unit='kilometers',
                secondary_length_unit='miles',
                primary_area_unit='square kilometers'
            ).add_to(m)
            
            # Ensure controls like zoom are visible and working
            options = {
                'zoomControl': True,
                'scrollWheelZoom': True,
                'dragging': True,
                'zoomSnap': 0.25,
                'wheelPxPerZoomLevel': 100,
                'preferCanvas': True  # Use canvas for better performance
            }
            
            for k, v in options.items():
                m.options[k] = v
            
            # Add title and improved CSS
            title_html = f'''
                <h3 align="center" style="font-size:16px; margin-top:10px;"><b>{title}</b></h3>
            '''
            m.get_root().html.add_child(folium.Element(title_html))
            
            css = '''
            <style>
                .leaflet-control-zoom {
                    visibility: visible !important;
                    opacity: 1 !important; 
                    display: block !important;
                    z-index: 1000 !important;
                }
                .leaflet-bar {
                    border: 2px solid rgba(0,0,0,0.2) !important;
                    background-clip: padding-box !important;
                }
                .leaflet-control-zoom-in, .leaflet-control-zoom-out {
                    font-size: 18px !important;
                    height: 30px !important;
                    width: 30px !important;
                    line-height: 30px !important;
                    color: #333 !important;
                    font-weight: bold !important;
                    background-color: white !important;
                    text-align: center;
                }
                .leaflet-control-zoom-in:hover, .leaflet-control-zoom-out:hover {
                    background-color: #f4f4f4 !important;
                    color: #000 !important;
                }
                .leaflet-control-layers {
                    background-color: white !important;
                    padding: 5px !important;
                }
                .leaflet-touch .leaflet-control-layers, .leaflet-touch .leaflet-bar {
                    border: 2px solid rgba(0,0,0,0.2) !important;
                }
                .leaflet-container {
                    height: 100%;
                    width: 100%;
                    max-width: 100%;
                    max-height: 100%;
                }
                /* Fix for Qt WebEngine rendering */
                #map {
                    height: 100% !important;
                    width: 100% !important;
                }
            </style>
            '''
            m.get_root().html.add_child(folium.Element(css))
            
            # Add JavaScript for improving interaction with Qt WebEngine
            js = '''
            <script>
                // Fix for potential zoom control issues in Qt WebEngine
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(function() {
                        try {
                            // Force map to invalidate size
                            map.invalidateSize();
                        } catch(e) {
                            console.log("Map resize error:", e);
                        }
                    }, 500);
                });
            </script>
            '''
            m.get_root().html.add_child(folium.Element(js))
            
            # Create a unique temp file with better path handling
            unique_id = str(uuid.uuid4())[:8]
            temp_dir = tempfile.gettempdir()
            temp_filename = os.path.join(temp_dir, f"map_{unique_id}.html")
            
            # Save the map with all data embedded
            m.save(temp_filename)
            
            # Read HTML content
            with open(temp_filename, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Register file for later cleanup
            self._register_temp_file(temp_filename)
            
            return html_content
            
        except Exception as e:
            import traceback
            print(f"Error creating interactive map: {e}")
            print(traceback.format_exc())
            # Return None to fall back to static map
            return None
        

    def get_professional_pie_chart(self, data: dict, title: str):
        """
        Genera un grafico a torta professionale.

        Args:
            data: Dizionario dei dati, ad esempio {"Capitale": 100000, "Interessi": 25000}
            title: Titolo del grafico

        Returns:
            Figura matplotlib formattata professionalmente.
        """
        # Crea la figura e l'asse
        fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
        
        # Imposta una palette di colori moderna usando un colormap
        cmap = cm.get_cmap('Set3')
        colors = [cmap(i) for i in range(len(data))]
        
        # Preparazione dei dati
        labels = list(data.keys())
        sizes = list(data.values())
        
        # Calcola l'explode per evidenziare la fetta più grande
        max_value = max(sizes)
        explode = [0.1 if s == max_value else 0 for s in sizes]
        
        # Crea il grafico a torta
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            explode=explode,
            colors=colors,
            autopct='%1.1f%%',
            startangle=140,
            textprops={'fontsize': 10, 'color': 'black'}
        )
        
        # Imposta il titolo con formattazione curata
        ax.set_title(title, fontsize=14, fontweight='bold', color='#333333', pad=20)
        ax.axis('equal')  # Garantisci che la torta sia perfettamente rotonda
        
        # Personalizza il formato dei testi interni
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
        
        fig.tight_layout()
        return fig

                
    def get_chart_image(self, data, title, chart_type, **kwargs):
        """
        Generate chart or map image with improved error handling and consistent styling
        
        Args:
            data: Dictionary of data for the chart
            title: Chart title
            chart_type: Type of chart (pie, bar, line, map)
            **kwargs: Additional parameters
        
        Returns:
            Base64 encoded image or HTML content for interactive maps
        """
        try:
            # Check for empty data
            if not data:
                return None
                
            # Import necessary libraries in function scope
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import base64
            import io
            
            # Improved styling setup
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # Consistent color palette for app-wide use
            app_colors = {
                'primary': '#2188ff',         # Primary blue
                'secondary': '#6f42c1',       # Purple
                'accent': '#ea4aaa',          # Pink
                'success': '#28a745',         # Green
                'warning': '#ffd33d',         # Yellow
                'danger': '#d73a49',          # Red
                'neutral': '#24292e',         # Dark gray
                'light': '#f6f8fa',           # Light gray
                'white': '#ffffff',           # White
            }
            
            # Generate color palette for multi-colored charts
            color_palette = [
                app_colors['primary'], 
                app_colors['secondary'], 
                app_colors['accent'],
                app_colors['success'], 
                app_colors['warning'], 
                app_colors['danger']
            ]
            
            # Custom styling for all charts
            matplotlib.rcParams.update({
                'font.family': 'sans-serif',
                'font.sans-serif': ['Segoe UI', 'Arial', 'Helvetica', 'DejaVu Sans'],
                'axes.labelcolor': app_colors['neutral'],
                'axes.edgecolor': '#dbe1e8',
                'axes.grid': True,
                'grid.color': '#eaeef2',
                'grid.linestyle': '--',
                'grid.alpha': 0.7,
                'xtick.color': app_colors['neutral'],
                'ytick.color': app_colors['neutral'],
                'figure.facecolor': app_colors['white'],
                'figure.titlesize': 14,
                'figure.titleweight': 'bold',
            })
            
            interactive = kwargs.get('interactive', False)
            
            # Handle interactive maps
            if chart_type == "map" and interactive:
                # Try to import required packages for interactive maps
                try:
                    import folium
                    import geopandas
                    
                    # Create interactive map with improved styling
                    html_content = self._create_interactive_map(data, title, kwargs)
                    if html_content:
                        return "html:" + html_content
                    
                    # If interactive map creation failed, fall back to static
                    print("Falling back to static map due to interactive map creation failure")
                    interactive = False
                except ImportError as e:
                    print(f"Required package for interactive maps not available: {e}")
                    interactive = False
                    
            # Static chart/map generation with consistent styling
            fig = plt.figure(figsize=(5, 5), dpi=100)
            
            # Handle static maps
            if chart_type == "map":
                try:
                    # Try to import geopandas for static maps
                    import geopandas as gpd
                    import os
                    from matplotlib.colors import LinearSegmentedColormap
                    
                    # Set environment variable for shapefile handling
                    os.environ['SHAPE_RESTORE_SHX'] = 'YES'
                    
                    # Get map detail level
                    map_detail = kwargs.get('map_detail', 'province').lower()
                    
                    # Create color map that matches app style
                    colors = [
                        '#e3f2fd',  # Very light blue
                        '#bbdefb',  # Light blue
                        '#90caf9',  # Medium light blue
                        '#64b5f6',  # Medium blue
                        '#42a5f5',  # Standard blue
                        '#2196f3',  # Vivid blue
                        '#1e88e5',  # Darker blue
                        '#1976d2'   # Deep blue
                    ]
                    cmap = LinearSegmentedColormap.from_list('app_blue_gradient', colors)
                    
                    # Load appropriate shapefile based on detail level
                    if map_detail == 'province':
                        gdf, geometry_name_column, _ = self._load_province_shapefile(data)
                    else:
                        gdf, geometry_name_column, _ = self._load_commune_shapefile(data)
                    
                    # Create the plot with improved styling
                    ax = fig.add_subplot(111)
                    gdf.plot(
                        column='client_count', 
                        cmap=cmap, 
                        linewidth=0.5, 
                        edgecolor=app_colors['light'], 
                        ax=ax, 
                        legend=True,
                        legend_kwds={
                            'label': "Numero Clienti", 
                            'orientation': "horizontal", 
                            'shrink': 0.8,
                            'pad': 0.05,
                            'fraction': 0.046
                        }
                    )
                    
                    # Improved title
                    plt.title(title, fontsize=16, fontweight='bold', pad=20, color=app_colors['neutral'])
                    plt.axis('off')
                    plt.tight_layout(pad=2.0)
                    
                except Exception as e:
                    import traceback
                    print(f"Error generating static map: {e}")
                    print(traceback.format_exc())
                    
                    # Fallback to bar chart if map generation fails
                    plt.clf()  # Clear the figure
                    plt.bar(data.keys(), data.values(), color=app_colors['primary'])
                    plt.title(f"{title} (Map rendering failed)", fontsize=16, fontweight='bold', color=app_colors['neutral'])
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout(pad=2.0)
            
            elif chart_type == "pie":
                # Create pie chart with improved styling
                fig = self.get_professional_pie_chart(data, title)
                # Convert the figure to a base64-encoded string
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
                buf.seek(0)
                img_data = base64.b64encode(buf.read()).decode('utf-8')
                plt.close(fig)
                
                # Store in cache (optionally for future use)
                self._chart_cache[title] = fig
                return img_data
            
            # Handle bar charts with improved styling
            elif chart_type == "bar":
                # Create styled bar chart
                bars = plt.bar(
                    list(data.keys()), 
                    list(data.values()),
                    color=app_colors['primary'],
                    edgecolor=app_colors['neutral'],
                    linewidth=0.5,
                    alpha=0.8
                )
                
                # Add value labels on top of bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(
                        bar.get_x() + bar.get_width()/2.,
                        height + 0.01 * max(data.values()),
                        f'{int(height):,}',
                        ha='center', 
                        va='bottom',
                        fontsize=10,
                        fontweight='bold',
                        color=app_colors['neutral']
                    )
                
                # Style the chart
                plt.title(title, fontsize=16, fontweight='bold', pad=20, color=app_colors['neutral'])
                plt.grid(True, linestyle='--', alpha=0.7, axis='y')
                plt.xticks(rotation=45, ha='right', fontweight='normal', color=app_colors['neutral'])
                plt.yticks(fontweight='normal', color=app_colors['neutral'])
                plt.tight_layout(pad=2.0)
                
            # Handle line charts with improved styling
            elif chart_type == "line":
                # Add gradient fill under the line
                import numpy as np
                from matplotlib import cm
                
                x_values = list(data.keys())
                y_values = list(data.values())
                
                # Create line with styled markers
                line = plt.plot(
                    x_values, 
                    y_values,
                    marker='o',
                    markersize=8,
                    markerfacecolor=app_colors['primary'],
                    markeredgecolor='white',
                    markeredgewidth=2,
                    linestyle='-',
                    linewidth=3,
                    color=app_colors['primary'],
                    alpha=0.8
                )[0]
                
                # Add light gradient area beneath the line
                plt.fill_between(
                    x_values, 
                    y_values, 
                    alpha=0.2, 
                    color=app_colors['primary'],
                    interpolate=True
                )
                
                # Add value labels above points
                for i, (x, y) in enumerate(zip(x_values, y_values)):
                    plt.annotate(
                        f'{int(y):,}',
                        (x, y),
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center',
                        va='bottom',
                        fontsize=9,
                        fontweight='bold',
                        color=app_colors['neutral']
                    )
                
                # Style the chart
                plt.title(title, fontsize=16, fontweight='bold', pad=20, color=app_colors['neutral'])
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45, ha='right', fontweight='normal', color=app_colors['neutral'])
                plt.yticks(fontweight='normal', color=app_colors['neutral'])
                plt.tight_layout(pad=2.0)
            
            # Save figure to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
            buf.seek(0)
            
            # Encode to base64
            img_data = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            return img_data
            
        except Exception as e:
            import traceback
            print(f"Error generating chart image: {e}")
            print(traceback.format_exc())
            return None


    def _download_italy_shapefile(self):
        """Setup Italy provinces shapefile from local file."""
        import os
        import shutil
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Path to local shapefile
        local_shapefile = os.path.join(os.path.dirname(__file__), "georef-italy-provincia-millesime.shp")
        
        # If local shapefile doesn't exist at expected path, search for it
        if not os.path.exists(local_shapefile):
            # Try common locations
            search_paths = [
                "c:\\Users\\User\\Desktop\\APP MIA\\Corporations and banks\\georef-italy-provincia-millesime.shp",
                os.path.join(os.path.dirname(__file__), "..", "georef-italy-provincia-millesime.shp"),
                "georef-italy-provincia-millesime.shp"
            ]
            
            for path in search_paths:
                if os.path.exists(path):
                    local_shapefile = path
                    break
        
        # Destination path
        dest_shapefile = os.path.join(data_dir, "italy_provinces.shp")
        
        if os.path.exists(local_shapefile):
            print(f"Using local shapefile: {local_shapefile}")
            
            # Copy the shapefile and related files (.dbf, .shx, .prj)
            base_local = local_shapefile[:-4]  # Remove .shp extension
            base_dest = dest_shapefile[:-4]    # Remove .shp extension
            
            for ext in ['.shp', '.dbf', '.shx', '.prj']:
                src = f"{base_local}{ext}"
                dst = f"{base_dest}{ext}"
                if os.path.exists(src):
                    shutil.copy2(src, dst)
            
            print("Shapefile setup completed successfully")
        else:
            print("Local shapefile not found, creating a simplified version")
            self._create_simple_italy_shapefile(data_dir)

    def _create_simple_italy_shapefile(self, data_dir):
        """Create a simplified shapefile for Italy provinces as fallback"""
        try:
            import geopandas as gpd
            from shapely.geometry import Polygon
            
            # Define simplified polygon data for major Italian provinces
            provinces = {
                'Roma': Polygon([(12.4, 41.9), (12.6, 41.9), (12.6, 41.8), (12.4, 41.8)]),
                'Milano': Polygon([(9.1, 45.5), (9.3, 45.5), (9.3, 45.4), (9.1, 45.4)]),
                'Napoli': Polygon([(14.2, 40.9), (14.4, 40.9), (14.4, 40.8), (14.2, 40.8)]),
                'Torino': Polygon([(7.6, 45.1), (7.8, 45.1), (7.8, 45.0), (7.6, 45.0)]),
                'Palermo': Polygon([(13.3, 38.2), (13.5, 38.2), (13.5, 38.1), (13.3, 38.1)])
            }
            
            # Create GeoDataFrame
            geometry = [provinces[name] for name in provinces]
            gdf = gpd.GeoDataFrame({
                'provincia': list(provinces.keys()),
                'state': list(provinces.keys()),  # Matching database field name
                'geometry': geometry
            })
            
            # Set CRS
            gdf.crs = "EPSG:4326"  # WGS84
            
            # Save to shapefile
            gdf.to_file(os.path.join(data_dir, "italy_provinces.shp"))
            print("Created simplified Italy shapefile as fallback")
            
        except Exception as e:
            print(f"Error creating simplified shapefile: {e}")
            raise
                
    @lru_cache(maxsize=32)
    def get_forecasting_data(self):
        """Get forecasting data with caching"""
        cached = self._get_cached_data("forecasting_data")
        if cached:
            return cached
            
        try:
            # Utilizzo diretto del loan_report esistente senza creare nuove connessioni
            forecast_df = self.loan_report.generate_forecasting_report(
                frequency='monthly', start='1994-01-01')
                
            forecast_data = forecast_df.to_dict(orient='list')
            self._set_cached_data("forecasting_data", forecast_data)
            return forecast_data
        except Exception as e:
            print(f"Forecasting error: {str(e)}")
            return {"error": f"Forecasting error: {str(e)}", "is_error": True}
        

    def clear_cache(self, component=None):
        """Clear specific component cache or all cache"""
        if component:
            if component in self._cache:
                del self._cache[component]
        else:
            self._cache.clear()
        # Also clear the lru_cache
        self.get_loan_metrics.cache_clear()
        self.get_crm_metrics.cache_clear()
        self.get_client_segmentation.cache_clear()
        self.get_forecasting_data.cache_clear()

    def _register_temp_file(self, filepath):
        """Register a temporary file for later cleanup"""
        if not hasattr(self, '_temp_files'):
            self._temp_files = []
        self._temp_files.append(filepath)
            
    def cleanup_temp_files(self):
        """
        Clean up temporary map files more thoroughly
        """
        import os
        import glob
        import tempfile
        import time
        
        # Track files we've successfully cleaned up
        cleaned_files = []
        
        # 1. Clean up registered temp files
        for file_path in self._temp_files[:]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Removed temporary file: {file_path}")
                    self._temp_files.remove(file_path)
                    cleaned_files.append(file_path)
            except Exception as e:
                print(f"Error removing temporary file {file_path}: {e}")
        
        # 2. Find and clean up any map files in temp directory that are older than 30 minutes
        try:
            temp_dir = tempfile.gettempdir()
            current_time = time.time()
            
            # Find map files with our prefix
            for temp_file in glob.glob(os.path.join(temp_dir, "map_*.html")):
                try:
                    # Check if file is older than 30 minutes
                    if os.path.getmtime(temp_file) < current_time - 1800:  # 30 minutes in seconds
                        os.remove(temp_file)
                        print(f"Removed old temporary map file: {temp_file}")
                        cleaned_files.append(temp_file)
                except Exception as e:
                    print(f"Error cleaning up old map file {temp_file}: {e}")
        except Exception as e:
            print(f"Error during additional temp file cleanup: {e}")
            
        return cleaned_files

    def __del__(self):
        """Clean up thread-local connections and temporary files on object destruction"""
        try:
            if hasattr(self._thread_local, 'conn'):
                if self._thread_local.conn:
                    self._thread_local.conn.close()
        except:
            pass
            
        # Add cleanup for temp files
        try:
            self.cleanup_temp_files()
        except:
            pass
        
class DashboardBackend:
    """
    Ottimizzato per prestazioni elevate nel fornire dati alla dashboard
    """
    def __init__(self, db_manager: DbManager):
        self.dashboard_data = DashboardData(db_manager)
        self.last_update_time = 0
        self.cache = {"priority": {}, "full": {}}
        self.update_interval = 5  # secondi
        self._update_lock = threading.Lock()
        self.update_thread = None
        self.running = False
        self.callbacks = []
        self.update_queue = []
    
    def register_update_callback(self, callback_function):
        """Register a callback function that will be called when dashboard data updates"""
        if callback_function not in self.callbacks:
            self.callbacks.append(callback_function)
    
    def unregister_update_callback(self, callback_function):
        """Remove a previously registered callback function"""
        if callback_function in self.callbacks:
            self.callbacks.remove(callback_function)
    
    def refresh_dashboard(self, force=False, priority_only=False):
        """Aggiorna i dati della dashboard in modo efficiente"""
        current_time = time.time()
        cache_key = "priority" if priority_only else "full"
        
        with self._update_lock:
            if force or (current_time - self.last_update_time) >= self.update_interval:
                try:
                    # Get data
                    data = self.dashboard_data.get_all_data(priority_only=priority_only)
                    self.cache[cache_key] = data
                    self.last_update_time = current_time
                    
                    # Convert to JSON for transfer
                    import json
                    json_data = json.dumps(data, default=str)
                    
                    # Notify all registered callbacks
                    for callback in self.callbacks:
                        try:
                            callback(json_data)
                        except Exception as e:
                            print(f"Error in dashboard callback: {e}")
                    
                    return json_data
                    
                except Exception as e:
                    error_data = {"error": f"Failed to refresh dashboard: {str(e)}"}
                    error_json = json.dumps(error_data)
                    
                    # Still notify callbacks about the error
                    for callback in self.callbacks:
                        try:
                            callback(error_json)
                        except Exception as callback_error:
                            print(f"Error in dashboard error callback: {callback_error}")
                    
                    return error_json
            else:
                # Return cached data
                import json
                return json.dumps(self.cache[cache_key], default=str)
        
# Nella classe DashboardBackend

    def start_auto_refresh(self, interval=None):
        """Start auto-refresh of dashboard data with specified interval in seconds"""
        from PyQt5.QtCore import QTimer
        
        # Assicura che il timer sia creato nel thread dell'UI
        if not hasattr(self, 'refresh_timer'):
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self.refresh_dashboard)
        
        # Imposta l'intervallo (default 60 secondi se non specificato)
        interval_ms = (interval or 60) * 1000
        
        # Ferma il timer se è già in esecuzione
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
        
        # Avvia il timer con il nuovo intervallo
        self.refresh_timer.start(interval_ms)
                    
    def stop_auto_refresh(self):
        """Stop automatic refresh"""
        self.running = False
        if self.update_thread:
            # The thread will terminate naturally after the next sleep cycle
            self.update_thread = None
    
    def clear_cache(self, component=None):
        """Clear specific component cache or all cache"""
        if component:
            if component in self.cache:
                self.cache[component] = {}
        else:
            self.cache = {"priority": {}, "full": {}}
        
        # Also clear cache in the dashboard data object
        self.dashboard_data.clear_cache()
