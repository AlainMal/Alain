# Cette classe sert uniquement à traiter les résultats.
# C'est prévu de lui faire traiter le NMEA 2000 en temps réel.
# ======================================================================================================================
class TempsReel:
    def __init__(self):
        pass

    # Méthode d'enregistremnt du bus CAN en temps réel. ----------------------------------------------------------------
    @staticmethod
    async def TempsReel(msg, file_path, coche_file, coche_buffer,coche_nmea, main_window):
        # print("On entre dans l'enregistement")
        # Initialise datas comme un str vide.
        datas = ""
        # On a défini les huits octets dans "datas".
        for i in range(msg.len):
            # On commence par un espace, car ça fini par le dernier octet.
            datas += " " + format(msg.data[i], "02X")

        if msg:
            # On met le réulltat dans un fichier si la case à cocher est validée.
            if coche_file:
                with open(file_path, "w") as file:
                    # msg.TimeStamp, msg.ID, msg.len, msg.data existent dans la structure msg
                    datas = ' '.join([f"{byte:02X}" for byte in msg.data])  # Format avec des bytes en hexadécimal
                    file.write(f"{msg.TimeStamp} {msg.ID:08X} {msg.len}{datas}\n")

            # On met le réulltat dans la table si la case à cocher est validée
            if coche_buffer:
                # Préparation d'un tuple pour la table
                tuple_modifie = (
                    format(msg.ID,'08X'),  # Identifiant CAN sur huits caractères en hexadécimale.
                    str(msg.len),  # Longueur des données sur un caractère.
                    ' '.join(f"{byte:02X}" for byte in msg.data)  # Données formatées (hexadécimal)
                )
                # On met le tuple modifié dans la table en buffer tournant.
                main_window.add_to_buffer(tuple_modifie)

            # *************** EMPLACEMENT PREVU POUR METTRE LE TEMPS REEL *********************
            #                             NMEA 2000
            #                       Affichage des jauges
            #                       Affichage des MMSI
            #                       Affichage de la carte
            # *********************************************************************************

            # On appelle la routine "octets" si la case à cocher est validée pour NMEA 2000 en temps réel.
            if coche_nmea:
                # Fournit le résultat de ma position, pour l'afficher sur la carte en temps réel.
                pgn =  main_window.NMEA2000.pgn( msg.ID)
                main_window.NMEA2000.octets(pgn, msg.data) # Ce qui est fait dans "octets".
            # =================================================================================
