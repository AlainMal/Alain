# Classe permettant de lister les MMSI en temps réel.
class MMSI:
    def __init__(self,pgn):
        self._pgn = pgn

        # Variables statiques partagées entre les instances
        self._nom_bateau_a = ""
        self._nom_bateau_a= ""
        self._indicatif_a = ""
        self._indicatif_b = ""
        self._destination_bateau_a = ""
        self._position_mmsi_a = 0
        self._donnees_mmsi_a = 0
        self._position_mmsi_b = 0
        self._donnees_mmsi_b = 0

        self._table = []  # Une table (liste) pour stocker les données

        # Méthode privée pour savoir si le MMSI est dans la table.
        def __existe_dans_table(self, pgn, trame):
            """
            Fonction privée pour vérifier si une combinaison PGN et Trame existe dans la table.
            Renvoie l'élément correspondant ou None.
            """
            for item in self._table:
                if item["PGN"] == pgn and item["Trame"] == trame:
                    return item  # Retourne l'entrée si elle existe
            return None  # Retourne None si aucune entrée n'est trouvée

        # Méthode affiche dans une table les resultats des MMSI. Exemple ****** >>>
        def mmsi(self,pgn,  nom, val1,val2,val3):
            # Utilisation de la correspondance pour identifier le PGN
            match pgn:
                case 129038:  # Classe A
                    if val1 == 0 and val2 ==9:  # Première trame (initialisation)



                        self._nom_bateau_a = nom  # On stocke le nom fourni
                    elif val1 == 1:  # Trame suivante (cumul)
                        self._nom_bateau_a += nom  # Ajout au nom existant

                        # Mise à jour dans la table
                        self._table.append({"PGN": pgn, "Nom_Bateau": self._nom_bateau_a, "Trame": val1})
                    else:
                        return "Trame inconnue pour Classe A"

                case 129039:  # Classe B (si prévu dans le futur)
                    if val1 == 0:
                        self.nom_bateau_b = nom
                    elif val1 == 1:
                        self.nom_bateau_b += nom
                    else:
                        return "Trame inconnue pour Classe B"

                case _:
                    return "PGN non pris en charge"

