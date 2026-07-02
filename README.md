# Streaks API

API REST para gerenciamento de hábitos com cálculo de streak.  
Desenvolvida em Flask com SQLite e documentação Swagger.

## Instalação

```bash
git clone https://github.com/matheus-rmds/streaks-backend
cd streaks-backend
python -m venv venv
#Linux/Mac:
source venv/bin/activate
#Windows:
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Acesse a documentação em http://localhost:5000/apidocs.

## Banco de dados
Criado automaticamente na primeira execução (streaks.db), contendo três tabelas:
- `users` -	id, name, email, created_at
- `habits` -	id, user_id, name, frequency_goal, created_at
- `records` -	id, habit_id, date, completed

## Rotas Principais
| Método | Rota                          | Descrição                          |
|--------|-------------------------------|------------------------------------|
| POST   | `/register`                   | Cadastra um novo usuário           |
| POST   | `/login`                      | Identifica usuário por email       |
| POST   | `/habits`                     | Cria um novo hábito                |
| GET    | `/habits/user/<user_id>`      | Lista hábitos com streak atual     |
| PUT    | `/habits/<habit_id>`          | Edita nome e meta do hábito        |
| DELETE | `/habits/<habit_id>`          | Remove hábito e registros          |
| POST   | `/records`                    | Marca/desmarca um dia              |
| GET    | `/habits/<habit_id>/streak`   | Retorna streak atual e recorde     |
| GET    | `/habits/<habit_id>/history`  | Calendário mensal com status       |
