#!/bin/bash

# Années à traiter
YEARS=(2022 2023 2024)

echo "--- Lancement du Processus de Collecte de Données Robuste ---"

# Boucle sur chaque année
for YEAR in "${YEARS[@]}"
do
    echo "--- Début du traitement pour l'année $YEAR ---"
    
    # On utilise un petit script python pour lister les courses de l'année
    # Cela évite de charger le calendrier dans la boucle shell
    RACES=$(python -c "import fastf1 as ff1; ff1.Cache.enable_cache('f1_cache'); schedule = ff1.get_event_schedule($YEAR); [print(f'\"{name}\"') for name in schedule[schedule['EventFormat'] != 'testing']['EventName']]")
    
    # Boucle sur chaque nom de course
    while IFS= read -r RACE_NAME; do
        # Retirer les guillemets
        RACE_NAME_CLEAN=$(echo "$RACE_NAME" | tr -d '"')
        
        # Appeler notre script "ouvrier" pour cette course spécifique
        python process_one_race.py "$YEAR" "$RACE_NAME_CLEAN"
        
        # Pause respectueuse entre chaque course
        SLEEP_TIME=$((RANDOM % 5 + 2))
        echo ">>> Pause de $SLEEP_TIME secondes avant la prochaine course..."
        sleep $SLEEP_TIME
        
    done <<< "$RACES"
done

echo "--- Processus de Collecte Terminé ---"
