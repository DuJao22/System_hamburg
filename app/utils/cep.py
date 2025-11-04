import requests
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

def buscar_cep(cep: str) -> Optional[Dict[str, str]]:
    """
    Busca informações de endereço a partir de um CEP usando ViaCEP.
    
    Args:
        cep: CEP a ser buscado (com ou sem formatação)
        
    Returns:
        Dicionário com dados do endereço ou None se não encontrado
    """
    cep_limpo = ''.join(filter(str.isdigit, cep))
    
    if len(cep_limpo) != 8:
        return None
    
    try:
        response = requests.get(
            f'https://viacep.com.br/ws/{cep_limpo}/json/',
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('erro'):
            return None
        
        return {
            'cep': data.get('cep', ''),
            'logradouro': data.get('logradouro', ''),
            'complemento': data.get('complemento', ''),
            'bairro': data.get('bairro', ''),
            'localidade': data.get('localidade', ''),
            'uf': data.get('uf', ''),
            'ibge': data.get('ibge', ''),
            'ddd': data.get('ddd', '')
        }
    except Exception as e:
        logger.error(f"Erro ao buscar CEP {cep}: {str(e)}", exc_info=True)
        return None


def buscar_endereco(estado: str, cidade: str, logradouro: str) -> Optional[List[Dict[str, str]]]:
    """
    Busca reversa: encontra CEPs a partir de um endereço usando ViaCEP.
    
    Args:
        estado: UF (2 letras, ex: 'MG')
        cidade: Nome da cidade (ex: 'Contagem')
        logradouro: Nome da rua/avenida (mínimo 3 caracteres)
        
    Returns:
        Lista de endereços encontrados ou None se houver erro
    """
    if not estado or not cidade or not logradouro:
        return None
    
    if len(logradouro) < 3:
        return None
    
    try:
        url = f'https://viacep.com.br/ws/{estado}/{cidade}/{logradouro}/json/'
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, dict) and data.get('erro'):
            return None
        
        if not isinstance(data, list):
            return None
        
        resultados = []
        for item in data:
            if not item.get('erro'):
                resultados.append({
                    'cep': item.get('cep', ''),
                    'logradouro': item.get('logradouro', ''),
                    'complemento': item.get('complemento', ''),
                    'bairro': item.get('bairro', ''),
                    'localidade': item.get('localidade', ''),
                    'uf': item.get('uf', ''),
                    'ibge': item.get('ibge', ''),
                    'ddd': item.get('ddd', '')
                })
        
        return resultados if resultados else None
    except Exception as e:
        logger.error(f"Erro ao buscar endereço {estado}/{cidade}/{logradouro}: {str(e)}", exc_info=True)
        return None
