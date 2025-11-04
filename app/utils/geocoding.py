import os
import requests
import math
from typing import Tuple, Optional

def get_coordinates_from_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Converte um endereço em coordenadas (latitude, longitude) usando Google Maps Geocoding API.
    
    Args:
        address: Endereço completo para geocodificar
        
    Returns:
        Tupla (latitude, longitude) ou None se não encontrado
    """
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    if not api_key:
        return None
    
    try:
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'address': address,
            'key': api_key,
            'region': 'br'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('results'):
            location = data['results'][0]['geometry']['location']
            return (location['lat'], location['lng'])
        
        return None
    except Exception as e:
        print(f"Erro na geocodificação: {str(e)}")
        return None


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância entre duas coordenadas geográficas usando a fórmula de Haversine.
    
    Args:
        lat1: Latitude do ponto 1
        lon1: Longitude do ponto 1
        lat2: Latitude do ponto 2
        lon2: Longitude do ponto 2
        
    Returns:
        Distância em quilômetros
    """
    # Raio da Terra em km
    R = 6371.0
    
    # Converter para radianos
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferenças
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance


def is_within_delivery_radius(
    address: str, 
    store_lat: float, 
    store_lon: float, 
    radius_km: float
) -> Tuple[bool, Optional[float]]:
    """
    Verifica se um endereço está dentro do raio de entrega.
    
    Args:
        address: Endereço do cliente
        store_lat: Latitude da loja
        store_lon: Longitude da loja
        radius_km: Raio máximo de entrega em km
        
    Returns:
        Tupla (está_dentro_do_raio, distancia_calculada)
    """
    coordinates = get_coordinates_from_address(address)
    
    if not coordinates:
        return (False, None)
    
    customer_lat, customer_lon = coordinates
    distance = calculate_distance(store_lat, store_lon, customer_lat, customer_lon)
    
    is_within = distance <= radius_km
    
    return (is_within, distance)
