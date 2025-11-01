from queues.filaProdutosPedidos import filaProdutosPedidos
from queues.filaDespachoGalpoes import filaDespachoGalpoes
import json
import math

SCHEMA_GALPOES = "./schema/cadastroGalpao.json"

def _calcula_distancia_euclidiana(pos_cliente, pos_galpao):
    '''(Helper) Calcula a distância Euclidiana entre dois pontos'''
    lat1, lon1 = pos_cliente
    lat2, lon2 = pos_galpao
    distancia = math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)
    return distancia

def _calcula_distancia_haversine(lat1, lon1, lat2, lon2):
    '''(Helper) Calcula a distância em KM usando Haversine (mais realista)'''
    R = 6371  # Raio da Terra em km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def calcularProximaRota():
    '''
    Processo 3: Lê da 'filaProdutosPedidos', consulta 'cadastroGalpão.json',
    calcula a melhor rota (galpão mais próximo do CLIENTE)
    e envia para 'filaDespachoGalpoes'.
    
    Retorna despacho com:
    - Localização do cliente
    - Localização do galpão selecionado
    - Distância calculada (Euclidiana e Haversine)
    - Informações de entrega
    '''
    
    if filaProdutosPedidos.empty():
        return {"status": 400, "mensagem": "Fila 'filaProdutosPedidos' está vazia."}

    pedido_enriquecido = filaProdutosPedidos.get()
    
    try:
        id_pedido = pedido_enriquecido["idPedido"]
        # Pega a localização do CLIENTE
        cliente_info = pedido_enriquecido["cliente"]
        pos_cliente = [cliente_info["latitude"], cliente_info["longitude"]]
    except KeyError as e:
        filaProdutosPedidos.task_done()
        print(f"(Processo 3) Erro: Pedido {pedido_enriquecido.get('idPedido')} mal formatado: {e}")
        return {"status": 500, "mensagem": "Dados do pedido incompletos"}

    # Carrega o JSON de Galpões (DB 2)
    try:
        with open(SCHEMA_GALPOES, "r", encoding='utf-8') as f_gal:
            dadosGalpoes = json.load(f_gal)
    except FileNotFoundError:
        filaProdutosPedidos.task_done()
        return {"status": 500, "mensagem": f"Erro: {SCHEMA_GALPOES} não encontrado."}

    # Lógica de Cálculo de Rota: Encontra o galpão mais próximo do CLIENTE
    melhor_galpao = None
    menor_distancia_euclidiana = float('inf')
    distancia_haversine = 0
    
    for galpao in dadosGalpoes.get('galpoes', []):
        pos_galpao = [galpao["latitude"], galpao["longitude"]]
        dist_euclidiana = _calcula_distancia_euclidiana(pos_cliente, pos_galpao)
        dist_haversine = _calcula_distancia_haversine(pos_cliente[0], pos_cliente[1], pos_galpao[0], pos_galpao[1])
        
        if dist_euclidiana < menor_distancia_euclidiana:
            menor_distancia_euclidiana = dist_euclidiana
            distancia_haversine = dist_haversine
            melhor_galpao = galpao
    
    if not melhor_galpao:
        filaProdutosPedidos.task_done()
        return {"status": 404, "mensagem": "Nenhum galpão cadastrado."}

    # Monta o resultado final para a Fila 3
    despacho = {
        "idPedido": id_pedido,
        "cliente": {
            "nome": cliente_info.get("nome"),
            "endereco": cliente_info.get("endereco"),
            "coordenadas": {
                "latitude": pos_cliente[0],
                "longitude": pos_cliente[1]
            }
        },
        "produto": {
            "idProduto": pedido_enriquecido["produto"]["idProduto"],
            "nome": pedido_enriquecido["produto"]["nome"],
            "peso_kg": pedido_enriquecido["produto"]["peso_kg"],
            "quantidade": pedido_enriquecido.get("quantidade", 1),
            "peso_total_kg": pedido_enriquecido["produto"]["peso_kg"] * pedido_enriquecido.get("quantidade", 1)
        },
        "galpao_origem": {
            "idGalpao": melhor_galpao["idGalpao"],
            "nome": melhor_galpao["nome"],
            "descricao": melhor_galpao.get("descricao"),
            "coordenadas": {
                "latitude": melhor_galpao["latitude"],
                "longitude": melhor_galpao["longitude"]
            },
            "capacidade_items": melhor_galpao.get("capacidade_items")
        },
        "distancia": {
            "euclidiana_unidades": round(menor_distancia_euclidiana, 2),
            "haversine_km": round(distancia_haversine, 2)
        },
        "status_despacho": "PRONTO_PARA_ENTREGA",
        "timestamp": None  # Será preenchido ao despachar
    }
    
    # Coloca na Fila 3
    filaDespachoGalpoes.put(despacho)
    print(f"(Processo 3) Pedido {id_pedido} (Cliente: {cliente_info['nome']}) alocado ao Galpão {melhor_galpao['idGalpao']}")
    print(f"   → Cliente em ({pos_cliente[0]}, {pos_cliente[1]})")
    print(f"   → Galpão em ({melhor_galpao['latitude']}, {melhor_galpao['longitude']})")
    print(f"   → Distância: {round(menor_distancia_euclidiana, 2)} unidades | {round(distancia_haversine, 2)} km")
    
    filaProdutosPedidos.task_done()
    return {"status": 200, "idPedido": id_pedido}
