from datetime import datetime, timezone, timedelta

# Timezone de Brasília (UTC-3)
BRASILIA_TZ = timezone(timedelta(hours=-3))

def get_brasilia_time():
    """Retorna o datetime atual no horário de Brasília (UTC-3)"""
    return datetime.now(BRASILIA_TZ)

def utcnow_brasilia():
    """Função compatível com datetime.utcnow() mas retorna horário de Brasília"""
    return datetime.now(BRASILIA_TZ).replace(tzinfo=None)
