# Module RACI Matrix

# Zielpublikum
- Fachorganisation - {{dataSteward.label}}
- IT-nahe Organisationen - {{dataCustodian.label}}

---

# Einsatzscope
{{dataGovernance.description}}. Die erweiterten Module werden insbesondere benötigt bei
- IT-Betrieb und Planung
- komplexeren IT- oder Datenprojekte

---

# 1. RACI-Matrix - erweitertes Modell (mit Modulen)

## Legende
- R (Responsible) = führt aus
- A (Accountable) = trägt Gesamtverantwortung
- C (Consulted) = wird einbezogen
- I (Informed) = wird informiert

## 1.1 Governance & Strategie

| Aktivität | {{dataOwner.alias_de}} | {{dataSteward.alias_de}} | {{dataCustodian.alias_de}} | {{gdg.alias_de}} |
|---|---|---|---|---|
| Datenstrategie definieren | A | I | I | R |
| Data Governance Policies verabschieden | A | I | I | R |
| Priorisierung Dateninitiativen | A | R | I | C |
| Kritische Daten definieren |  A | R | I | C |


## 1.2 Datennutzung & Zugriff
| Aktivität | {{dataOwner.alias_de}} | {{dataSteward.alias_de}} | {{dataCustodian.alias_de}} | {{complianceOfficer.label}}
|---|---|---|---|---|
| Zugriff auf Daten genehmigen | A | C | R | C |
| OGD-Freigabe | A | R | I | C |
| Datennutzung definieren | A | R | I | C |

## 1.3 Architektur & IT-Betrieb
| Aktivität | {{dataOwner.alias_de}} | {{dataSteward.alias_de}} | {{dataCustodian.alias_de}} | {{applicationOwner.label}} | {{dataArchitect.label}} |
|---|---|---|---|---|---|
| Datenmodell definieren | I | C | C | R | A/R |
| Datenintegration umsetzen | I | C | R | R | A |
| Betrieb sicherstellen | I | I | A/R | C | I |
| Backup & Recovery | I | I | A/R | C | I |

## 1.4 Compliance & Sicherheit
| Aktivität | {{dataOwner.alias_de}} | {{dataCustodian.alias_de}} | {{informationSecurityOfficer.label}} | {{complianceOfficer.label}} |
|---|---|---|---|---|
| Schutzbedarf festlegen | A | C | R | C |
| Sicherheitsmassnahmen umsetzen | I | R | A | C |
| Datenschutz-Compliance prüfen |  A | C | C | R |
| Incident Management | I | R | A | C |



