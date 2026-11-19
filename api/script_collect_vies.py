# Lire des numéros de TVA dans un CSV, les vérifier avec l'API VIES,
# puis écrire les résultats dans un autre CSV.
# Si on relance le script, il ne refait PAS les appels déjà faits.
# Installation : pip install requests pandas

import csv
import os
import time
import requests
import pandas as pd

# Les noms de nos fichiers
fichier_source = "../data/numeros_tva_nettoyee.csv"
fichier_resultat = "../data/resultats.csv"

# 1) On lit le fichier source et on prend 250 numéros au hasard
# random_state=42 : on obtient TOUJOURS les mêmes 250 numéros à chaque lancement
# (sans ça, un nouveau lancement piocherait d'autres numéros)
df = pd.read_csv(fichier_source, dtype=str, keep_default_na=False)
echantillon = df["normaliser"].sample(200, random_state=42).values.tolist()

# 2) On regarde ce qui a déjà été fait lors d'un lancement précédent
deja_faits = set()
fichier_existe = os.path.exists(fichier_resultat) and os.path.getsize(fichier_resultat) > 0

if fichier_existe:
    anciens = pd.read_csv(fichier_resultat, dtype=str, keep_default_na=False)
    deja_faits = set(anciens["tva"])
    print(len(deja_faits), "numéros déjà faits, on les saute")

# 3) On ouvre le fichier résultat
# "a" = on AJOUTE à la fin (sans effacer ce qui existe déjà)
sortie = open(fichier_resultat, "a", newline="", encoding="utf-8")
writer = csv.writer(sortie)

# On écrit les titres des colonnes seulement si le fichier est nouveau
if not fichier_existe:
    writer.writerow(["tva", "valide", "erreur", "duree_secondes"])

# 4) On vérifie chaque numéro un par un
nb_appels = 0
for numeros_tva in echantillon:

    # Si ce numéro est déjà dans le fichier résultat, on passe au suivant
    if numeros_tva in deja_faits:
        continue

    code_pays = numeros_tva[:2]
    numero_id = numeros_tva[2:]

    url = f"https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{code_pays}/vat/{numero_id}"
    print(f"Vérification du numéro TVA : {numeros_tva}...")

    # On appelle l'API en mesurant le temps
    timestart = time.time()
    reponse = requests.get(url)
    timeend = time.time()
    duree = round(timeend - timestart, 2)

    # Si la réponse n'est pas du JSON, on note l'erreur et on passe au suivant
    try:
        resultat = reponse.json()
    except Exception:
        print("  -> réponse illisible, code", reponse.status_code)
        writer.writerow([numeros_tva, "", f"reponse illisible ({reponse.status_code})", duree])
        sortie.flush()
        time.sleep(2)
        continue

    # On récupère les informations
    valide = resultat.get("isValid", resultat.get("valid"))
    erreur = resultat.get("userError")

    # On écrit une ligne dans le fichier résultat
    writer.writerow([numeros_tva, valide, erreur, duree])
    sortie.flush()  # on écrit tout de suite dans le fichier

    nb_appels = nb_appels + 1
    time.sleep(2)

# 5) On ferme le fichier
sortie.close()
print("Terminé !", nb_appels, "nouveaux appels. Résultats dans", fichier_resultat)