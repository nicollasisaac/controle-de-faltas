sequenceDiagram
    actor Admin
    participant UI as "Front-end (React)"
    participant API as "NestJS API"
    participant DB as "PostgreSQL"
    participant WS as "WebSocket Gateway"

    %% 1. Admin marca AUSÊNCIA
    Admin->>UI: Marcar Ana AUSENTE
    UI->>API: POST /events/201/attendance\n{personId:101,status:"ABSENT"}
    API->>DB: UPSERT Attendance
    API->>DB: COUNT faltas de Ana

    alt 3 ≤ faltas < 5
        API->>DB: SET Person.warning = true
        API-->>WS: emit warning(personId=101)
    else faltas ≥ 5
        API->>DB: SET Person.suspended = true
        API-->>WS: emit suspended(personId=101)
    end

    API-->>UI: retorno presença + totalFaltas
    WS-->>UI: push warning/suspended

    %% 2. Painel de status
    Admin->>UI: Listar membros SSTM
    UI->>API: GET /groups/1/persons
    API->>DB: SELECT * FROM Person
    DB-->>API: lista
    API-->>UI: lista + status
    UI-->>Admin: Renderiza badges ⚠ ⛔

    %% 3. Guardas de rota
    Note over UI,API: Rotas só para\nrole = 'admin'
