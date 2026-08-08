# Mood Development Dashboard

A personal mood tracking system with a Discord bot for daily logging and a Streamlit dashboard for visualizing trends over time.

## How it works

Every night at 9pm PT, the **Mood-Checker** Discord bot sends a DM asking how your day went. Reply with how you felt and it logs the entry. You can also add a free-text note — the bot keeps the note prompt open for 24 hours so you can reply later.

The **Streamlit dashboard** pulls from the same database and visualizes your mood history across multiple views.

## Components

### Discord Bot (`discord_bot/`)
- Sends a daily DM prompt at 9pm PT
- Accepts mood input by name (e.g. "Good", "Tired", "Stressed") with synonym matching
- Optionally logs a free-text note per entry
- Persists all state to Supabase — survives restarts

### Dashboard (`pages/`)
| Page | Description |
|---|---|
| Overview | High-level summary stats |
| Monthly Trends | Score over time, month-by-month |
| Emotions | Breakdown by emotion category |
| Calendar | Day-by-day calendar heatmap with notes |

## Emotion Scale

| Emotion | Score |
|---|---|
| Happy | 11 |
| Productive | 10 |
| Good | 9 |
| Tired | 8 |
| Lazy | 7 |
| SAD | 6 |
| Stress/Anxiety | 5 |
| Angry/Annoyed | 4 |
| Depressed | 3 |
| Hopeless | 2 |
| Suicidal | 1 |

## Stack

- **Discord bot** — discord.py, hosted on Railway
- **Dashboard** — Streamlit, hosted on Railway
- **Database** — Supabase (Postgres)

## Setup

### Environment variables

```
DISCORD_BOT_TOKEN=
DISCORD_USER_ID=
SUPABASE_URL=
SUPABASE_KEY=
ANTHROPIC_API_KEY=
```

### Run locally

```bash
# Dashboard
streamlit run app.py

# Discord bot
cd discord_bot && python main.py
```
