import pandas as pd, json
import numpy as np

# Load data
df = pd.read_csv(r'C:\\Users\\Utilisateur\\Documents\\Simplon\\Exércices\\Brief-TVA\\data\\numeros_tva.csv')
col = df['numero_tva']

# Define representations of empty
representations = {
    "NaN": lambda s: s.isna(),
    "'' (empty string)": lambda s: s.astype(str) == '',
    "' ' (space)": lambda s: s.astype(str) == ' ',
    "'nan'": lambda s: s.astype(str).str.lower() == 'nan',
    "'null'": lambda s: s.astype(str).str.lower() == 'null',
    "'N/A'": lambda s: s.astype(str).str.upper() == 'N/A',
    "'-'": lambda s: s.astype(str) == '-',
}

counts = {name: int(func(col).sum()) for name, func in representations.items()}
print(json.dumps(counts, ensure_ascii=False))
