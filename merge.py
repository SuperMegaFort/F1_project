import pandas as pd
import os
import re
from collections import defaultdict

def standardize_columns(df, filename):
    """
    Tente de trouver et de renommer les colonnes 'Driver' et 'GP'
    en utilisant une liste de noms alternatifs (alias).
    """
    standard_names = {
        'Driver': ['driver_name', 'Driver_Name', 'driver', 'Pilote'],
        # --- MODIFICATION CLÉ ---
        # Ajout de 'race_name' à la liste des alias pour la colonne 'GP'
        'GP': ['Grand_Prix', 'grand_prix', 'gp', 'Race', 'race_name']
    }

    rename_map = {}
    for standard, aliases in standard_names.items():
        if standard not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    rename_map[alias] = standard
                    print(f"INFO [{filename}]: Colonne '{alias}' renommée en '{standard}'.")
                    break
    
    df.rename(columns=rename_map, inplace=True)
    return df


def merge_all_f1_data(base_path):
    """
    Scanne, standardise, fusionne et combine toutes les données F1 d'un dossier.
    """
    try:
        files_by_year = defaultdict(dict)
        file_pattern = re.compile(r"f1_(\d{4})_([\w_]+)\.csv")

        print(f"Analyse du dossier : {base_path}\n")
        if not os.path.isdir(base_path):
            print(f"ERREUR : Le dossier '{base_path}' est introuvable.")
            return

        for filename in os.listdir(base_path):
            if match := file_pattern.match(filename):
                year, file_type = match.groups()
                files_by_year[year][file_type] = filename

        if not files_by_year:
            print("Aucun fichier CSV au format 'f1_YYYY_type.csv' n'a été trouvé.")
            return

        all_years_data = []
        sorted_years = sorted(files_by_year.keys())

        for year in sorted_years:
            print(f"--- Traitement de l'année {year} ---")
            year_files = files_by_year[year]
            
            if 'race' not in year_files:
                print(f"AVERTISSEMENT : Fichier 'f1_{year}_race.csv' manquant. Année {year} ignorée.")
                continue

            dataframes = {}
            for file_type, filename in year_files.items():
                path = os.path.join(base_path, filename)
                df = pd.read_csv(path)
                df = standardize_columns(df, filename)
                dataframes[file_type] = df

            try:
                merged_df = dataframes['race']
                keys = ['GP', 'Driver']

                if not all(key in merged_df.columns for key in keys):
                    print(f"ERREUR : Le fichier principal 'f1_{year}_race.csv' ne contient pas les colonnes {keys} même après tentative de standardisation.")
                    continue

                for name, df in dataframes.items():
                    if name == 'race': continue
                    
                    if all(key in df.columns for key in keys):
                        if name == 'pit_stop':
                             pit_stop_summary = df.groupby(keys, dropna=False).size().reset_index(name='Pit_Stops_Count')
                             merged_df = pd.merge(merged_df, pit_stop_summary, on=keys, how='left')
                        else:
                             merged_df = pd.merge(merged_df, df, on=keys, how='left', suffixes=('', f'_{name}'))
                    else:
                        print(f"AVERTISSEMENT : Fichier 'f1_{year}_{name}.csv' ignoré car une des colonnes {keys} est manquante.")
                
                merged_df['Year'] = year
                all_years_data.append(merged_df)

            except KeyError as e:
                print(f"ERREUR FATALE pour l'année {year} : La colonne {e} est introuvable.")
                continue

        if not all_years_data:
            print("\nTraitement terminé, mais aucune donnée n'a pu être fusionnée. Veuillez vérifier les erreurs ci-dessus.")
            return

        final_df = pd.concat(all_years_data, ignore_index=True)
        if 'Pit_Stops_Count' in final_df.columns:
            final_df['Pit_Stops_Count'] = final_df['Pit_Stops_Count'].fillna(0)

        output_filename = f'f1_{sorted_years[0]}_{sorted_years[-1]}_training_data.csv'
        final_df.to_csv(output_filename, index=False)

        print("\n--- ✅ Fusion terminée ! ---")
        print(f"Le fichier '{output_filename}' a été créé avec succès.")
        print(f"Il contient {final_df.shape[0]} lignes et {final_df.shape[1]} colonnes.")
        print("\nVoici un aperçu des 5 dernières lignes pour vérifier :")
        print(final_df.tail())

    except Exception as e:
        print(f"Une erreur inattendue et globale est survenue : {e}")

# --- Script principal ---
if __name__ == "__main__":
    BASE_DATA_PATH = 'f1_results_by_type_simple'
    merge_all_f1_data(BASE_DATA_PATH)