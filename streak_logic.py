"""
Lógica de cálculo de streak.

Regra:
- O streak conta dias consecutivos terminando hoje ou ontem.
  (Se o usuário ainda não marcou hoje, o streak de ontem continua ativo
  até o fim do dia atual, para não punir quem ainda vai marcar.)
- Qualquer dia faltando quebra a sequência.
- O recorde (maior streak já alcançado) também é calculado a partir do
  histórico completo de registros.
"""

from datetime import date, timedelta

"""Recebe uma lista de registros (date, completed) e retorna um set de
objetos date() em que o hábito foi marcado como concluído."""
def _parse_completed_dates(records):
    dates = set()
    for r in records:
        if r["completed"]:
            year, month, day = map(int, r["date"].split("-"))
            dates.add(date(year, month, day))
    return dates

"""Calcula o streak atual."""
def calculate_current_streak(records):
    completed_dates = _parse_completed_dates(records)  # <-- AQUI ESTAVA O ERRO
    if not completed_dates:
        return 0

    today = date.today()
    yesterday = today - timedelta(days=1)

    cursor = today if today in completed_dates else yesterday
    if cursor not in completed_dates:
        return 0

    streak = 0
    while cursor in completed_dates:
        streak += 1
        cursor -= timedelta(days=1)

    return streak

"""Calcula a maior sequência de dias consecutivos já alcançada"""
def calculate_record(records):
    completed_dates = sorted(_parse_completed_dates(records))
    if not completed_dates:
        return 0

    longest = 1
    current = 1
    for i in range(1, len(completed_dates)):
        diff = (completed_dates[i] - completed_dates[i - 1]).days
        if diff == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest