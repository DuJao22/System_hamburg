from flask import Blueprint, request, jsonify
from app.utils.cep import buscar_cep, buscar_endereco

cep_api_bp = Blueprint('cep_api', __name__, url_prefix='/api/cep')

@cep_api_bp.route('/buscar/<cep>', methods=['GET'])
def api_buscar_cep(cep):
    """
    API para buscar endereço por CEP.
    Exemplo: /api/cep/buscar/01001000
    """
    resultado = buscar_cep(cep)
    
    if resultado:
        return jsonify({
            'success': True,
            'data': resultado
        })
    else:
        return jsonify({
            'success': False,
            'error': 'CEP não encontrado'
        }), 404


@cep_api_bp.route('/buscar-endereco', methods=['POST'])
def api_buscar_endereco():
    """
    API para busca reversa de CEP por endereço.
    Exemplo de POST body: {"estado": "MG", "cidade": "Contagem", "logradouro": "Rua Judith"}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Dados não fornecidos'
        }), 400
    
    estado = data.get('estado', '').strip()
    cidade = data.get('cidade', '').strip()
    logradouro = data.get('logradouro', '').strip()
    
    if not estado or not cidade or not logradouro:
        return jsonify({
            'success': False,
            'error': 'Estado, cidade e logradouro são obrigatórios'
        }), 400
    
    if len(logradouro) < 3:
        return jsonify({
            'success': False,
            'error': 'O logradouro deve ter no mínimo 3 caracteres'
        }), 400
    
    resultados = buscar_endereco(estado, cidade, logradouro)
    
    if resultados:
        return jsonify({
            'success': True,
            'data': resultados
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Nenhum endereço encontrado'
        }), 404
