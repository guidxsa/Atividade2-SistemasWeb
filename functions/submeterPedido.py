from queue import filaPedidos

def submeterPedido(pedido):
    '''
    Processo 1: Adiciona um novo pedido (vindo do 'Actor') 
    à 'filaPedidos'.
    
    Pedido agora inclui:
    - Localização do CLIENTE (latitude/longitude)
    - ID do produto
    - Quantidade
    
    Exemplo:
    {
        "idPedido": 1,
        "idProduto": 1,
        "quantidade": 2,
        "cliente": {
            "nome": "João Silva",
            "latitude": 2.5,
            "longitude": 3.5,
            "endereco": "Rua das Flores, 123 - Manhattan"
        }
    }
    '''
    try:
        filaPedidos.put(pedido)
        print(f"(Processo 1) Pedido {pedido['idPedido']} submetido à 'filaPedidos'.")
        print(f"   → Cliente: {pedido['cliente']['nome']} em ({pedido['cliente']['latitude']}, {pedido['cliente']['longitude']})")
        return True
    except Exception as e:
        print(f"(Processo 1) Erro: {e}")
        return False
