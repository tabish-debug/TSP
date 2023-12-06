import networkx as nx
from fastapi import status
from itertools import combinations
from unittest.mock import patch

from app.utils import execute, distance, create_graph, PIZZA_SHOP, tsp_closest_to_max_distance
from .override import client


def test_upload_csv():
    csv_file_content = 'order_time,address\n"8/11/2022 12:16","1016, Huntingdon Drive, San Jose, Santa Clara County, California, 95129, United States"'
    files = {"file": ("test.csv", csv_file_content)}
    response = client.post("api/drone/upload", files=files)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "csv file uploaded successfully"}


def test_execute():
    with patch('app.utils.geolocator.geocode') as mock_geocode:
        mock_geocode.return_value.latitude = 40.7128
        mock_geocode.return_value.longitude = -74.0060
        mock_geocode.return_value.address = 'New York, NY'

        data = {'address': 'New York, NY', 'order_time': '2023-12-01T12:00:00'}
        result = execute(data)

        assert result == {
            'order_time': '2023-12-01T12:00:00',
            'location': 'New York, NY',
            'latitude': 40.7128,
            'longitude': -74.0060
        }


def test_distance():
    assert distance(40.7128, 40.7128, -74.0060, -74.0060) == 0.0

    lat1, lon1 = 37.7749, -122.4194
    lat2, lon2 = 34.0522, -118.2437

    expected_distance = 347.471

    assert abs(distance(lat1, lat2, lon1, lon2) - expected_distance) < 0.5

    earth_radius_km = 6371.0
    expected_distance_km = expected_distance * 1.60934

    assert abs(distance(lat1, lat2, lon1, lon2, r=earth_radius_km) -
               expected_distance_km) < 0.5


def test_create_graph():

    graph = create_graph([])
    assert isinstance(graph, nx.Graph)
    assert graph.number_of_nodes() == 1
    assert graph.number_of_edges() == 0

    data = [{'location': 'Location A',
             'latitude': 37.7749, 'longitude': -122.4194}]
    graph = create_graph(data)
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1

    data = [
        {'location': 'Location A', 'latitude': 37.7749, 'longitude': -122.4194},
        {'location': 'Location B', 'latitude': 34.0522, 'longitude': -118.2437},
        {'location': 'Location C', 'latitude': 41.8781, 'longitude': -87.6298},
    ]
    graph = create_graph(data)
    assert graph.number_of_nodes() == len(data) + 1
    assert graph.number_of_edges() == len(
        list(combinations(data + [PIZZA_SHOP], 2)))

    edge = list(graph.edges(data=True))[0]
    nodeA, nodeB, weight_data = edge
    latitude1, longitude1 = PIZZA_SHOP['latitude'], PIZZA_SHOP['longitude']
    latitude2, longitude2 = data[0]['latitude'], data[0]['longitude']
    expected_weight = round(
        distance(latitude1, latitude2, longitude1, longitude2), 2)

    assert weight_data['weight'] == expected_weight


def test_tsp_closest_to_max_distance():
    graph = nx.Graph()
    path, distance = tsp_closest_to_max_distance(graph)
    assert path == ()
    assert distance == 0

    graph.add_node(PIZZA_SHOP['location'])
    path, distance = tsp_closest_to_max_distance(graph)
    assert path == ()
    assert distance == 0

    graph.add_node('Location A')
    graph.add_edge(PIZZA_SHOP['location'], 'Location A', weight=10)
    path, distance = tsp_closest_to_max_distance(graph)
    assert path == (PIZZA_SHOP['location'],
                    'Location A', PIZZA_SHOP['location'])

    assert distance == 20

    graph.add_node('Location B')
    graph.add_edge('Location A', 'Location B', weight=20)
    graph.add_edge('Location B', PIZZA_SHOP['location'], weight=15)
    path, distance = tsp_closest_to_max_distance(graph, max_distance=30)
    assert path == (PIZZA_SHOP['location'],
                    'Location B', PIZZA_SHOP['location'])
    assert distance == 30

    graph.add_node('Location C')
    graph.add_edge('Location A', 'Location C', weight=25)
    graph.add_edge('Location C', PIZZA_SHOP['location'], weight=10)
    graph.add_edge('Location B', 'Location C', weight=50)
    path, distance = tsp_closest_to_max_distance(graph, max_distance=50)
    assert distance == 45
