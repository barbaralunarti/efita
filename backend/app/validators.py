# backend/app/validators.py
"""
Validadores customizados para a aplicação EFITA.
"""
import re


def validar_cpf(cpf: str) -> bool:
    """
    Valida um CPF usando o algoritmo de dígito verificador (Módulo 11).
    
    Args:
        cpf: String com CPF (pode conter pontos e hífens)
    
    Returns:
        bool: True se CPF é válido, False caso contrário
    
    Exemplos:
        >>> validar_cpf("11366554796")
        True
        >>> validar_cpf("00000000000")
        False
        >>> validar_cpf("111.665.547-96")
        True
    """
    # Remove caracteres não dígitos
    cpf_limpo = re.sub(r'\D', '', cpf)
    
    # Valida comprimento
    if len(cpf_limpo) != 11:
        return False
    
    # Rejeita sequências repetidas (000...000, 111...111, etc)
    if cpf_limpo == cpf_limpo[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_limpo[9]) != digito1:
        return False
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_limpo[10]) != digito2:
        return False
    
    return True


def normalizar_cpf(cpf: str) -> str:
    """
    Remove caracteres de formatação de um CPF.
    
    Args:
        cpf: CPF com ou sem formatação
    
    Returns:
        str: CPF com apenas dígitos (11 caracteres)
    
    Exemplo:
        >>> normalizar_cpf("111.665.547-96")
        "11366554796"
    """
    return re.sub(r'\D', '', cpf)
