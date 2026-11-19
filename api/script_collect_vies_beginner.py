# Vérifier des numéros de TVA avec l'API VIES
# - les résultats vont dans un CSV
# - tout ce qui se passe est noté dans un journal (collecte.log)
# - si on relance, les numéros déjà vérifiés sont sautés
# Installation : pip install requests pandas

import csv
import logging
import os
import time
import requests
import pandas as pd

# Les noms de nos fichiers
fichier_source = "../data/numeros_tva_nettoyee.csv"
fichier_resultat = "../data/resultats.csv"

# Configuration du journal : les messages sont écrits dans collecte.log
logging.basicConfig(
    filename="collecte.log",
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# 1) On regarde si des numéros ont déjà été vérifiés
deja_faits = []
fichier_existe = os.path.exists(fichier_resultat) and os.path.getsize(fichier_resultat) > 0

if fichier_existe:
    anciens = pd.read_csv(fichier_resultat, dtype=str, keep_default_na=False)
    deja_faits = anciens["tva"].tolist()

# 2) On lit le fichier source et on retire les numéros déjà vérifiés
df = pd.read_csv(fichier_source, dtype=str, keep_default_na=False)
numeros = df["normaliser"].drop_duplicates()
numeros = numeros[~numeros.isin(deja_faits)]

# 3) On tire 250 NOUVEAUX numéros au hasard parmi ceux qui restent
# (min évite une erreur s'il en reste moins de 250)
nb = min(250, len(numeros))
echantillon = numeros.sample(nb).values.tolist()

logging.info("DEBUT DE CAMPAGNE : %s déjà vérifiés, %s nouveaux à traiter", len(deja_faits), len(echantillon))

# 3) On ouvre le fichier résultat ("a" = on ajoute à la fin)
sortie = open(fichier_resultat, "a", newline="", encoding="utf-8")
writer = csv.writer(sortie)

# On écrit les titres seulement si le fichier est nouveau
if not fichier_existe:
    writer.writerow(["tva", "valide", "erreur", "duree_secondes"])

# 4) On vérifie chaque numéro un par un
for numeros_tva in echantillon:

    # Si le numéro est déjà dans le fichier résultat, on le saute
    if numeros_tva in deja_faits:
        logging.info("SAUTE %s : deja verifie", numeros_tva)
        continue

    code_pays = numeros_tva[:2]
    numero_id = numeros_tva[2:]

    url = f"https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{code_pays}/vat/{numero_id}"
    print(f"Vérification du numéro TVA : {numeros_tva}...")

    # On appelle l'API en mesurant le temps
    try:
        timestart = time.time()
        reponse = requests.get(url, timeout=30)
        duree = round(time.time() - timestart, 2)

        # On note l'appel dans le journal : numéro, code HTTP, temps
        logging.info("APPEL %s | HTTP %s | %s s", numeros_tva, reponse.status_code, duree)

        resultat = reponse.json()

    except Exception as e:
        # Si quelque chose plante (réseau, réponse illisible...), on le note
        logging.error("ERREUR sur %s : %s", numeros_tva, e)
        writer.writerow([numeros_tva, "", "erreur", ""])
        sortie.flush()
        time.sleep(2)
        continue

    # On récupère les informations
    valide = resultat.get("isValid", resultat.get("valid"))
    erreur = resultat.get("userError")

    # Si le service renvoie une erreur, on la note dans le journal
    if erreur and erreur != "VALID":
        logging.warning("ERREUR SERVICE sur %s : %s", numeros_tva, erreur)

    # On écrit une ligne dans le fichier résultat
    writer.writerow([numeros_tva, valide, erreur, duree])
    sortie.flush()

    time.sleep(2)

# 5) On ferme le fichier
sortie.close()
logging.info("FIN DE CAMPAGNE")
print("Terminé ! Regardez le fichier collecte.log")