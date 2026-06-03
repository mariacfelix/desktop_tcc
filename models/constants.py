API_BASE       = "http://localhost:8080"
API_GASTOS     = f"{API_BASE}/apiGastos"
API_MARMITERIA = f"{API_BASE}/apiMarmiteria"
API_CARDAPIO   = f"{API_BASE}/apiCardapio"
API_PEDIDO     = f"{API_BASE}/apiPedido"

CATEGORIAS = [
    "Proteínas", "Carboidratos", "Legumes", "Embalagens", "Gás / Energia",
    "Aluguel", "Transporte", "Mão de Obra", "Equipamentos", "Outros",
]

CORES_CATEGORIA = {
    "Proteínas": "#A0522D", "Carboidratos": "#8B6914", "Legumes": "#6B8E23",
    "Embalagens": "#CC7722", "Gás / Energia": "#CD853F", "Aluguel": "#A0522D",
    "Transporte": "#8B4513", "Mão de Obra": "#D2691E", "Equipamentos": "#B8860B",
    "Outros": "#696969",
}

COR_PRIMARIA   = "#A0522D"
COR_SECUNDARIA = "#FF8C42"
COR_FUNDO      = "#ECE0D4"
COR_CARD       = "#E6D4BA"
COR_SIDEBAR    = "#E6D4BA"
COR_BORDA      = "#563903"
COR_TEXTO      = "#2C2C2C"
COR_SUBTEXTO   = "#4A4A4A"
COR_DESTAQUE   = "#CC7722"
COR_ERRO       = "#C62828"
COR_SUCESSO    = "#388E3C"

PRINTER_VENDOR_ID  = 0x0483
PRINTER_PRODUCT_ID = 0x5743
PRINTER_WIDTH_MM   = 55
PRINTER_CHAR_WIDTH = 32