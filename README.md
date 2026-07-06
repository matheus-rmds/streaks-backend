# Streaks API

API REST para o Streaks, um app de rastreamento de hábitos diários com cálculo automático de sequência de dias consecutivos.

## Tecnologias

- Python 3
- Flask
- SQLite
- Flasgger (Swagger / OpenAPI)
- Flask-CORS

## Estrutura

```
streaks-backend/
├── app.py
├── database.py
├── streak_logic.py
└── requirements.txt
```

## Modelo de dados

- **users**: id, name, email, created_at
- **habits**: id, user_id (FK), name, frequency_goal, created_at
- **records**: id, habit_id (FK), date, completed

## Instalação

```bash
git clone https://github.com/matheus-rmds/streaks-backend
cd streaks-backend
python -m venv venv
#Windows:
venv\Scripts\activate
#Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
A API sobe em `http://localhost:5000`.

## Documentação (Swagger)

```
http://localhost:5000/apidocs
```

## Rotas

| Rota | Método | Descrição |
|---|---|---|
| `/register` | POST | Cadastra um novo usuário |
| `/login` | POST | Identifica um usuário existente pelo email |
| `/habits` | POST | Cria um hábito vinculado a um usuário |
| `/habits/user/<user_id>` | GET | Lista os hábitos de um usuário, com streak atual |
| `/habits/<habit_id>` | PUT | Edita o nome de um hábito |
| `/habits/<habit_id>` | DELETE | Remove um hábito e seus registros |
| `/records` | POST | Marca/desmarca um hábito como concluído em uma data |
| `/habits/<habit_id>/streak` | GET | Retorna o streak atual e o recorde de um hábito |
| `/habits/<habit_id>/history` | GET | Retorna o calendário mensal de um hábito (aceita `?year=` e `?month=`) |

## Observação

A identificação de usuário (`/login`) é feita apenas por email, sem senha, cada requisição carrega os dados necessários para ser processada, sem depender de sessão no servidor.
