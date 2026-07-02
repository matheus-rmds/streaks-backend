"""
API do Streaks

Permite "cadastrar" e entrar na conta de usuários, criar hábitos
diários, marcar registros e calcular o streak de cada hábito.

Para rodar (Pela primeira vez):
  pip install -r requirements.txt
  python -m venv venv
  venv\Scripts\activate
  python app.py

Para rodar:
  venv\Scripts\activate
  python app.py

Swagger:
    http://localhost:5000/apidocs
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
from datetime import date
import calendar as calendar_module

from database import get_connection, init_db
from streak_logic import calculate_current_streak, calculate_record

MONTH_NAMES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

app = Flask(__name__)
CORS(app)

app.config["SWAGGER"] = {
    "title": "Streaks API",
    "uiversion": 3,
}
swagger = Swagger(app, template={
    "info": {
        "title": "Streaks API",
        "description": "API para rastreamento de hábitos com cálculo automático de streaks.",
        "version": "1.0.0",
    }
})

init_db()

@app.route("/register", methods=["POST"])
def register_user():
    """
    Cadastrar um novo usuário.
    ---
    tags:
      - Usuários
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
          properties:
            name:
              type: string
              example: User
            email:
              type: string
              example: user@email.com
    responses:
      201:
        description: Usuário criado com sucesso
        examples:
          application/json: {"id": 1, "name": "User", "email": "user@email.com"}
      400:
        description: Dados inválidos (nome ou email ausentes)
      409:
        description: Email já cadastrado
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return jsonify({"error": "Os campos 'name' e 'email' são obrigatórios."}), 400

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, created_at) VALUES (?, ?, ?)",
            (name, email, date.today().isoformat()),
        )
        conn.commit()
        new_id = cursor.lastrowid
        return jsonify({"id": new_id, "name": name, "email": email}), 201
    except Exception:
        return jsonify({"error": "Este email já está cadastrado."}), 409
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    """
    Entrar na conta de um usuário existente.
    ---
    tags:
      - Usuários
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              example: user@email.com
    responses:
      200:
        description: Usuário encontrado
        examples:
          application/json: {"id": 1, "name": "User", "email": "user@email.com"}
      400:
        description: Email não informado
      404:
        description: Nenhum usuário encontrado com esse email
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "O campo 'email' é obrigatório."}), 400

    conn = get_connection()
    user = conn.execute(
        "SELECT id, name, email FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if user is None:
        return jsonify({"error": "Usuário não encontrado. Cadastre-se primeiro."}), 404

    return jsonify(dict(user)), 200

@app.route("/habits", methods=["POST"])
def create_habit():
    """
    Cria um novo hábito vinculado a um usuário.
    ---
    tags:
      - Hábitos
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - name
          properties:
            user_id:
              type: integer
              example: 1
            name:
              type: string
              example: Beber 2L de água
            frequency_goal:
              type: integer
              example: 7
    responses:
      201:
        description: Hábito criado com sucesso
      400:
        description: Dados inválidos
      404:
        description: Usuário não encontrado
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    name = data.get("name")
    frequency_goal = data.get("frequency_goal", 7)

    if not user_id or not name:
        return jsonify({"error": "Os campos 'user_id' e 'name' são obrigatórios."}), 400

    conn = get_connection()
    user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        conn.close()
        return jsonify({"error": "Usuário não encontrado."}), 404

    cursor = conn.execute(
        "INSERT INTO habits (user_id, name, frequency_goal, created_at) VALUES (?, ?, ?, ?)",
        (user_id, name, frequency_goal, date.today().isoformat()),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "id": new_id,
        "user_id": user_id,
        "name": name,
        "frequency_goal": frequency_goal,
    }), 201

@app.route("/habits/user/<int:user_id>", methods=["GET"])
def list_habits(user_id):
    """
    Lista todos os hábitos de um usuário, já com o streak atual de cada um.
    ---
    tags:
      - Hábitos
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: Lista de hábitos do usuário
      404:
        description: Usuário não encontrado
    """
    conn = get_connection()
    user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        conn.close()
        return jsonify({"error": "Usuário não encontrado."}), 404

    habits = conn.execute(
        "SELECT * FROM habits WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()

    result = []
    for h in habits:
        records = conn.execute(
            "SELECT date, completed FROM records WHERE habit_id = ?", (h["id"],)
        ).fetchall()
        result.append({
            "id": h["id"],
            "name": h["name"],
            "frequency_goal": h["frequency_goal"],
            "created_at": h["created_at"],
            "current_streak": calculate_current_streak(records),
        })

    conn.close()
    return jsonify(result), 200

@app.route("/habits/<int:habit_id>", methods=["PUT"])
def edit_habit(habit_id):
    """
    Edita o nome de um hábito existente.
    ---
    tags:
      - Hábitos
    parameters:
      - in: path
        name: habit_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: Beber 3L de água
            frequency_goal:
              type: integer
              example: 7
    responses:
      200:
        description: Hábito atualizado com sucesso
      400:
        description: Dados inválidos (nome ausente ou vazio)
      404:
        description: Hábito não encontrado
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "O campo 'name' é obrigatório."}), 400

    conn = get_connection()
    habit = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
    if habit is None:
        conn.close()
        return jsonify({"error": "Hábito não encontrado."}), 404

    frequency_goal = data.get("frequency_goal", habit["frequency_goal"])

    conn.execute(
        "UPDATE habits SET name = ?, frequency_goal = ? WHERE id = ?",
        (name, frequency_goal, habit_id),
    )
    conn.commit()
    conn.close()

    return jsonify({
        "id": habit_id,
        "name": name,
        "frequency_goal": frequency_goal,
    }), 200


@app.route("/habits/<int:habit_id>", methods=["DELETE"])
def delete_habit(habit_id):
    """
    Remove um hábito e todos os seus registros associados.
    ---
    tags:
      - Hábitos
    parameters:
      - in: path
        name: habit_id
        type: integer
        required: true
    responses:
      200:
        description: Hábito removido com sucesso
      404:
        description: Hábito não encontrado
    """
    conn = get_connection()
    habit = conn.execute("SELECT id FROM habits WHERE id = ?", (habit_id,)).fetchone()
    if habit is None:
        conn.close()
        return jsonify({"error": "Hábito não encontrado."}), 404

    conn.execute("DELETE FROM records WHERE habit_id = ?", (habit_id,))
    conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Hábito removido com sucesso."}), 200

@app.route("/records", methods=["POST"])
def toggle_record():
    """
    Marca um hábito como concluído em uma data específica.
    Se já existir um registro para essa data, ele é atualizado.
    ---
    tags:
      - Registros
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - habit_id
          properties:
            habit_id:
              type: integer
              example: 1
            date:
              type: string
              example: "2026-06-30"
              description: "Formato AAAA-MM-DD. Se omitido, usa a data de hoje."
            completed:
              type: boolean
              example: true
    responses:
      200:
        description: Registro salvo, retorna também o streak atualizado
      400:
        description: Dados inválidos
      404:
        description: Hábito não encontrado
    """
    data = request.get_json(silent=True) or {}
    habit_id = data.get("habit_id")
    record_date = data.get("date", date.today().isoformat())
    completed = 1 if data.get("completed", True) else 0

    if not habit_id:
        return jsonify({"error": "O campo 'habit_id' é obrigatório."}), 400

    conn = get_connection()
    habit = conn.execute("SELECT id FROM habits WHERE id = ?", (habit_id,)).fetchone()
    if habit is None:
        conn.close()
        return jsonify({"error": "Hábito não encontrado."}), 404

    conn.execute("""
        INSERT INTO records (habit_id, date, completed)
        VALUES (?, ?, ?)
        ON CONFLICT(habit_id, date) DO UPDATE SET completed = excluded.completed
    """, (habit_id, record_date, completed))
    conn.commit()

    records = conn.execute(
        "SELECT date, completed FROM records WHERE habit_id = ?", (habit_id,)
    ).fetchall()
    conn.close()

    return jsonify({
        "habit_id": habit_id,
        "date": record_date,
        "completed": bool(completed),
        "current_streak": calculate_current_streak(records),
    }), 200

@app.route("/habits/<int:habit_id>/streak", methods=["GET"])
def get_streak(habit_id):
    """
    Retorna o streak atual e o recorde de um hábito.
    ---
    tags:
      - Registros
    parameters:
      - in: path
        name: habit_id
        type: integer
        required: true
    responses:
      200:
        description: Streak calculado com sucesso
      404:
        description: Hábito não encontrado
    """
    conn = get_connection()
    habit = conn.execute("SELECT id, name FROM habits WHERE id = ?", (habit_id,)).fetchone()
    if habit is None:
        conn.close()
        return jsonify({"error": "Hábito não encontrado."}), 404

    records = conn.execute(
        "SELECT date, completed FROM records WHERE habit_id = ?", (habit_id,)
    ).fetchall()
    conn.close()

    return jsonify({
        "habit_id": habit_id,
        "name": habit["name"],
        "current_streak": calculate_current_streak(records),
        "record": calculate_record(records),
    }), 200

@app.route("/habits/<int:habit_id>/history", methods=["GET"])
def get_history(habit_id):
    """
    Retorna o calendário de um mês específico para um hábito, indicando quais
    dias foram concluídos. Permite navegar entre meses/anos via query params.
    ---
    tags:
      - Registros
    parameters:
      - in: path
        name: habit_id
        type: integer
        required: true
      - in: query
        name: year
        type: integer
        required: false
        description: "Ano do calendário (ex: 2026). Padrão: ano atual."
      - in: query
        name: month
        type: integer
        required: false
        description: "Mês do calendário, de 1 a 12. Padrão: mês atual."
    responses:
      200:
        description: Calendário do mês com status de conclusão de cada dia
      400:
        description: Parâmetros 'year' ou 'month' inválidos
      404:
        description: Hábito não encontrado
    """
    conn = get_connection()
    habit = conn.execute("SELECT id FROM habits WHERE id = ?", (habit_id,)).fetchone()
    if habit is None:
        conn.close()
        return jsonify({"error": "Hábito não encontrado."}), 404

    today = date.today()

    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
        if month < 1 or month > 12 or year < 2000 or year > 2100:
            raise ValueError
    except ValueError:
        conn.close()
        return jsonify({"error": "Parâmetros 'year' ou 'month' inválidos."}), 400

    records = conn.execute(
        "SELECT date, completed FROM records WHERE habit_id = ?", (habit_id,)
    ).fetchall()
    conn.close()

    completed_map = {r["date"]: bool(r["completed"]) for r in records}

    _, days_in_month = calendar_module.monthrange(year, month)

    days = []
    for day_number in range(1, days_in_month + 1):
        day_obj = date(year, month, day_number)
        key = day_obj.isoformat()
        weekday = (day_obj.weekday() + 1) % 7
        days.append({
            "day": day_number,
            "date": key,
            "weekday": weekday,
            "completed": completed_map.get(key, False),
            "future": day_obj > today,
            "today": day_obj == today,
        })

    next_month = (year, month + 1) if month < 12 else (year + 1, 1)
    prev_month = (year, month - 1) if month > 1 else (year - 1, 12)

    return jsonify({
        "habit_id": habit_id,
        "year": year,
        "month": month,
        "month_name": f"{MONTH_NAMES[month]} de {year}",
        "days": days,
        "previous_month": {"year": prev_month[0], "month": prev_month[1]},
        "next_month": {"year": next_month[0], "month": next_month[1]},
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
