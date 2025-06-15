# merge_all_data.py
import pandas as pd
from pathlib import Path # Import the Path class

# --- Configuration des Noms de Fichiers ---
HISTORICAL_DATA_DIR = Path("f1_summary_files") # Convert to a Path object

MERGED_RACES_PATH = HISTORICAL_DATA_DIR / "race_all_years.csv"
MERGED_QUALI_PATH = HISTORICAL_DATA_DIR / "qualifying_all_years.csv"
MERGED_P1_PATH = HISTORICAL_DATA_DIR / "practice_1_all_years.csv"
MERGED_P2_PATH = HISTORICAL_DATA_DIR / "practice_2_all_years.csv"
MERGED_P3_PATH = HISTORICAL_DATA_DIR / "practice_3_all_years.csv"
MERGED_GRID_PATH = HISTORICAL_DATA_DIR / "starting_grid_all_years.csv"

def merge_all_historical_data():
    """
    Charge tous les fichiers CSV historiques par type (race_all_years, etc.)
    et les fusionne en un seul grand DataFrame, sauvegardé en CSV.
    """
    print("--- Lancement de la fusion de toutes les données historiques ---")
    
    try:
        # --- 1. Charger chaque fichier de données ---
        print("Chargement des fichiers CSV de base...")
        races = pd.read_csv(MERGED_RACES_PATH)
        qualis = pd.read_csv(MERGED_QUALI_PATH)
        grids = pd.read_csv(MERGED_GRID_PATH)
        fp1 = pd.read_csv(MERGED_P1_PATH)
        fp2 = pd.read_csv(MERGED_P2_PATH)
        fp3 = pd.read_csv(MERGED_P3_PATH)
        # Vous pouvez charger d'autres fichiers comme les pitstops ici

        # --- 2. Préparer et fusionner les DataFrames ---
        print("Fusion des données en cours...")

        # Clés de fusion communes
        merge_keys = ['race_id', 'driver_number']
        
        # On part des résultats de course comme base
        # On s'assure que la colonne 'team' est bien là
        merged_df = races.copy()

        # Fusionner avec la grille de départ
        # On ne garde que les colonnes utiles pour éviter les colonnes en double
        grid_cols_to_merge = ['race_id', 'driver_number', 'position']
        merged_df = pd.merge(
            merged_df, 
            grids[grid_cols_to_merge], 
            on=merge_keys, 
            how='left',
            suffixes=('', '_grid') # Suffixe pour la colonne position
        )
        merged_df.rename(columns={'position_grid': 'grid', 'position': 'position'}, inplace=True)


        # Fusionner avec les qualifications
        quali_cols_to_merge = ['race_id', 'driver_number', 'q1_time', 'q2_time', 'q3_time']
        merged_df = pd.merge(merged_df, qualis[quali_cols_to_merge], on=merge_keys, how='left')

        # Fusionner avec les essais libres, en renommant les colonnes pour les distinguer
        fp1.rename(columns={'lap_time': 'fp1_time'}, inplace=True)
        fp2.rename(columns={'lap_time': 'fp2_time'}, inplace=True)
        fp3.rename(columns={'lap_time': 'fp3_time'}, inplace=True)
        
        merged_df = pd.merge(merged_df, fp1[['race_id', 'driver_number', 'fp1_time']], on=merge_keys, how='left')
        merged_df = pd.merge(merged_df, fp2[['race_id', 'driver_number', 'fp2_time']], on=merge_keys, how='left')
        merged_df = pd.merge(merged_df, fp3[['race_id', 'driver_number', 'fp3_time']], on=merge_keys, how='left')
        
        # --- 3. Sauvegarder le grand fichier final ---
        # On le sauvegarde dans le même dossier pour la simplicité
        output_path = HISTORICAL_DATA_DIR / "F1_ALL_DATA_2020_2024.csv"
        merged_df.to_csv(output_path, index=False)
        
        print(f"\n✅ Fusion terminée ! Le jeu de données complet est sauvegardé ici :")
        print(output_path)
        
    except FileNotFoundError as e:
        print(f"\n❌ ERREUR: Fichier non trouvé : {e.filename}")
        print("Veuillez vous assurer que tous vos fichiers CSV mergés (race_all_years.csv, etc.) se trouvent bien dans le dossier défini dans config.py.")
    except Exception as e:
        print(f"\n❌ Une erreur inattendue est survenue : {e}")

if __name__ == "__main__":
    merge_all_historical_data()