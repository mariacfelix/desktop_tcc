def aplicar_mascara_data(valor: str) -> str:
    nums = "".join(c for c in (valor or "") if c.isdigit())[:8]
    r = ""
    for i, c in enumerate(nums):
        if i == 2 or i == 4:
            r += "/"
        r += c
    return r