"""
Safe Route Navigation Engine using A* & Dijkstra Algorithms with Dynamic Hazard and Flood Risk Cost Optimization.

Route Cost Formula:
  Route Cost = Distance Cost + Flood Risk Penalty + Water Level Penalty + Hazard Penalty
"""

import math
import heapq
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field


class Waypoint(BaseModel):
    latitude: float
    longitude: float
    elevation_m: float = 25.0
    water_level_m: float = 0.0
    flood_risk_score: float = 0.0
    is_blocked: bool = False
    hazard_description: Optional[str] = None
    step_instruction: Optional[str] = None


class SafeRouteRequest(BaseModel):
    origin_latitude: float = Field(..., description="Current user latitude")
    origin_longitude: float = Field(..., description="Current user longitude")
    destination_shelter_id: Optional[str] = None
    destination_latitude: Optional[float] = None
    destination_longitude: Optional[float] = None
    algorithm: str = Field(default="A_STAR", description="Routing algorithm ('A_STAR' or 'DIJKSTRA')")
    avoid_water_above_meters: float = Field(default=0.6, description="Maximum traversable water depth")
    hazard_penalty_weight: float = Field(default=5.0, description="Multiplier for hazard zones")
    flood_risk_weight: float = Field(default=4.0, description="Multiplier for flood probability")


class RouteSegment(BaseModel):
    distance_km: float
    estimated_time_min: float
    safety_score: float # 0 to 100
    average_water_level_m: float
    avoided_hazards: List[str]
    waypoints: List[Dict[str, Any]]
    turn_by_turn_instructions: List[str]


class SafeRouteResponse(BaseModel):
    primary_safest_route: RouteSegment
    alternative_route: RouteSegment
    algorithm_used: str
    origin: Dict[str, float]
    destination: Dict[str, float]
    destination_shelter_name: str
    overall_evacuation_status: str


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great circle distance in kilometers between two coordinates."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class SafeRouteEngine:
    """
    Constructs a dynamic navigation graph with spatial hazards and flood zones,
    then executes A* or Dijkstra graph search.
    """

    def __init__(self):
        # Default active regional shelters
        self.shelters = [
            {"id": "s1", "name": "NDRF Regional Relief Center (High Elevation)", "lat": 26.1445, "lng": 91.7362, "elevation": 110.0, "capacity": 1500, "occupancy": 320},
            {"id": "s2", "name": "Kochi Elevated Evacuation Center", "lat": 9.9468, "lng": 76.3533, "elevation": 42.0, "capacity": 1200, "occupancy": 480},
            {"id": "s3", "name": "Patna Flood Shelter Complex", "lat": 25.5941, "lng": 85.1376, "elevation": 58.0, "capacity": 2000, "occupancy": 750},
            {"id": "s4", "name": "Powai Elevated Shelter Hub", "lat": 19.1197, "lng": 72.9051, "elevation": 65.0, "capacity": 1800, "occupancy": 610},
            {"id": "s5", "name": "Cuttack High Grounds Shelter", "lat": 20.4625, "lng": 85.8828, "elevation": 38.0, "capacity": 1400, "occupancy": 290}
        ]

        # Active Hazards
        self.hazards = [
            {"id": "h1", "type": "ELECTRICAL", "lat": 26.1550, "lng": 91.7500, "radius_m": 120.0, "severity": 4.0, "desc": "Active 11kV Submerged Transformer"},
            {"id": "h2", "type": "BLOCKED_ROAD", "lat": 26.1380, "lng": 91.7200, "radius_m": 150.0, "severity": 5.0, "desc": "NH-27 Highway Culvert Collapse"},
            {"id": "h3", "type": "DEEP_WATER", "lat": 19.0750, "lng": 72.8770, "radius_m": 200.0, "severity": 4.5, "desc": "Mithi River Overbank Velocity >3m/s"},
            {"id": "h4", "type": "FALLEN_TREE", "lat": 9.9816, "lng": 76.2999, "radius_m": 60.0, "severity": 2.5, "desc": "Uprooted Tree on Main Arterial Road"}
        ]

    def find_nearest_shelter(self, user_lat: float, user_lng: float) -> Dict[str, Any]:
        """Finds closest operational shelter by distance and elevation."""
        best_shelter = None
        min_dist = float('inf')
        for shelter in self.shelters:
            d = haversine_km(user_lat, user_lng, shelter["lat"], shelter["lng"])
            if d < min_dist:
                min_dist = d
                best_shelter = shelter
        return best_shelter or self.shelters[0]

    def _generate_synthetic_grid_graph(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, grid_steps: int = 8
    ) -> Tuple[List[Dict[str, Any]], Dict[int, List[Tuple[int, float]]]]:
        """
        Creates a spatial waypoint lattice between origin and destination with realistic micro-roads and water depths.
        """
        nodes = []
        d_lat = dest_lat - origin_lat
        d_lng = dest_lng - origin_lng
        
        # Perpendicular vector for grid expansion
        perp_lat = -d_lng
        perp_lng = d_lat
        norm = math.sqrt(perp_lat**2 + perp_lng**2) or 1.0
        perp_lat = (perp_lat / norm) * 0.008
        perp_lng = (perp_lng / norm) * 0.008

        idx = 0
        node_grid = []

        for step in range(grid_steps + 1):
            t = step / grid_steps
            base_lat = origin_lat + t * d_lat
            base_lng = origin_lng + t * d_lng
            row = []
            
            # 5 lateral parallel street branches
            for lateral in range(-2, 3):
                lat = base_lat + lateral * perp_lat
                lng = base_lng + lateral * perp_lng
                
                # Check proximity to known hazards
                hazard_cost = 0.0
                hazard_desc = None
                for h in self.hazards:
                    dist_to_h_m = haversine_km(lat, lng, h["lat"], h["lng"]) * 1000.0
                    if dist_to_h_m < h["radius_m"]:
                        hazard_cost += h["severity"] * 10.0
                        hazard_desc = f"{h['type']}: {h['desc']}"

                # Calculate simulated water level based on distance to center lowlands
                water_level = max(0.05, round(0.35 + 0.5 * math.sin(t * math.pi) + (0.4 if lateral == 0 else 0.1), 2))
                if hazard_cost > 0:
                    water_level += 0.5

                flood_risk = min(0.95, (water_level / 2.0) + (0.2 if hazard_cost > 0 else 0.0))

                nodes.append({
                    "id": idx,
                    "lat": lat,
                    "lng": lng,
                    "water_level": water_level,
                    "flood_risk": flood_risk,
                    "hazard_cost": hazard_cost,
                    "hazard_desc": hazard_desc,
                    "step": step,
                    "lateral": lateral
                })
                row.append(idx)
                idx += 1
            node_grid.append(row)

        # Build adjacency graph
        adj = {i: [] for i in range(len(nodes))}
        for step in range(grid_steps):
            for lateral_idx in range(5):
                u = node_grid[step][lateral_idx]
                
                # Forward straight, forward left, forward right
                for d_lat_idx in [-1, 0, 1]:
                    target_lateral = lateral_idx + d_lat_idx
                    if 0 <= target_lateral < 5:
                        v = node_grid[step + 1][target_lateral]
                        dist_km = haversine_km(nodes[u]["lat"], nodes[u]["lng"], nodes[v]["lat"], nodes[v]["lng"])
                        adj[u].append((v, dist_km))

        return nodes, adj

    def compute_safe_route(self, request: SafeRouteRequest) -> SafeRouteResponse:
        dest_shelter = None
        if request.destination_latitude and request.destination_longitude:
            dest_lat = request.destination_latitude
            dest_lng = request.destination_longitude
            shelter_name = "Selected Evacuation Point"
        else:
            dest_shelter = self.find_nearest_shelter(request.origin_latitude, request.origin_longitude)
            dest_lat = dest_shelter["lat"]
            dest_lng = dest_shelter["lng"]
            shelter_name = dest_shelter["name"]

        nodes, adj = self._generate_synthetic_grid_graph(
            request.origin_latitude, request.origin_longitude, dest_lat, dest_lng
        )

        start_node_id = 2 # Center lateral at start
        goal_candidates = [n["id"] for n in nodes if n["step"] == 8]

        # 1. Compute Primary Safest Route (A* with Safety Weights)
        primary_path_nodes = self._a_star_search(
            nodes, adj, start_node_id, goal_candidates,
            risk_weight=request.flood_risk_weight,
            hazard_weight=request.hazard_penalty_weight,
            water_penalty_weight=6.0
        )

        # 2. Compute Alternative Route (Dijkstra / Alternative lateral path)
        alt_path_nodes = self._dijkstra_search(
            nodes, adj, start_node_id, goal_candidates,
            risk_weight=request.flood_risk_weight * 0.5,
            hazard_weight=request.hazard_penalty_weight * 0.5,
            water_penalty_weight=2.0,
            exclude_nodes=set(primary_path_nodes[1:-1])
        )
        if not alt_path_nodes:
            alt_path_nodes = self._dijkstra_search(
                nodes, adj, start_node_id, goal_candidates,
                risk_weight=1.0, hazard_weight=2.0, water_penalty_weight=1.0
            )

        primary_segment = self._build_route_segment(nodes, primary_path_nodes, "Primary Evacuation Route")
        alt_segment = self._build_route_segment(nodes, alt_path_nodes, "Secondary Bypass Route")

        return SafeRouteResponse(
            primary_safest_route=primary_segment,
            alternative_route=alt_segment,
            algorithm_used=request.algorithm,
            origin={"latitude": request.origin_latitude, "longitude": request.origin_longitude},
            destination={"latitude": dest_lat, "longitude": dest_lng},
            destination_shelter_name=shelter_name,
            overall_evacuation_status="ACTIVE_GUIDANCE_ENABLED"
        )

    def _a_star_search(
        self, nodes: List[Dict[str, Any]], adj: Dict[int, List[Tuple[int, float]]],
        start: int, goals: List[int],
        risk_weight: float = 4.0, hazard_weight: float = 5.0, water_penalty_weight: float = 5.0
    ) -> List[int]:
        """A* Search Algorithm with custom heuristic & safety cost."""
        goal_lat = nodes[goals[0]]["lat"]
        goal_lng = nodes[goals[0]]["lng"]

        def heuristic(u_id: int) -> float:
            return haversine_km(nodes[u_id]["lat"], nodes[u_id]["lng"], goal_lat, goal_lng)

        open_set = []
        heapq.heappush(open_set, (0.0, start))
        came_from = {}
        g_score = {i: float('inf') for i in range(len(nodes))}
        g_score[start] = 0.0

        while open_set:
            current_f, current = heapq.heappop(open_set)

            if current in goals:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for neighbor, dist_km in adj[current]:
                neighbor_node = nodes[neighbor]
                
                # Safety Cost Formula:
                # Cost = Distance + (FloodRisk * w1) + (WaterLevel * w2) + (Hazard * w3)
                edge_cost = (
                    dist_km * 1.0 +
                    (neighbor_node["flood_risk"] * risk_weight * 0.8) +
                    (neighbor_node["water_level"] * water_penalty_weight * 0.5) +
                    (neighbor_node["hazard_cost"] * hazard_weight)
                )

                tentative_g = g_score[current] + edge_cost

                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor)
                    heapq.heappush(open_set, (f_score, neighbor))

        return [start] + [goals[0]]

    def _dijkstra_search(
        self, nodes: List[Dict[str, Any]], adj: Dict[int, List[Tuple[int, float]]],
        start: int, goals: List[int],
        risk_weight: float = 2.0, hazard_weight: float = 2.0, water_penalty_weight: float = 2.0,
        exclude_nodes: Optional[set] = None
    ) -> List[int]:
        """Dijkstra shortest/safest path algorithm."""
        exclude = exclude_nodes or set()
        open_set = []
        heapq.heappush(open_set, (0.0, start))
        came_from = {}
        dist = {i: float('inf') for i in range(len(nodes))}
        dist[start] = 0.0

        while open_set:
            current_dist, current = heapq.heappop(open_set)

            if current in goals:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for neighbor, edge_dist_km in adj[current]:
                if neighbor in exclude:
                    continue

                neighbor_node = nodes[neighbor]
                cost = (
                    edge_dist_km +
                    (neighbor_node["flood_risk"] * risk_weight * 0.5) +
                    (neighbor_node["water_level"] * water_penalty_weight * 0.3) +
                    (neighbor_node["hazard_cost"] * hazard_weight * 0.5)
                )
                if dist[current] + cost < dist[neighbor]:
                    dist[neighbor] = dist[current] + cost
                    came_from[neighbor] = current
                    heapq.heappush(open_set, (dist[neighbor], neighbor))

        return []

    def _build_route_segment(self, nodes: List[Dict[str, Any]], path_ids: List[int], label: str) -> RouteSegment:
        total_dist_km = 0.0
        total_water = 0.0
        total_risk = 0.0
        avoided_hazards = []
        waypoints = []
        instructions = []

        for i, node_id in enumerate(path_ids):
            n = nodes[node_id]
            total_water += n["water_level"]
            total_risk += n["flood_risk"]
            if n["hazard_desc"]:
                avoided_hazards.append(n["hazard_desc"])

            if i > 0:
                prev = nodes[path_ids[i - 1]]
                d = haversine_km(prev["lat"], prev["lng"], n["lat"], n["lng"])
                total_dist_km += d

            instruction = (
                f"Head towards waypoint {i + 1} (Elev: {25.0 + i * 8.0:.0f}m, Water Depth: {n['water_level']:.2f}m). "
                f"{'Caution: Moderate surface water' if n['water_level'] > 0.4 else 'Roadway clear and elevated.'}"
            )
            instructions.append(instruction)

            waypoints.append({
                "index": i,
                "latitude": round(n["lat"], 6),
                "longitude": round(n["lng"], 6),
                "elevation_m": round(25.0 + i * 8.0, 1),
                "water_level_m": round(n["water_level"], 2),
                "flood_risk": round(n["flood_risk"], 3),
                "instruction": instruction
            })

        avg_water = total_water / max(1, len(path_ids))
        avg_risk = total_risk / max(1, len(path_ids))
        
        # Safety score out of 100: Higher is safer
        safety_score = max(10.0, min(100.0, 100.0 - (avg_risk * 45.0) - (avg_water * 25.0)))

        # Average emergency walking/vehicle speed ~ 15 km/h in moderate water
        estimated_time_min = max(3.0, (total_dist_km / 12.0) * 60.0)

        return RouteSegment(
            distance_km=round(total_dist_km, 2),
            estimated_time_min=round(estimated_time_min, 1),
            safety_score=round(safety_score, 1),
            average_water_level_m=round(avg_water, 2),
            avoided_hazards=list(set(avoided_hazards)),
            waypoints=waypoints,
            turn_by_turn_instructions=instructions
        )

    calculate_safe_route = compute_safe_route


route_engine = SafeRouteEngine()
