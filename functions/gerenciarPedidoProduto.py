from queues.filaPedidos import filaPedidos
from queues.filaProdutosPedidos import filaProdutosPedidos
import json

SCHEMA_PRODUTOS = "./schema/cadastroProduto.json"

def gerenciaProximoPedido():
    '''
    Processo 2: Lê da 'filaPedidos', consulta 'cadastroProduto.json',
    enriquece o pedido com localização do produto e envia para 'filaProdutosPedidos'.
    '''
    
    if filaPedidos.empty():
        return {"status": 400, "mensagem": "Fila 'filaPedidos' está vazia."}

    pedido = filaPedidos.get()
    
    try:
        id_pedido = pedido["idPedido"]
        id_produto = pedido["idProduto"]
    except KeyError as e:
        filaPedidos.task_done()
        print(f"(Processo 2) Erro: Pedido {pedido.get('idPedido')} mal formatado: {e}")
        return {"status": 500, "mensagem": "Dados do pedido incompletos"}

    # Carrega o JSON de Produtos (DB 1)
    try:
        with open(SCHEMA_PRODUTOS, "r", encoding='utf-8') as f_prod:
            dadosProdutos = json.load(f_prod)
    except FileNotFoundError:
        filaPedidos.task_done()
        return {"status": 500, "mensagem": f"Erro: {SCHEMA_PRODUTOS} não encontrado."}

    # Lógica de Gerenciamento: Encontra o produto
    produto_encontrado = None
    for produto in dadosProdutos.get('produtos', []):
        if produto["idProduto"] == id_produto:
            produto_encontrado = produto
            break
    
    if not produto_encontrado:
        filaPedidos.task_done()
        print(f"(Processo 2) Pedido {id_pedido} REJEITADO. Produto {id_produto} não cadastrado.")
        return {"status": 404, "mensagem": f"Produto {id_produto} não cadastrado."}

    # Enriquece o pedido com os dados do produto + LOCALIZAÇÃO
    pedido["produto"] = {
        "idProduto": produto_encontrado["idProduto"],
        "nome": produto_encontrado["nome"],
        "peso_kg": produto_encontrado["peso_kg"],
        "localizacao_padrao": produto_encontrado.get("localizacao_padrao", {})
    }
    
    # Coloca na Fila 2
    filaProdutosPedidos.put(pedido)
    print(f"(Processo 2) Pedido {id_pedido} (Produto: {produto_encontrado['nome']}) validado e enviado para 'filaProdutosPedidos'.")
    print(f"   → Localização Padrão do Produto: ({produto_encontrado['localizacao_padrao'].get('latitude')}, {produto_encontrado['localizacao_padrao'].get('longitude')})")
    
    filaPedidos.task_done()
    return {"status": 200, "idPedido": id_pedido}
