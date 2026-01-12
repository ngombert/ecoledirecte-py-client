# Script de Capture des Réponses API

Ce script capture et sauvegarde les réponses JSON de tous les endpoints de l'API EcoleDirecte pour faciliter la migration vers Pydantic v2.

## Endpoints Capturés

### Pour les comptes Student/Family:
- **Grades** (`grades_all`, `grades_quarter_N`) - Notes par trimestre
- **Homework** (`homework`) - Cahier de texte
- **Schedule** (`schedule`) - Emploi du temps (semaine en cours + suivante)
- **Messages** (`messages`) - Messagerie

### Pour les comptes Family:
- **Family Account** (`family_account`) - Données du compte famille
- Données de chaque élève associé

## Utilisation

### 1. Avec un compte étudiant:
```bash
uv run --env-file .env_student capture_api_responses.py
```

### 2. Avec un compte famille:
```bash
uv run --env-file .env_family capture_api_responses.py
```

### 3. Avec variables d'environnement:
```bash
export ECOLEDIRECTE_USER="votre_identifiant"
export ECOLEDIRECTE_PASSWORD="votre_mot_de_passe"
uv run capture_api_responses.py
```

## Sortie

Tous les fichiers JSON sont sauvegardés dans le dossier `api_responses/` avec le format:
```
api_responses/
├── grades_all_student_12345_20260111_151430.json
├── grades_quarter_1_student_12345_20260111_151431.json
├── homework_student_12345_20260111_151432.json
├── schedule_student_12345_20260111_151433.json
├── messages_student_12345_20260111_151434.json
└── family_account_20260111_151429.json
```

## Gestion MFA

Le script gère automatiquement le MFA (Multi-Factor Authentication):
- Utilise les réponses sauvegardées dans `qcm.json` si disponibles
- Passe en mode interactif si nécessaire
- Sauvegarde les nouvelles réponses correctes pour utilisation future

## Prochaines Étapes

Une fois les réponses capturées, utilisez-les pour:
1. Analyser la structure des données
2. Créer les modèles Pydantic v2 correspondants
3. Définir les types appropriés (datetime, enums, etc.)
4. Ajouter les propriétés calculées (@property)
5. Implémenter les validateurs (model_validator)

## Exemple de Réponses Attendues

### Grades (Notes)
```json
{
  "notes": [...],
  "periodes": [
    {
      "idPeriode": "A001",
      "periode": "Trimestre 1",
      "dateDebut": "2024-09-01",
      "dateFin": "2024-12-15",
      "notes": [...]
    }
  ]
}
```

### Homework (Cahier de texte)
```json
{
  "data": {
    "dates": [
      {
        "date": "2024-01-11",
        "matiere": "Mathématiques",
        "aFaire": {...}
      }
    ]
  }
}
```
