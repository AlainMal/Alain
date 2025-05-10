import math
from Package.constante import *

# **********************************************************************************************************************
#       Programme d'analyse des trames du bus CAN et les transforment en NMEA 2000
# **********************************************************************************************************************

# Cette classe permet de déduire le PGN, sa source, son destinataire, sa priorité et la définition des octets.
class NMEA2000:
    def __init__(self,main_window):
        self.main_window = main_window
        self._definition = None
        print("NMEA2000 initialisé.")

        self._analyse0 = None
        self._analyse1 = None
        self._analyse2 = None
        self._analyse3 = None
        self._analyse4 = None
        self._analyse5 = None
        self._analyse6 = None
        self._analyse7 = None

        self._pgn1 = None
        self._pgn2 = None
        self._pgn3 = None
        self._definition = None
        self._valeurChoisieTab = None
        self._valeurChoisie2 = None
        self._valeurChoisie1 = None
        self._valeurChoisie3 = None
        self._priorite = None
        self._destination = None
        self._source = None
        self._pgn = None

        self._coor = None

        # Défini la taille de la mémoire, elle est calculé au plus juste, mais c'est la plus rapide.
        nombre_octets = 8
        nombre_pgn = 25
        nombre_trames = 36  # On limite la valeur à 36 le nombre maximum de trames sur le même PGN.
        valeur_defaut = 0

        # Crée une table 3D fixe remplie avec la valeur par défaut
        self.memoire = [[[valeur_defaut for _ in range(nombre_trames)]
                         for _ in range(nombre_pgn)]
                        for _ in range(nombre_octets)]

    # ========================== Méthodes de récupération des valeurs dans l'ID ========================================
    # On récupère le PGN, puis la source ensuite la detination ensuite la priorité.
    def pgn(self, id_msg):
        try:
            pf = (id_msg & 0x00FF0000) >> 16  # Extraire les bits PF (byte 2)
            ps = (id_msg & 0x0000FF00) >> 8  # Extraire les bits PS (byte 1)
            dp = (id_msg & 0x03000000) >> 24  # Extraire les bits DP (bits 24-25)

            if pf < 240:  # Si PF < 240, c'est un message point à point
                self._pgn = (dp << 16) | (pf << 8)  # Construire le PGN

            else:  # Sinon, c'est un message global (broadcast)
                self._pgn = (dp << 16) | (pf << 8) | ps

            return self._pgn

        except Exception as e:
            print(f"Erreur dans la méthode 'pgn' : {e}")
            raise

    def source(self,id_msg):
        self._source = id_msg & 0xFF
        return self._source

    def destination(self,id_msg):
        if ((id_msg & 0xFF0000) >> 16) < 240:
            self._destination = (id_msg &  0x00FF00) >> 8
        else:
            self._destination = (id_msg & 0xFF0000) >> 16

        return self._destination

    def priorite(self,id_msg):
        self._priorite = (id_msg & 0x1C000000) >> 26
        return self._priorite

    # Renvoi un tuple contenant toutes les variables contenus dans l'id
    def id(self,id_msg):
        return self.pgn(id_msg), self.source(id_msg) ,self.destination(id_msg),self.priorite(id_msg)
    # ================================== FIN DES METHODES POUR L'ID ====================================================

    # ================================= Méthodes de gestion de la mémoire ==============================================
    def set_memoire(self, numero_d_octet, numero_pgn, numero_de_trame, valeur):
        self.memoire[numero_d_octet][numero_pgn][numero_de_trame] = valeur

    def get_memoire(self, numero_d_octet, numero_pgn, numero_de_trame):
        return self.memoire[numero_d_octet][numero_pgn][numero_de_trame]
    # ======================================== Fin des mémoires ========================================================


    # ============================= Méthodes de récupération des valeurs des octets ====================================
    def octets(self,pgn,datas):
        self._pgn1 = None
        self._pgn2 = None
        self._pgn3 = None
        self._valeurChoisieTab = None
        self._valeurChoisie2 = None
        self._valeurChoisie1 = None
        self._valeurChoisie3 = None
        self._definition = None
        # z = Numéro de trame

        try:
            match pgn:
                case 129025:
                    self._valeurChoisie1 = "{:.6f}".format((datas[3] << 24 | datas[2] << 16
                                                            | datas[1] << 8 | datas[0]) * (10 ** -7))
                    self._pgn1 = "Lattitude"

                    self._valeurChoisie2 = "{:.6f}".format((datas[7] << 24 | datas[6] << 16
                                                            | datas[5] << 8 | datas[3]) * (10 ** -7))
                    self._pgn2 = "Longitude"

                    # Pour Analyse.
                    self._analyse3 = "Coor " + self._pgn1
                    self._analyse2 = "Coor " + self._pgn1
                    self._analyse1 = "Coor " + self._pgn1
                    self._analyse0 = "Coor " + self._pgn1
                    self._analyse7 = "Coor " + self._pgn2
                    self._analyse6 = "Coor " + self._pgn2
                    self._analyse5 = "Coor " + self._pgn2
                    self._analyse4 = "Coor " + self._pgn2

                    # Mise à jour des coordonnées sur la carte environ toutes les secondes (1/10 scrutation).
                    if self._coor % 10 == 0:
                        self.main_window.update_coordinates(self._valeurChoisie1,self._valeurChoisie2)

                    self._coor += 1

                case 130306:
                    self._valeurChoisie1 = "{:.2f}".format((datas[2] << 8 | datas[1]) * 0.01 * 1.94384449)
                    self._pgn1 = "Noeuds du Vent"

                    self._valeurChoisie2 = "{:.2f}".format((datas[4] << 8 | datas[3]) * 0.0001 * 180 / math.pi)
                    self._pgn2 = "Direction du vent"

                    self._valeurChoisieTab = datas[5] & 0x07
                    self._definition = VENT[self._valeurChoisieTab]

                    # Pour Analyse.
                    self._analyse2 = "Nds " + self._pgn1
                    self._analyse1 = "Nds " + self._pgn1
                    self._analyse4 = "Deg " + self._pgn2
                    self._analyse3 = "Deg " + self._pgn2
                    self._analyse5 = "Table: sur 3 bits"

                case 129026:
                    self._valeurChoisie1 = "{:.2f}".format((datas[3] << 8 | datas[2]) * 0.0001 * 180 / math.pi)
                    self._pgn1 = "COG"

                    self._valeurChoisie2 = "{:.2f}".format((datas[5] << 8 | datas[4]) * 0.01 * 1.94384449)
                    self._pgn2 = "SOG"

                    # Pour Analyse.
                    self._analyse3 = "Deg " + self._pgn1
                    self._analyse2 = "Deg " + self._pgn1
                    self._analyse5 = "Nds " + self._pgn2
                    self._analyse4 = "Nds " + self._pgn2

                case 127250:
                    self._valeurChoisie1 = "{:.2f}".format((datas[2] << 8 | datas[1]) * 0.0001 * 180 / math.pi)
                    self._pgn1 = "Heading"

                    # Pour Analyse.
                    self._analyse2 = "Deg " + self._pgn1
                    self._analyse1 = "Deg " + self._pgn1

                    self._analyse4 = "Deg Déviation"
                    self._analyse3 = "Deg Déviation"
                    self._analyse6 = "Deg Variation"
                    self._analyse5 = "Deg Variation"
                    self._analyse7 = "Référence 2 bits"

                case 128267:
                    self._valeurChoisie1 = "{:.2f}".format((datas[4] << 24 | datas[3] << 16
                                                            |  datas[2] << 8 |  datas[1]   )  * 0.01)
                    self._pgn1 = "Profondeur"

                    # Pour Analyse.
                    self._analyse4 = "m " + self._pgn1
                    self._analyse3 = "m " + self._pgn1
                    self._analyse2 = "m " + self._pgn1
                    self._analyse1 = "m " + self._pgn1
                    self._analyse6 = "Sous la quille"
                    self._analyse5 = "Sous la quille"

                case 130312:
                    self._valeurChoisie1 = "{:.2f}".format((datas[4] << 8 | datas[3])  * 0.01 - 273.15)
                    self._pgn1 = "Température"

                    self._valeurChoisieTab = datas[2]
                    self._definition = TEMPERATURE[self._valeurChoisieTab]

                    # Pour Analyse.
                    self._analyse4 = "°C " + self._pgn1
                    self._analyse3 = "°C " + self._pgn1
                    self._analyse6 = "°C R&gler la temp."
                    self._analyse5 = "°C R&gler la temp."

                case 130316:
                    self._valeurChoisie1 = "{:.2f}".format((datas[5] << 16 | datas[4] << 8 | datas[3]) * 0.01 - 273.15)
                    self._pgn1 = "Température étendue"

                    self._valeurChoisieTab = datas[2]
                    self._definition = TEMPERATURE[self._valeurChoisieTab]

                    # Pour Analyse.
                    self._analyse5 = "°C " + self._pgn1
                    self._analyse4 = "°C " + self._pgn1
                    self._analyse3 = "°C " + self._pgn1
                    self._analyse2 = "Table Temp."

                case 130310:
                    self._pgn1 = "Température Mer"
                    if datas[2] & 0xEF != 0xEF:
                        self._valeurChoisie1 = "{:.2f}".format((datas[2] << 8 | datas[1]) * 0.01 - 273.15)

                    self._pgn2 = "Température de l'air"
                    if datas[4] & 0xEF != 0xEF:
                        if datas[4] & 0xEf != 0xEF:
                            self._valeurChoisie2 = "{:.2f}".format((datas[4] << 8 | datas[3]) * 0.01 - 273.15)

                    self._pgn3 = "Pression atmosphérique"
                    if datas[6] & 0xEF != 0xEF:
                        self._valeurChoisie3 = "{:.2f}".format((datas[6] << 8 | datas[5]))

                    # Pour Analyse.
                    self._analyse2 = "°C " + self._pgn1
                    self._analyse1 = "°C " + self._pgn1
                    self._analyse4 = "°C " + self._pgn2
                    self._analyse3 = "°C " + self._pgn2
                    self._analyse6 = "mBar " + self._pgn3
                    self._analyse5 = "mBar " + self._pgn3

                case 128259:
                    self._pgn1 = "Vitesse surface"
                    if datas[2] & 0xEf != 0xEF:
                        self._valeurChoisie1 = "{:.2f}".format((datas[2] << 8 | datas[1]) * 0.01 * 1.94384449)

                    self._pgn2 = "Vitesse fond"
                    if datas[4] & 0xEf != 0xEF:
                        self._valeurChoisie2 = "{:.2f}".format((datas[4] << 8 | datas[3]) * 0.01 * 1.94384449)

                    self._valeurChoisieTab = (datas[5])
                    self._definition = WATER_SPEED[self._valeurChoisieTab]


                    # Pour Analyse.
                    self._analyse2 = "Nds " + self._pgn1
                    self._analyse1 = "Nds " + self._pgn1
                    self._analyse4 = "Nds " + self._pgn2
                    self._analyse3 = "Table 3 bits"
                    self._analyse5 = "Table 3 bits"

                case 127508:
                    self._pgn1 = "Volts Batterie"
                    if (datas[2] <<8 | datas[1]) != 0x7FFF:
                        self._valeurChoisie1 = "{:.2f}".format((datas[2] << 8 | datas[1]) * 0.01)

                    self._pgn2 = "Ampères Batterie"
                    raw_value = ((datas[4] << 8) | datas[3])
                    if raw_value != 0x7FFF:
                        self._valeurChoisie2 = "{:.2f}".format((raw_value if raw_value < 0x8000 else raw_value - 0x10000) *0.1)


                    self._pgn3 = "Température Batterie"
                    if datas[6] & 0xEf != 0xEF:
                        self._valeurChoisie3 = "{:.2f}".format((datas[6] << 8 | datas[5]) * 0.01 - 273.15)

                    # Pour Analyse.
                    self._analyse2 = "Volts " + self._pgn1
                    self._analyse1 = "Volts " + self._pgn1
                    self._analyse4 = "Amp " + self._pgn2
                    self._analyse3 = "Amp " + self._pgn2
                    self._analyse6 = "°C " + self._pgn3
                    self._analyse5 = "°C " + self._pgn3

                case 129038:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "AIS Posittion Class A"

                    if z == 0:
                        self._valeurChoisie2 = datas[6] << 24 | datas[5] << 16 | datas[4] << 8 | datas[3]
                        self._pgn2 = "MMSI"
                        self.set_memoire(MEMOIRE_PGN_a7,PGN_129038,z + 1,datas[7])

                    elif z == 1:
                        self._valeurChoisie2 = "{:.6f}".format((datas[3] << 24 | datas[2] << 16 | datas[1] << 8
                                                | self.get_memoire(MEMOIRE_PGN_a7,PGN_129038,z))
                                                               * (10**-7))
                        self._pgn2 = "AIS_A Longitude"

                        self._valeurChoisie3 = "{:.6f}".format((datas[7] << 24 | datas[6] << 16
                                                                | datas[5] << 8 | datas[4] ) * (10**-7))
                        self._pgn3 = "AIS_A Latitude"

                    elif z == 2:
                        self._valeurChoisie2 = "{:.2f}".format((datas[3] << 8 | datas[2]) * 0.0001 * 180 / math.pi)
                        self._pgn2 = "AIS_A COG"

                        self._valeurChoisie3 = "{:.2f}".format((datas[5] << 8 | datas[4]) * 0.01 * 1.94384449)
                        self._pgn3 = "AIS_A SOG"

                    elif z == 3:
                        self._valeurChoisie2 = "{:.2f}".format((datas[3] << 8 | datas[2]) * 0.0001 * 180 / math.pi)
                        self._pgn2 = "AIS_A Heading"

                case 129794:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "AIS Données classe A"

                    if z == 0:
                        self._valeurChoisie2 = datas[6] << 24 | datas[5] << 16 | datas[4] << 8 | datas[3]
                        self._pgn2 = "MMSI"

                    elif z == 1:
                        self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(4, 8)])
                        self._pgn2 = "Indicatif"

                    elif z == 2:
                        self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(1, 4)])
                        self._pgn2 = "Indicatif"

                        self._valeurChoisie3 = "".join([chr(datas[i]) for i in range(4, 8)])
                        self._pgn3 = "Nom du navire"

                    elif z == 3 or z == 4:
                        self._valeurChoisie3 = "".join([chr(datas[i]) for i in range(1, 8)])
                        self._pgn3 = "Nom du navire"

                    elif z == 5:
                        self._valeurChoisie2 = "{:.2f}".format((datas[5] << 8 | datas[4]) * 0.1)
                        self._pgn2 = "Longueur"

                        self._valeurChoisie3 = "{:.2f}".format((datas[7] << 8 | datas[6]) * 0.1)
                        self._pgn3 = "Largeur"

                    elif z == 6:
                        self._valeurChoisie2 = "{:.2f}".format((datas[3] << 8 | datas[2]) * 0.0001 / 1.85)
                        self._pgn2 = "Longueur"

                        self._valeurChoisie3 = "{:.2f}".format((datas[5] << 8 | datas[4]) * 0.0001 / 1.85)
                        self._pgn3 = "Largeur"

                    elif z == 7:
                        self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(6, 8)])
                        self._pgn2 = "Destinaion"

                    elif z == 8 or z == 9:
                        self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(1, 8)])
                        self._pgn2 = "Destinaion"

                case 129809:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "AIS Données classe B"

                    if z == 0:
                        self._valeurChoisie2 = datas[6] << 24 | datas[5] << 16 | datas[4] << 8 | datas[3]
                        self._pgn2 = "MMSI"

                        self._valeurChoisie2 = chr(datas[7])
                        self._pgn2 = "Nom du navire"

                    elif z == 1:
                        self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(1, 8)])
                        self._pgn2 = "Nom du navire"

                    elif z == 2:
                        self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(1, 6)])
                        self._pgn2 = "Nom du navire"

                case 129039:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "AIS Position classe B"

                    if z == 0:
                        self._valeurChoisie2 = datas[6] << 24 | datas[5] << 16 | datas[4] << 8 | datas[3]
                        self._pgn2 = "MMSI"

                        self.set_memoire(MEMOIRE_PGN_a7, PGN_129039, z + 1, datas[7])

                    elif z == 1:
                        self._valeurChoisie2 = "{:.6f}".format((datas[3] << 24 | datas[2] << 16 | datas[1] << 8
                                                | self.get_memoire(MEMOIRE_PGN_a7,PGN_129039,z)) * (10**-7))
                        self._pgn2 = "AIS_B Longitude"

                        self._valeurChoisie3 = "{:.6f}".format((datas[7] << 24 | datas[6] << 16
                                                                | datas[5] << 8 | datas[4] ) * (10**-7))
                        self._pgn3 = "AIS_B Latitude"

                    elif z == 2:
                        self._valeurChoisie2 = "{:.2f}".format((datas[3] << 8 | datas[2]) * 0.0001 * 180 / math.pi)
                        self._pgn2 = "AIS_B COG"

                        self._valeurChoisie3 = "{:.2f}".format((datas[5] << 8 | datas[4]) * 0.01 * 1.94384449)
                        self._pgn3 = "AIS_B SOG"

                    elif z == 3:
                        self._valeurChoisie2 = "{:.2f}".format((datas[3] << 8 | datas[2]) * 0.0001 * 180 / math.pi)
                        self._pgn2 = "AIS_B Heading"

                case 129810:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "AIS Données classe A Part B"

                    if z == 0:
                        self._valeurChoisie2 = datas[6] << 24 | datas[5] << 16 | datas[4] << 8 | datas[3]
                        self._pgn2 = "MMSI"

                    elif z == 2 or z == 3:
                        self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(1, 8)])
                        self._pgn2 = "Indicatif"

                case 129029:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "Info. de positioon GNSS"

                    if z == 4:
                        self._valeurChoisie2 = datas[7]
                        self._pgn2 = "Nombre de satélites"

                case 129539:
                    self._valeurChoisie1 = "N° " + str(datas[0] & 0x1F)
                    self._pgn1 = "Précision GNSS"

                case 130577:
                    z = (datas[0] & 0x0F)
                    self._valeurChoisie1 = "N° "+ str(z)
                    self._pgn1 = "Données de direction"

                    if z == 1:
                        self._pgn2 = "COG"
                        if datas[2] & 0xEF != 0xEF:
                            self._valeurChoisie2 = "{:.2f}".format((datas[2] << 8 | datas[1]) * 0.0001 * 180 / math.pi)

                        self._pgn3 = "SOG"
                        if datas[4] & 0xEF != 0xEF:
                            self._valeurChoisie3 = "{:.2f}".format((datas[4] << 8 | datas[3]) * 0.01 * 1.94384449)


                case 127506:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° "+ str(z)
                    self._pgn1 = "Batteries détaillées"

                    if z == 0:
                        self._valeurChoisieTab = (datas[4])
                        self._definition = ENERGIE_DC[self._valeurChoisieTab]

                        self._valeurChoisie2 = datas[5]
                        self._pgn2 = "Etat de charge"

                        self._valeurChoisie2 = datas[6]
                        self._pgn2 = "Etat de santé"

                        self.set_memoire(MEMOIRE_PGN_a7,PGN_127506,z + 1,datas[7])

                    elif z == 1:
                        if not self.get_memoire(MEMOIRE_PGN_a7,PGN_127506,z) == 0xFF:
                            self._pgn2 = "Temps restant"
                            if datas[1] & 0xEF != 0xEF:
                                self._valeurChoisie2 = (datas[1] << 8
                                                    | self.get_memoire(MEMOIRE_PGN_a7,PGN_127506,z))

                        self._pgn3 = "Ah"
                        if datas[5] & 0xEF != 0xEF:
                            self._valeurChoisie3 = datas[5] << 8 | datas[4]



                case 126720:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "Info propriétaire"

                    if z == 0:
                        self._valeurChoisie2 = datas[2]
                        self._pgn2 = "Code propriétaire"

                case 127245:
                    if datas[0] != 0xFF:
                        self._valeurChoisie1 =  "{:.2f}".format((datas[5] << 8 | datas[4]) * 0.0001 * 180 / math.pi)

                    self._pgn1 = "Ordre de barre"

                case 127251:
                    self._valeurChoisie1 =  "{:.2f}".format((datas[3] << 8 | datas[2])  * 0.00000003125 * 180 / math.pi)
                    self._pgn1 = "Vitesse de rotation"

                case 126464:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(datas[0] & 0x1F)
                    self._pgn1 = "Liste des PGN"

                    if (z + 3) % 3 == 0:
                        temp = (datas[5] << 16 | datas[4] << 8 | datas[3])
                        self._pgn2 = "Num PGN"
                        if not (temp < 59392 or temp > 130944 or datas[5] & 0xEF == 0xEF):
                            self._valeurChoisie2 = temp
                            self.set_memoire(MEMOIRE_PGN_a6, PGN_126464, z + 1, datas[6])
                            self.set_memoire(MEMOIRE_PGN_a7, PGN_126464, z + 1, datas[7])


                    elif (z + 2) % 3 == 0:
                        temp =  (datas[1] << 16 | self.get_memoire(MEMOIRE_PGN_a7,PGN_126464,z) << 8
                                                | self.get_memoire(MEMOIRE_PGN_a6,PGN_126464,z))
                        self._pgn2 = "Num PGN"
                        if not (temp < 59392 or temp > 130944 or datas[1] & 0xEF == 0xEF):
                            self._valeurChoisie2 = temp


                        temp = (datas[4] << 16 | datas[3] << 8 | datas[2])
                        self._pgn3 = "Num PGN"
                        if not (temp < 59392 or temp > 130944 or datas[4] & 0xEF == 0xEF):
                            self._valeurChoisie3 = temp


                        temp = (datas[7] << 16 | datas[6] << 8 | datas[5])
                        if not (temp < 59392 or temp > 130944 or datas[7] & 0xEF == 0xEF):
                            self._valeurChoisieTab = "Num PGN: " + str(temp)


                    elif (z + 1) % 3 == 0:
                        temp = (datas[3] << 16 | datas[2] << 8 | datas[1])
                        self._pgn2 = "Num PGN"
                        if not (temp < 59392 or temp > 130944 or datas[3] & 0xEF == 0xEF):
                            self._valeurChoisie2 = temp


                        temp = (datas[6] << 16 | datas[5] << 8 | datas[4])
                        self._pgn3 = "Num PGN"
                        if not (temp < 59392 or temp > 130944 or datas[6] & 0xEF == 0xEF):
                            self._valeurChoisie3 = temp

                case 126993:
                    self._pgn1 = "Heart beat"
                    self._pgn2 = "Heart beat"
                    if datas[2] & 0xEF != 0xEF:
                        self._valeurChoisie1 = "{:.2f}".format((datas[2] << 8 | datas[1]) * 0.001)


                case 127505:
                    self._pgn1 = "Niveau Réservoir"
                    if datas[2] & 0xEF != 0xEF:
                        self._valeurChoisie1 = "{:.2f}".format((datas[2] << 8 | datas[1]) * 0.004)


                    self._pgn2 = "Capacité du reservoir"
                    if datas[6] & 0xEF != 0xEF:
                        self._valeurChoisie2 = "{:.2f}".format((datas[6] << 24 | datas[5] << 16
                                                                | datas[4] << 8 | datas[3]) * 0.1)

                    self._valeurChoisieTab = datas[0] & 0x0F
                    self._definition = RESERVOIR[self._valeurChoisieTab]


                case 128275:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "Journal"

                    if z == 1:
                        self._pgn2 = "Distance parcourrue"
                        if datas[6] & 0xEF != 0xEF:
                            self._valeurChoisie2 = (datas[6] << 24 | datas[5] << 16 | datas[4] << 8 | datas[3])

                case 129540:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "Satélites en vues"

                    if z == 0:
                        self._valeurChoisie2 = datas[5]
                        self._pgn2 = "Nombre de satélites"

                case 129284:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "Données Navigation"

                    if z == 4:
                        self._pgn2 ="Latitude Waypoint"
                        self._pgn3 = "Longitude Waypoint"

                case 126996:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 = "N° " + str(z)
                    self._pgn1 = "Information prodruit"

                    self._pgn2 = "Configuration"
                    if datas[6] & 0xEF != 0xEF:
                        self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(6, 8)])

                    if z == 1 or z == 2 or z == 3 or z == 4:
                        self._pgn2 = "Configuration"
                        if datas[1] & 0xEF != 0xEF:
                            self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(1, 8)])

                    elif z == 5:
                        self._pgn2 = "Version"
                        if datas[3] & 0xEF != 0xEF:
                            self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(3, 8)])

                case 126998:
                    z = (datas[0] & 0x1F)
                    self._valeurChoisie1 ="N° " +  str(z)
                    self._pgn1 = "Info Configuration"

                    if z == 0:
                        self._pgn2 = "Configuration"
                        if datas[6] & 0xEF != 0xEF:
                            self._valeurChoisie2 = "".join([chr(datas[i]) for i in range(1, 7)])


                case 127258:
                    self._valeurChoisie1 = "{:.2f}".format((datas[5] << 8 | datas[4]) * 0.0001 * 180 / math.pi)
                    self._pgn1 = "Variation magnétique"

                case 130314:
                    self._valeurChoisie1 = "{:.2f}".format((datas[6] << 24 | datas[5] << 16 | datas[4] << 8 | datas[3]) * 0.001)
                    self._pgn1 = "Prssion atmosphérique"

                    self._valeurChoisieTab = datas[2]
                    self._definition = PRESSION[self._valeurChoisieTab]


                case 129283:
                    self._pgn1 = "XTE"
                    if datas[5] & 0xEF != 0xEF:
                        self._valeurChoisie1 = "{:.2f}".format((datas[5] << 24 | datas[4] << 16 | datas[3] << 8 | datas[2]) * 0.00001)

                    self._valeurChoisieTab = datas[1] & 0xF0 >> 4
                    self._definition = MODE_XTE[self._valeurChoisieTab]

                case 59392:
                    self._valeurChoisie1 = datas[7] << 16 | datas[6] << 8 | datas[5]
                    self._pgn1 = "Aquittement ISO"

                case 59904:
                    self._pgn1 = "Réclame le PGN ISO"
                    self._valeurChoisie1 = datas[2] << 16 | datas[1] << 8 | datas[0]


                case 60160:
                    self._valeurChoisie1 = datas[0]
                    self._pgn1 = "Protocole de transfert ISO"

                case 61184:
                    self._valeurChoisie1 = datas[0]
                    self._pgn1 = "Propriétaire Numeéro"

                case 60416:
                    self._valeurChoisie1 = datas[0] & 0x0F
                    self._pgn1 = "Protocole de transfert ISO"

                case 60928:
                    self._pgn1 = "Réponse Adresse revendiquée"
                    self._pgn2 = "Code fabriquant"
                    self._valeurChoisie2 = (datas[3] & 0x7) <<8 | datas[2]

                case _:
                    self._pgn1 = "<PGN inconnu sur cette version>"
                    print(f"PGN inattendu : {pgn}, Données : {datas}")
                    return None, None, None, None, None, None, None

        except KeyError:
            print(f"ERREUR sur le PGN: {pgn}")

        finally:
            # Retoune le tuple qui ne comprend pas les analyses pour l'instant.
            return (self._pgn1, self._pgn2, self._pgn3, self._valeurChoisie1,
                    self._valeurChoisie2, self._valeurChoisie3, self._valeurChoisieTab, self._definition)

