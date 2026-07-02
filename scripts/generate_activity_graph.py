#!/usr/bin/env python3
"""
Gera um gráfico de contribuições customizado (SVG) para o README do GitHub,
pintando de vermelho os dias em que houve contribuição em fim de semana
(sábado ou domingo).

Variáveis de ambiente:
  GH_TOKEN     - token com permissão de leitura (obrigatório)
  GH_USERNAME  - usuário do GitHub (default: thyagohyvo)
  DAYS         - quantos dias mostrar no gráfico (default: 31)
  OUTPUT_PATH  - caminho do SVG gerado (default: assets/activity-graph.svg)
"""

import os
import sys
import datetime
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

GH_TOKEN = os.environ.get("GH_TOKEN")
USERNAME = os.environ.get("GH_USERNAME", "thyagohyvo")
DAYS = int(os.environ.get("DAYS", "31"))
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "assets/activity-graph.svg")

if not GH_TOKEN:
    print("ERRO: defina a variável de ambiente GH_TOKEN", file=sys.stderr)
    sys.exit(1)

today = datetime.date.today()
start_date = today - datetime.timedelta(days=DAYS - 1)
from_iso = f"{start_date.isoformat()}T00:00:00Z"
to_iso = f"{today.isoformat()}T23:59:59Z"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": QUERY, "variables": {"login": USERNAME, "from": from_iso, "to": to_iso}},
    headers={"Authorization": f"Bearer {GH_TOKEN}"},
    timeout=30,
)
resp.raise_for_status()
data = resp.json()
if "errors" in data:
    raise RuntimeError(data["errors"])

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

dates, ys, colors = [], [], []
for week in weeks:
    for day in week["contributionDays"]:
        d = datetime.datetime.strptime(day["date"], "%Y-%m-%d")
        dates.append(d)
        ys.append(day["contributionCount"])
        is_weekend = d.weekday() >= 5  # 5=sábado, 6=domingo
        colors.append("#ff4d4d" if is_weekend else "#4ade80")

fig, ax = plt.subplots(figsize=(9, 3.2), dpi=150)
fig.patch.set_alpha(0)
ax.set_facecolor("none")

ax.plot(dates, ys, color="#4ade80", linewidth=1.5, zorder=1)
ax.fill_between(dates, ys, color="#4ade80", alpha=0.12, zorder=0)
ax.scatter(dates, ys, c=colors, s=28, zorder=2, edgecolors="none")

ax.set_title(f"{USERNAME}'s Contribution Graph (vermelho = fim de semana)",
             color="#60a5fa", fontsize=10)
ax.set_ylabel("Contributions", color="#e6edf3", fontsize=8)
ax.tick_params(colors="#8b949e", labelsize=7)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
for spine in ax.spines.values():
    spine.set_color("#30363d")
ax.grid(True, color="#30363d", linewidth=0.4, alpha=0.5)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_PATH, transparent=True)
print(f"SVG gerado em {OUTPUT_PATH}")
