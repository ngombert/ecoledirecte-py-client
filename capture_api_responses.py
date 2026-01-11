#!/usr/bin/env python3
"""
Script pour capturer les réponses de tous les endpoints de l'API EcoleDirecte.
Ce script appelle chaque endpoint et sauvegarde la réponse JSON brute dans un fichier.
Ces fichiers JSON seront utilisés pour créer les modèles Pydantic v2.

Usage:
    uv run --env-file .env_student capture_api_responses.py
    # OU
    uv run --env-file .env_family capture_api_responses.py
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Ensure src is in python path for local testing without install
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from ecoledirecte_py_client import (
    Client,
    LoginError,
    ApiError,
    MFARequiredError,
    Family,
    Student,
)

QCM_FILE = "qcm.json"
OUTPUT_DIR = Path("api_responses")


def load_qcm():
    """Charge les réponses MFA sauvegardées."""
    if os.path.exists(QCM_FILE):
        try:
            with open(QCM_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_qcm(question, answer):
    """Sauvegarde une nouvelle réponse MFA."""
    data = load_qcm()
    if question not in data:
        data[question] = []
    if answer not in data[question]:
        data[question].append(answer)
    with open(QCM_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_response(endpoint_name: str, response_data: dict, student_id: int = None):
    """
    Sauvegarde une réponse API dans un fichier JSON.

    Args:
        endpoint_name: Nom de l'endpoint (ex: 'grades', 'homework')
        response_data: Les données de la réponse
        student_id: ID de l'élève (optionnel, pour différencier les réponses)
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Créer un nom de fichier unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if student_id:
        filename = f"{endpoint_name}_student_{student_id}_{timestamp}.json"
    else:
        filename = f"{endpoint_name}_{timestamp}.json"

    filepath = OUTPUT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Réponse sauvegardée: {filepath}")
    return filepath


async def capture_student_data(student: Student):
    """
    Capture toutes les données pour un élève donné.

    Args:
        student: Instance Student
    """
    student_name = getattr(student, "name", f"Student {student.id}")
    print(f"\n{'=' * 60}")
    print(f"Capture des données pour: {student_name} (ID: {student.id})")
    print(f"{'=' * 60}")

    # 1. GRADES - Notes (tous les trimestres)
    print("\n[1/5] Récupération des notes...")
    try:
        grades_all = await student.get_grades()
        save_response("grades_all", grades_all, student.id)

        # Aussi capturer par trimestre si disponible (1-4)
        for quarter in range(1, 5):
            try:
                grades_quarter = await student.get_grades(quarter=quarter)
                if grades_quarter:  # Si le trimestre existe
                    save_response(
                        f"grades_quarter_{quarter}", grades_quarter, student.id
                    )
            except Exception as e:
                print(f"  ⚠ Trimestre {quarter} non disponible: {e}")
    except Exception as e:
        print(f"  ✗ Erreur lors de la récupération des notes: {e}")

    # 2. HOMEWORK - Cahier de texte
    print("\n[2/5] Récupération du cahier de texte...")
    try:
        homework = await student.get_homework()
        save_response("homework", homework, student.id)
    except Exception as e:
        print(f"  ✗ Erreur lors de la récupération du cahier de texte: {e}")

    # 3. SCHEDULE - Emploi du temps
    print("\n[3/5] Récupération de l'emploi du temps...")
    try:
        # Récupérer l'emploi du temps de la semaine en cours
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Lundi
        end_of_week = start_of_week + timedelta(days=6)  # Dimanche

        start_date = start_of_week.strftime("%Y-%m-%d")
        end_date = end_of_week.strftime("%Y-%m-%d")

        print(f"  Période: {start_date} à {end_date}")
        schedule = await student.get_schedule(start_date, end_date)
        save_response("schedule", schedule, student.id)

        # Aussi capturer une semaine future pour avoir plus d'exemples
        next_week_start = start_of_week + timedelta(days=7)
        next_week_end = next_week_start + timedelta(days=6)
        schedule_next = await student.get_schedule(
            next_week_start.strftime("%Y-%m-%d"), next_week_end.strftime("%Y-%m-%d")
        )
        save_response("schedule_next_week", schedule_next, student.id)

    except Exception as e:
        print(f"  ✗ Erreur lors de la récupération de l'emploi du temps: {e}")

    # 4. MESSAGES - Messagerie
    print("\n[4/5] Récupération des messages...")
    try:
        messages = await student.get_messages()
        save_response("messages", messages, student.id)
    except Exception as e:
        print(f"  ✗ Erreur lors de la récupération des messages: {e}")

    # 5. TIMELINE / VIE SCOLAIRE (si disponible)
    print("\n[5/5] Recherche d'autres endpoints disponibles...")
    # Note: Ajouter d'autres endpoints ici si découverts dans le code
    # Par exemple: absences, sanctions, vie scolaire, etc.

    print(f"\n{'=' * 60}")
    print(f"Capture terminée pour {student_name}")
    print(f"{'=' * 60}")


async def capture_family_data(family: Family):
    """
    Capture les données pour un compte famille.

    Args:
        family: Instance Family
    """
    print(f"\n{'=' * 60}")
    print(f"Compte Famille détecté - {len(family.students)} élève(s)")
    print(f"{'=' * 60}")

    # Sauvegarder les données brutes du compte famille
    save_response("family_account", family.data)

    # Capturer les données pour chaque élève
    for student in family.students:
        await capture_student_data(student)


async def login_with_mfa(client: Client, username: str, password: str):
    """
    Gère la connexion avec support MFA automatique et interactif.

    Returns:
        Session (Student ou Family)
    """
    try:
        print(f"Connexion en cours pour {username}...")
        session = await client.login(username, password)
        print(f"✓ Connexion réussie! Type de session: {type(session).__name__}")
        return session

    except MFARequiredError as e:
        print("\n--- MFA REQUIS ---")
        print(f"Question: {e.question}")

        known_answers = load_qcm().get(e.question, [])

        # Tentative automatique avec réponse sauvegardée
        if known_answers:
            print(f"Réponses connues: {known_answers}")
            potential_answer = known_answers[-1]
            print(f"Tentative automatique avec: {potential_answer}")

            try:
                session = await client.submit_mfa(potential_answer)
                print("✓ MFA validé automatiquement!")
                return session
            except Exception as auto_err:
                print(f"✗ Échec de la soumission automatique: {auto_err}")
                print("Passage en mode interactif...")

        # Mode interactif
        if e.propositions:
            print("\nPropositions disponibles:")
            for idx, p in enumerate(e.propositions):
                print(f"  {idx}: {p}")

        while True:
            choice = input("\nEntrez votre choix (numéro ou texte complet): ")

            answer = choice
            if choice.isdigit() and int(choice) < len(e.propositions):
                answer = e.propositions[int(choice)]
                print(f"Sélectionné: {answer}")

            try:
                session = await client.submit_mfa(answer)
                print("✓ MFA validé!")
                save_qcm(e.question, answer)
                print("Réponse sauvegardée dans qcm.json")
                return session

            except Exception as mfa_err:
                print(f"✗ Échec MFA: {mfa_err}")
                print("Veuillez réessayer.")


async def main():
    """Point d'entrée principal du script."""
    print("=" * 60)
    print("CAPTURE DES RÉPONSES API - EcoleDirecte")
    print("=" * 60)

    username = os.environ.get("ECOLEDIRECTE_USER")
    password = os.environ.get("ECOLEDIRECTE_PASSWORD")

    if not username or not password:
        print("\n✗ ERREUR: Variables d'environnement manquantes!")
        print("Définissez ECOLEDIRECTE_USER et ECOLEDIRECTE_PASSWORD")
        print("\nExemple:")
        print("  export ECOLEDIRECTE_USER='votre_identifiant'")
        print("  export ECOLEDIRECTE_PASSWORD='votre_mot_de_passe'")
        print("\nOu utilisez un fichier .env:")
        print("  uv run --env-file .env_student capture_api_responses.py")
        return 1

    client = Client()

    try:
        # Connexion avec gestion MFA
        session = await login_with_mfa(client, username, password)

        # Capturer les données selon le type de compte
        if isinstance(session, Family):
            await capture_family_data(session)
        elif isinstance(session, Student):
            await capture_student_data(session)
        else:
            print(f"✗ Type de session inconnu: {type(session)}")
            return 1

        print("\n" + "=" * 60)
        print("✓ CAPTURE TERMINÉE AVEC SUCCÈS!")
        print(f"✓ Fichiers sauvegardés dans: {OUTPUT_DIR.absolute()}")
        print("=" * 60)

        # Afficher la liste des fichiers créés
        files = sorted(OUTPUT_DIR.glob("*.json"))
        if files:
            print(f"\nFichiers créés ({len(files)}):")
            for f in files:
                size_kb = f.stat().st_size / 1024
                print(f"  - {f.name} ({size_kb:.1f} KB)")

        return 0

    except LoginError as e:
        print(f"\n✗ Erreur de connexion: {e}")
        return 1
    except ApiError as e:
        print(f"\n✗ Erreur API: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Erreur inattendue: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await client.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
