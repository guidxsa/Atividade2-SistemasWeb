import sys
import os
import json
import time

# --- Configuração de Path ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)
# --------------------------

from queues.filaPedidos import filaPedidos
from queues.filaProdutosPedidos import filaProdutosPedidos
from queues.filaDespachoGalpoes import filaDespachoGalpoes
from functions.submeterPedido import submeterPedido
from functions.gerenciarPedidoProduto import gerenciaProximoPedido
from functions.calcularRotaPedidos import calcularProximaRota

def setup_test_environment():
    """ Limpa todas as 3 filas antes de cada teste """
    while not filaPedidos.empty():
        filaPedidos.get(block=False)
        filaPedidos.task_done()
    while not filaProdutosPedidos.empty():
        filaProdutosPedidos.get(block=False)
        filaProdutosPedidos.task_done()
    while not filaDespachoGalpoes.empty():
        filaDespachoGalpoes.get(block=False)
        filaDespachoGalpoes.task_done()
    
    print("\n--- Setup Teste: Todas as 3 filas limpas ---")

def test_fluxo_completo_com_localizacao():
    """ 
    Testa o fluxo de logística com LOCALIZAÇÃO:
    - Cliente em NY (2.5, 3.5)
    - Produto disponível em estoque
    - Galpão mais próximo selecionado
    - Distância calculada
    """
    setup_test_environment()
    
    # Payload com localização do CLIENTE (simulando pedido real)
    pedido_teste = {
        "idPedido": 1,
        "idProduto": 1,
        "quantidade": 2,
        "cliente": {
            "nome": "João Silva",
            "latitude": 2.5,
            "longitude": 3.5,
            "endereco": "Rua das Flores, 123 - Manhattan, NY"
        }
    }
    
    # 1. Processo 1: Submeter Pedido
    print("\n" + "="*60)
    print("PROCESSO 1: SUBMETER PEDIDO")
    print("="*60)
    resultado1 = submeterPedido(pedido_teste)
    assert resultado1 == True
    assert filaPedidos.qsize() == 1
    assert filaProdutosPedidos.qsize() == 0
    assert filaDespachoGalpoes.qsize() == 0
    print("✓ Processo 1 OK")
    
    # 2. Processo 2: Gerenciar Pedido e Produto
    print("\n" + "="*60)
    print("PROCESSO 2: GERENCIAR PEDIDO + PRODUTO")
    print("="*60)
    res_gerencia = gerenciaProximoPedido()
    assert res_gerencia["status"] == 200, f"Processo 2 falhou: {res_gerencia}"
    assert filaPedidos.empty() == True
    assert filaProdutosPedidos.qsize() == 1
    assert filaDespachoGalpoes.qsize() == 0
    print("✓ Processo 2 OK")
    
    # 3. Processo 3: Calcular Rota
    print("\n" + "="*60)
    print("PROCESSO 3: CALCULAR ROTA + DISTÂNCIA")
    print("="*60)
    res_calculo = calcularProximaRota()
    assert res_calculo["status"] == 200, f"Processo 3 falhou: {res_calculo}"
    assert filaProdutosPedidos.empty() == True
    assert filaDespachoGalpoes.qsize() == 1
    print("✓ Processo 3 OK")
    
    # 4. Verificação Final
    print("\n" + "="*60)
    print("DESPACHO FINAL - RESULTADO COMPLETO")
    print("="*60)
    despacho_final = filaDespachoGalpoes.get()
    
    print(f"\n{json.dumps(despacho_final, indent=2, ensure_ascii=False)}\n")
    
    # Validações
    assert despacho_final["idPedido"] == 1
    assert despacho_final["cliente"]["nome"] == "João Silva"
    assert despacho_final["cliente"]["coordenadas"]["latitude"] == 2.5
    assert despacho_final["cliente"]["coordenadas"]["longitude"] == 3.5
    assert despacho_final["produto"]["nome"] == "NEW BALANCE 1906 A"
    assert despacho_final["produto"]["quantidade"] == 2
    assert despacho_final["produto"]["peso_total_kg"] == 5.0
    assert despacho_final["galpao_origem"]["idGalpao"] == "G1"
    assert despacho_final["distancia"]["euclidiana_unidades"] > 0
    assert despacho_final["distancia"]["haversine_km"] > 0
    
    print("✓ Todas as validações OK\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SIMULAÇÃO: LOGÍSTICA COM CÁLCULO DE DISTÂNCIA")
    print("="*60)
    print("Sistema de entrega que calcula a rota mais curta")
    print("entre o cliente e o galpão de origem")
    print("="*60)
    
    try:
        test_fluxo_completo_com_localizacao()
        print("\n" + "="*60)
        print("   ✅ SIMULAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ ERRO DE ASSERTIVA: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
