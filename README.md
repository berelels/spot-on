# Spot On! ⚽

> **Probabilidades baseadas em dados, não em palpites.**

Spot On! é um sistema web de previsão de resultados de futebol que usa estatística séria para calcular quão provável é cada desfecho de uma partida.

---

## Como funciona

### Modelo de Poisson

O futebol pode ser modelado como um processo de Poisson: cada time marca gols de forma aproximadamente aleatória, com uma taxa média que depende de seu histórico de ataque e defesa. O modelo calcula:

- **λ_mandante** — gols esperados do time da casa
- **λ_visitante** — gols esperados do time de fora

A partir dessas duas médias, constrói-se uma **matriz 9×9** de probabilidades para todos os placares de 0-0 até 8-8. A soma das células acima da diagonal = vitória do visitante, na diagonal = empate, abaixo = vitória do mandante.

### Correção Dixon-Coles

O Poisson puro subestima placares de 0-0 e 1-1 e superestima outros resultados baixos. A correção Dixon-Coles (1997) aplica fatores tau a esses quatro placares críticos, usando um parâmetro de correlação **ρ = −0.13** (valor empírico da literatura):

| Placar | Fator tau        |
|--------|------------------|
| 0–0    | 1 − λh·λa·ρ      |
| 1–0    | 1 + λa·ρ         |
| 0–1    | 1 + λh·ρ         |
| 1–1    | 1 − ρ            |

Após a correção, a matriz é renormalizada para somar 1.

---

## Obter chave da API (gratuita)

1. Acesse [football-data.org](https://www.football-data.org/)
2. Clique em **Register** e crie uma conta gratuita
3. Copie sua chave de API no painel do usuário
4. Cole no arquivo `backend/.env`:
   ```
   FOOTBALL_DATA_API_KEY=sua_chave_aqui
   ```

> **Sem chave?** O sistema funciona com dados de demonstração integrados — ideal para conhecer a interface antes de configurar a API.

---

## Como rodar

> **Pré-requisito:** Python 3.10 ou superior instalado ([python.org](https://python.org)).

### Linux / macOS

```bash
chmod +x run.sh
./run.sh
```

### Windows

Dê um duplo clique em `run.bat` ou execute no Prompt de Comando:

```bat
run.bat
```

> **Windows:** certifique-se de que `python` está no PATH do sistema. Durante a instalação do Python, marque a opção **"Add Python to PATH"**.

### 2. Abrir o frontend

Abra o arquivo `frontend/index.html` diretamente no navegador (não precisa de servidor web).

### 3. Usar

1. Selecione uma liga (ex.: Premier League)
2. Escolha o time mandante e o visitante
3. Clique em **Analisar**
4. Veja as probabilidades e os 10 placares mais prováveis em segundos

---

## Exemplo de resultado

```
Manchester City  vs  Manchester United
Premier League

  Vitória      Empate     Derrota
  Man. City              Man. Utd
   52.3%        24.1%      23.6%

Gols esperados: Man. City 1.84 · Man. Utd 0.97

Placares mais prováveis:
  2-1  11.2%  |  1-0  9.8%  |  2-0  9.1%  |  1-1  8.7%  |  3-1  6.7%
  2-2   4.8%  |  0-0  4.4%  |  3-0  4.2%  |  0-1  3.8%  |  1-2  3.3%

Baseado em 38 partidas · Confiança: Alta
```

---

## Ligas suportadas

| ID    | Liga                    | País      |
|-------|-------------------------|-----------|
| `PL`  | Premier League          | Inglaterra|
| `BL1` | Bundesliga              | Alemanha  |
| `SA`  | Serie A                 | Itália    |
| `PD`  | La Liga                 | Espanha   |
| `FL1` | Ligue 1                 | França    |
| `BSB` | Brasileirão Série A     | Brasil    |

---

## Limitações conhecidas

- **Rate limit**: A API gratuita do football-data.org permite **10 requisições por minuto**. Se você fizer muitas análises rapidamente, aguarde antes de tentar novamente.
- **Histórico**: O modelo usa até **38 partidas** recentes de cada time na liga selecionada. Times recém-promovidos ou com poucas partidas receberão nível de **confiança baixa**.
- **Ligas**: Apenas as 6 ligas listadas acima são suportadas no plano gratuito da API.
- **Sem dados em tempo real**: Os resultados não consideram fatores como lesões, escalações ou condições climáticas — apenas o histórico estatístico.
- **Cache**: Dados de times são cacheados por 24h e partidas por 6h para respeitar o rate limit.

---

## Estrutura do projeto

```
spot-on/
├── backend/
│   ├── main.py          # FastAPI: endpoints /api/leagues, /api/teams, /api/predict
│   ├── model.py         # Poisson + Dixon-Coles
│   ├── data_service.py  # football-data.org + cache SQLite
│   ├── requirements.txt
│   └── .env.example     # Modelo de configuração (copiar para .env)
├── frontend/
│   ├── index.html       # SPA com 3 estados: seleção, carregando, resultado
│   ├── style.css        # Tema escuro, animações, layout responsivo
│   └── app.js           # Lógica JS completa
├── run.sh               # Script de inicialização (Linux/macOS)
├── run.bat              # Script de inicialização (Windows)
└── README.md
```

---

*Spot On! — Uso educacional e estatístico. Não use para apostas.*
