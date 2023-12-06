from math import radians, cos, sin, asin, sqrt
from itertools import permutations, combinations
from copy import deepcopy
from passlib.context import CryptContext
from concurrent.futures import ThreadPoolExecutor
from geopy.geocoders import Nominatim
import networkx as nx


PIZZA_SHOP = {"location": "Pizza Shop",
              "latitude": 37.33182, "longitude": -122.03118}
DRONE_BATTERY_DECHARGE_DISTANCE = 35

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
geolocator = Nominatim(
    user_agent="jbtc", timeout=10)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def execute(data):
    address = data.get('address', None)
    order_time = data.get('order_time', None)

    latitude = None
    longitude = None
    location = None

    if address:
        location = geolocator.geocode(address)
        latitude = location.latitude
        longitude = location.longitude

    return dict(
        order_time=order_time,
        location=location.address,
        latitude=latitude,
        longitude=longitude
    )


def process_data(data):
    num_threads = 5

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(execute, data))

    return results


def distance(latitute1, latitute2, longitude1, longitude2, r=3956):

    latitute1 = radians(latitute1)
    latitute2 = radians(latitute2)
    longitude1 = radians(longitude1)
    longitude2 = radians(longitude2)

    dlongitude = longitude2 - longitude1
    dlatitute = latitute2 - latitute1
    a = sin(dlatitute / 2)**2 + cos(latitute1) * \
        cos(latitute2) * sin(dlongitude / 2)**2

    c = 2 * asin(sqrt(a))

    return round(c * r, 3)


def tsp_closest_to_max_distance(graph, max_distance=DRONE_BATTERY_DECHARGE_DISTANCE, start_at=PIZZA_SHOP.get("location")):
    complete_graph = nx.complete_graph(graph.nodes)

    best_path = ()
    best_distance = 0
    number_of_nodes = complete_graph.number_of_nodes()

    for path_length in range(1, number_of_nodes + 1):
        for path in permutations(complete_graph.nodes - {start_at}, path_length):
            path = (start_at,) + path

            distance = sum(graph[path[i]][path[i + 1]]['weight']
                           for i in range(len(path) - 1))

            distance += graph[path[-1]][path[0]]['weight']

            if distance <= max_distance and distance > best_distance:
                best_distance = distance
                best_path = path

    if best_path:
        best_path = best_path + (best_path[0],)

    return best_path, best_distance


def create_graph(data: list):
    G = nx.Graph()

    collected_data = deepcopy(data)

    collected_data.insert(0, PIZZA_SHOP)

    data_combinations = combinations(collected_data, 2)

    for i in collected_data:
        G.add_node(i.get('location'))

    for data_combination in data_combinations:
        nodeA, nodeB = data_combination
        latitude1 = nodeA.get('latitude')
        latitude2 = nodeB.get('latitude')
        longitude1 = nodeA.get('longitude')
        longitude2 = nodeB.get('longitude')

        weight = round(distance(latitude1, latitude2,
                       longitude1, longitude2), 2)

        G.add_edge(nodeA.get('location'), nodeB.get('location'), weight=weight)

    return G


def add_optimal_path_order(results, optimal_paths):
    for i, optimal_path in enumerate(optimal_paths, 0):
        result = next(
            (item for item in results if item['location'] == optimal_path), None)
        if result:
            result['order_by'] = i
