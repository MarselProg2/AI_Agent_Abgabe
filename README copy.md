# 🚀 InsightBench: Social Media Analyse & Erstellungs-Architektur (Final)

Basierend auf "INSIGHTBENCH: EVALUATING BUSINESS ANALYTICS AGENTS THROUGH MULTI-STEP INSIGHT GENERATION".

## 1. Projektübersicht

Ein Multi-Agenten-System, das darauf ausgelegt ist, Social-Media-Inhalte zu optimieren, indem tiefe Einblicke (Insights) anstatt nur oberflächlicher Daten generiert werden. Das System nutzt eine Pipeline von **Deskriptiver**, **Diagnostischer**, **Prädiktiver** und **Präskriptiver** Analytik.

## 2. Die "InsightBench" Agenten-Pipeline

### Schritt 1: Video Analyst Agent (Der Beobachter)

- **Modell**: `gemini-2.0-flash`
- **Rolle**: Extraktion der Datenstruktur (Schema).
- **Kernaufgabe**: Erfasst nicht nur visuelle Eindrücke, sondern extrahiert statistische Eckpunkte: Einzigartige visuelle Elemente, Szenenlängen und die Verteilung der ersten 3 Sekunden (Hook).
- **Output**: Formulierung von **3 Root Questions** (Kernfragen), die speziell auf die Retentions-Logik abzielen.

### Schritt 2: Insight Extractor Agent (Der Analyst)

- **Modell**: `gemini-2.0-flash`
- **Rolle**: Durchführung einer **Multi-Step-Analyse** zur Vermeidung oberflächlicher Ergebnisse.
- **Mechanismus (Drill-Down)**: Zu jeder beantworteten Root Question generiert dieser Agent automatisch **n Follow-up Fragen**, um tieferliegende Muster zu finden. **Hinweis:** Dieser Agent arbeitet jetzt rein basierend auf der Video-Analyse, ohne externe Trend-Daten (TrendScout entfernt).
- **Analyse-Level**:
  - _Deskriptiv_: Was passiert im Video?
  - _Diagnostisch_: Warum funktioniert der Hook?
  - _Prädiktiv_: Was wird passieren (Viralität)?
  - _Präskriptiv_: Welche konkreten Handlungsempfehlungen gibt es?

### Schritt 3: Creator Agent (Der Künstler)

- **Modell**: `gemini-2.5-pro` (Maximale kreative Tiefe)
- **Rolle**: Synthetisierung der **Präskriptiven Insights** in Captions und Hashtags.
- **Anforderung**: Übersetzung der strategischen Winkel in emotionalen Content, der genau auf den identifizierten Insight eingeht.

### Schritt 4: Evaluator Agent (Der numerische Richter)

- **Modell**: `gemini-1.5-flash` + **Google Search**
- **Rolle**: Qualitätssicherung durch das **LLaMA-3-Eval Protokoll**.
- **Numerisches Rating (Anti-Halluzination)**: Der Agent vergibt ein **Rating von 1-10** basierend auf der Nähe des Entwurfs zum Video-Inhalt (Ground Truth).
  - **10**: Faktisch perfekt und trend-aktuell.
  - **< 7**: Signal zur Überarbeitung (Loop), falls Halluzinationen oder Abweichungen erkannt werden.
- **Validierung**: Nutzung von Google Search zur Verifizierung von Fakten und Trend-Aktualität.

## 3. Erfolgskennzahlen (S.M.A.R.T.)

1.  **Insight-Tiefe**: Mindestens 1 valider Punkt pro Analyse-Kategorie.
2.  **Präzision**: LLaMA-3-Eval Score von durchschnittlich > 8.0 für freigegebene Posts.
3.  **Effizienz**: Abschluss der Analysezyklen ohne unnötiges Overengineering durch stabilisierte Prompts (Temperatur 0.0).

---

