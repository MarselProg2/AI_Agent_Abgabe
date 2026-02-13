# SMART-Ziele zur Evaluierung der InsightBench-Agenten

Dieses Dokument definiert spezifische, messbare, erreichbare, relevante und zeitgebundene (SMART) Ziele, um die Leistung der einzelnen KI-Agenten im System objektiv zu bewerten.

---

## 1. Video Analyst Agent (Wahrnehmung & Schema-Extraktion)
**Ziel:** Präzise Extraktion visueller Daten als Basis für die weitere Verarbeitung.

| Kriterium | Beschreibung |
| :--- | :--- |
| **S (Spezifisch)** | Der Agent soll visuelle Schlüsselelemente (`hook_type`, `scene_length`, `unique_visual_elements`) korrekt identifizieren und klassifizieren. |
| **M (Messbar)** | **Genauigkeit > 90%** im Vergleich zu manuell annotierten Ground-Truth-Daten (Test-Set von 50 Videos). <br> **Schema-Validität:** 100% valide JSON-Struktur gemäß `VideoAnalysisSchema`. |
| **A (Erreichbar)** | Durch Nutzung von Gemini 2.0 Flash Vision und striktem Pydantic-Output-Schema. |
| **R (Relevant)** | Fehlerhafte Eingangsdaten führen zu fehlerhaften Strategien in nachgelagerten Agenten (Garbage In, Garbage Out). |
| **T (Zeitgebunden)** | Die Analyse muss im Durchschnitt **unter 5 Sekunden** pro Video abgeschlossen sein. |

---

## 2. Insight Extractor Agent (Logik & Strategie)
**Ziel:** Ableitung tiefergehender, logisch konsistenter Strategien aus Rohdaten.

| Kriterium | Beschreibung |
| :--- | :--- |
| **S (Spezifisch)** | Der Agent muss für jede `Root Question` eine 4-Ebenen-Analyse (Descriptive, Diagnostic, Predictive, Prescriptive) durchführen, die in sich schlüssig ist. |
| **M (Messbar)** | **Logische Konsistenz:** < 5% Widersprüche zwischen `Descriptive` und `Prescriptive` Ebene (manuelle Stichprobe). <br> **Vollständigkeit:** 100% der `Root Questions` müssen vollständig analysiert sein (keine leeren Felder). |
| **A (Erreichbar)** | Durch Multi-Step-Reasoning Prompts und strukturierte `AnalysisLevels`-Modelle. |
| **R (Relevant)** | Kritisch für die Qualität der Content-Strategie; oberflächliche Analyse führt zu generischem Content. |
| **T (Zeitgebunden)** | Die Synthese aller Insights muss **unter 10 Sekunden** erfolgen. |

---

## 3. Creator Agent (Kreativität & Trend-Alignment)
**Ziel:** Generierung von viralem, plattformgerechtem Content.

| Kriterium | Beschreibung |
| :--- | :--- |
| **S (Spezifisch)** | Erstellung von Captions und Hashtags, die aktuelle Trends aufgreifen und die strategischen Vorgaben umsetzen. |
| **M (Messbar)** | **Erfolgsquote:** > 80% der Generierungen erreichen im ersten Durchlauf einen Evaluator-Score von **≥ 7/10**. <br> **Trend-Validität:** 100% der genutzten Trends sind laut Google Search aktuell (< 30 Tage). |
| **A (Erreichbar)** | Durch Zugriff auf Google Search Tools und Feedback-Schleifen. |
| **R (Relevant)** | Maximiert das potenzielle User-Engagement (Likes, Shares) und die Sichtbarkeit. |
| **T (Zeitgebunden)** | Generierung inkl. Trend-Recherche **unter 8 Sekunden**. |

---

## 4. Evaluator Agent (Qualitätssicherung & Sicherheit)
**Ziel:** Zuverlässige Erkennung von Fehlern und Halluzinationen.

| Kriterium | Beschreibung |
| :--- | :--- |
| **S (Spezifisch)** | Der Agent soll kritisch prüfen, ob der generierte Content Fakten enthält, die nicht im Video vorkamen (Halluzinationen), und ob Trends aktuell sind. |
| **M (Messbar)** | **Recall (Sensitivität):** 100% Erkennung von absichtlich eingefügten Halluzinationen in einem Test-Set. <br> **Precision:** < 10% False Positives (fälschliches Ablehnen von gutem Content). |
| **A (Erreichbar)** | Durch Wort-für-Wort-Abgleich mit der `Video Analysis` und `google_search` Verifizierung. |
| **R (Relevant)** | Schützt die Markenreputation und verhindert die Verbreitung von Fehlinformationen. |
| **T (Zeitgebunden)** | Vollständige Evaluation **unter 5 Sekunden**. |

---

## 5. Gesamtsystem (End-to-End Performance)
**Ziel:** Effiziente Orchestrierung und stabile Ausführung.

| Kriterium | Beschreibung |
| :--- | :--- |
| **S (Spezifisch)** | Der gesamte Pipeline-Durchlauf vom Video-Input zum finalen, approvten Content. |
| **M (Messbar)** | **Durchlaufzeit:** < 30 Sekunden für den gesamten Prozess (inkl. möglicher Retry-Loops). <br> **Robustheit:** < 1% Systemabstürze oder Timeout-Fehler bei 100 Testläufen. |
| **A (Erreichbar)** | Durch asynchrone Verarbeitung und effizientes Prompt-Engineering. |
| **R (Relevant)** | Sicherstellung der Skalierbarkeit für den produktiven Einsatz. |
| **T (Zeitgebunden)** | Erreichung dieser Metriken bis zum Datum der Abgabe. |
