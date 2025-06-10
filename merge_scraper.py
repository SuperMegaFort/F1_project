import pandas as pd
import glob
import os
import re

def group_yearly_files(input_dir="f1_results_by_type_simple", output_dir="f1_summary_files"):
    """
    Regroupe tous les fichiers CSV annuels pour chaque type de donnée en un seul 
    fichier de synthèse par type.

    Par exemple:
    - f1_2020_race.csv, f1_2021_race.csv -> race_all_years.csv
    - f1_2020_pit_stop.csv, f1_2021_pit_stop.csv -> pit_stop_all_years.csv
    """
    print(f"Lancement du regroupement des fichiers du répertoire '{input_dir}'...")
    
    # S'assurer que le répertoire de sortie existe
    os.makedirs(output_dir, exist_ok=True)
    print(f"Les fichiers de synthèse seront sauvegardés dans '{output_dir}'.")

    # 1. Trouver tous les fichiers CSV dans le répertoire d'entrée
    all_files = glob.glob(os.path.join(input_dir, "f1_*.csv"))

    if not all_files:
        print("Aucun fichier CSV trouvé. Veuillez vérifier le répertoire d'entrée.")
        return

    # 2. Identifier tous les types de données uniques (race, qualifying, etc.)
    data_types = set()
    for f in all_files:
        filename = os.path.basename(f)
        match = re.search(r'f1_\d{4}_(.+)\.csv', filename)
        if match:
            data_types.add(match.group(1))

    print(f"\nTypes de données trouvés : {', '.join(sorted(list(data_types)))}")

    # 3. Traiter chaque type de donnée
    for data_type in sorted(list(data_types)):
        print("-" * 50)
        print(f"Traitement du type de donnée : '{data_type}'")

        # Trouver tous les fichiers correspondant à ce type de donnée pour toutes les années
        type_specific_files = glob.glob(os.path.join(input_dir, f"f1_*_{data_type}.csv"))
        
        if not type_specific_files:
            print("  - Aucun fichier trouvé pour ce type. Passage au suivant.")
            continue
            
        print(f"  - {len(type_specific_files)} fichier(s) trouvé(s) à regrouper.")

        # Liste pour stocker les DataFrames de chaque année
        list_of_dfs = []
        for f in sorted(type_specific_files):
            try:
                df = pd.read_csv(f)
                list_of_dfs.append(df)
            except pd.errors.EmptyDataError:
                print(f"    - Avertissement : Le fichier '{os.path.basename(f)}' est vide et a été ignoré.")
            except Exception as e:
                print(f"    - Erreur lors de la lecture de '{os.path.basename(f)}': {e}")
        
        if not list_of_dfs:
            print("  - Aucun DataFrame valide n'a pu être chargé. Passage au suivant.")
            continue

        # Concaténer tous les DataFrames en un seul
        combined_df = pd.concat(list_of_dfs, ignore_index=True)
        print(f"  - Toutes les années ont été combinées. Total de {len(combined_df)} lignes.")

        # Définir le nom du fichier de sortie
        output_filename = os.path.join(output_dir, f"{data_type}_all_years.csv")

        # Sauvegarder le DataFrame combiné
        try:
            combined_df.to_csv(output_filename, index=False, encoding='utf-8')
            print(f"  - Fichier de synthèse sauvegardé avec succès : '{output_filename}'")
        except Exception as e:
            print(f"  - Erreur lors de la sauvegarde du fichier '{output_filename}': {e}")
            
    print("-" * 50)
    print("\nRegroupement terminé.")

# --- Point d'entrée du script ---
if __name__ == "__main__":
    # Le répertoire où se trouvent vos fichiers CSV par année
    INPUT_DIRECTORY = "f1_results_by_type_simple"
    
    # Le répertoire où les nouveaux fichiers de synthèse seront créés
    OUTPUT_DIRECTORY = "f1_summary_files"
    
    group_yearly_files(input_dir=INPUT_DIRECTORY, output_dir=OUTPUT_DIRECTORY)

