import asyncio
import csv
import os
import subprocess
import sys
import webbrowser

from quart import Quart, jsonify, render_template
from qasync import QEventLoop
from PyQt5.QtWidgets import QTableView, QMessageBox, QFileDialog
from PyQt5.QtWidgets import QApplication, QMainWindow, QAbstractItemView
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from Package.CAN_dll import WindowsUSBCANInterface
from Package.TempsReel import TempsReel
from Package.NMEA_2000 import NMEA2000
from Package.CANApplication import CANApplication

# ========================== METHODE QUI SONT ASYNCHRONE SUR JSON ======================================================
# Application Quart
quart_app = Quart(__name__)

# Route pour afficher le fichier HTML (page de la carte)
@quart_app.route('/map')
async def map_page():
    """Affiche la page HTML 'index.html'."""
    return await render_template("index.html")

# Variables globales pour stocker les coordonnées
coordinates = {"latitude": 0.0, "longitude": 0.0}

@quart_app.route('/map')
async def display_map():
    """Route qui affiche les coordonnées actuelles."""
    return jsonify(coordinates)
# ===================================== FIN DE JSON ====================================================================


# ********************************** CLASSE MODELE DE LA TABLE *********************************************************
# Cette classe sert de modèle à la table incluse dans MainWindow().
class TableModel(QAbstractTableModel):
    def __init__(self, buffer, buffer_index, buffer_capacity):
        """
        Initialise le modèle avec le buffer circulaire.
        """
        super().__init__()
        self._buffer_count = 0
        self._buffer = buffer
        self._buffer_index = buffer_index
        self._buffer_capacity = buffer_capacity
        self._row_count = 0  # Nombre réel de lignes dans le buffer.

    # ==================================== DEBUT DES METHODES DE LA TABLE ==============================================
    # Méthode pour actualiser le buffer de la table. -------------------------------------------------------------------
    def update_buffer(self, buffer, buffer_index, row_count):
        self.beginResetModel()
        self._buffer = buffer
        self._buffer_index = buffer_index
        self._row_count = row_count
        self.endResetModel()

    # Méthode pour récupérer l'index du buffer. ------------------------------------------------------------------------
    def get_real_index(self, logical_row):
        return (self._buffer_index - self._buffer_count + logical_row) % self._buffer_capacity


    # Méthode pour récupéper la ligne en cours. ------------------------------------------------------------------------
    def get_row_data(self, row):
        real_index = self.get_real_index(row)
        return self._buffer[real_index]

    # Méthode pour retourner le nombre de lignes. ----------------------------------------------------------------------
    def rowCount(self, parent=None):
       return self._row_count

    # Méthode pour retourner le nombre de colonnes. --------------------------------------------------------------------
    def columnCount(self, parent=None):
        return 3

    # Méthode pour retourner la donnée de la trame. --------------------------------------------------------------------
    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            # Obtenir l'indice réel dans l'ordre FIFO (en respectant l'ordre haut vers bas)
            real_index = self.get_real_index(index.row())
            trame = self._buffer[real_index]

            # Vérifier si la trame est valide (ne pas afficher les valeurs vides par défaut)
            if trame == ("", "", ""):
                return None

            # Retourner la donnée de la colonne correspondante
            return trame[index.column()]

        return None

    # Méthode pour retourner l'en-tête. --------------------------------------------------------------------------------
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                headers = ["ID", "Len", "Datas"]
                return headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None
# ************************************ FIN DE LA CLASSE TableModel *****************************************************


# ***************************************** FENETRE PRINCIAPALE ********************************************************
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__() # Lance la fenêtre
        self._file_path_csv = None
        self._reply = None
        self._selected_file_path = None
        self.loop = None
        uic.loadUi('Alain.ui', self)
        self._fenetre_status = None
        self._file_path = None
        self._can_interface = None
        self._handle = None
        self._status = None
        self._stop_flag = False
        self._fenetre_status = None

        # Initialisation des attributs d'instance dans le constructeur
        self.loop = None  # La boucle asyncio sera définie plus loin.

        # Définition des capicités par défaut des : Fichier bus CAN dans Fichier NMEA et taille du buffer tournant.
        self.line_nmea.setText("10000") # Taille pour enregistrer le NMEA 2000
        self.line_table.setText("5000") # Taille pour le buffer tournant

        # Crée l'instance des Classes
        self.setWindowIcon(QIcon("icones/ps2.png"))
        self._traitement_can = TempsReel()
        self._nmea_2000 = NMEA2000(self)
        self._can_interface = WindowsUSBCANInterface(self._stop_flag)

        # Instanciez CANApplication en lui passant les paramètres nécessaires
        self.can_interface_app = CANApplication(
            self,
            traitement_can=self._traitement_can,
            file_path=self._file_path,
            lab_trame=self.lab_trame,
            lab_connection=self.lab_connection,
            check_file=self.check_file,
            check_buffer=self.check_buffer,
            check_nmea=self.check_nmea,
            handle=None,
            actions={
                "actionOpen": self.actionOpen,
                "actionClose": self.actionClose,
                "actionRead": self.actionRead,
                "actionStop": self.actionStop,
                "actionStatus": self.actionStatus
            }
        )

        # table_can
        self.table_can: QTableView = self.findChild(QTableView, "table_can")

        # Variables pour le buffer tournant
        self._buffer_capacity = int(self.line_table.text())
        self._buffer_index = 0  # Position actuelle du buffer circulaire
        self._buffer_count = 0  # Nombre d'éléments actuellement remplis

        # Buffer initialisé avec des données vides.
        self._buffer = [("", "", "")] * self._buffer_capacity

        # Instanciation de notre TableModel
        self._model = TableModel(self._buffer, self._buffer_index, self._buffer_capacity)
        self.table_can.setModel(self._model)  # Lien entre le modèle et la table

        # Initialise la table.
        self.table_can.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_can.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_can.setModel(self._model)

        # Configurer les largeurs des colonnes
        self.configurer_colonnes()

        # Défini la méthode sur changement de ligne sur la table.
        # noinspection PyUnresolvedReferences
        self.table_can.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Appel des méthodes des objets widgets.
        self.check_file.stateChanged.connect(self.on_check_file_changed)
        self.table_can.clicked.connect(self.on_click_table)                 # Gestion du clic dans la table
        self.line_table.editingFinished.connect(self.on_change_buffer_size) # Modification de la taille du buffer

        # Appel des méthodes des menus.
        self.actionOuvrir.triggered.connect(self.on_click_file)
        self.actionImporter.triggered.connect(self.on_click_import)
        self.actionVoir.triggered.connect(self.on_click_voir)
        self.actionAbout.triggered.connect(self.show_about_box)
        self.actionExport.triggered.connect(self.on_click_Export)
        self.actionMap.triggered.connect(self.on_click_map)
        self.actionQuitter.triggered.connect(self.close_both)

        # Initialse les menus innacessibles.
        self.actionClose.setEnabled(False)
        self.actionRead.setEnabled(False)
        self.actionStop.setEnabled(False)
        self.actionImporter.setEnabled(False)
        self.actionVoir.setEnabled(False)
        self.actionExport.setEnabled(False)

    @property
    def nmea_2000(self):
        """Propriété pour accéder à NMEA2000."""
        return self._nmea_2000

    # ==================================== DEBUT DES METHODES LIEES A LA TABLE =========================================
    # Méthode pour configurer la taille des colonnes de la table. ------------------------------------------------------
    def configurer_colonnes(self):
        self.table_can.setColumnWidth(0, 80)  # Largeur de "ID"
        self.table_can.setColumnWidth(1, 30)  # Largeur de "Len"
        self.table_can.setColumnWidth(2, 180)  # Largeur de "Data"
        # Ouvre la table.
        self.show()

    # Méthode sur changement de ligne sur la table. --------------------------------------------------------------------
    def on_selection_changed(self):
        indexes = self.table_can.selectionModel().selectedRows()
        if indexes:  # Vérifier s'il y a une sélection active
            index = indexes[0]
            self.on_click_table(index)  # On va sur "on_click_table".

    # Méthode sur clique sur la table, elle est incluse sur méthode ci-dessus. -----------------------------------------
    def on_click_table(self, index: QModelIndex):
        model = self.table_can.model()  # Récupérer le modèle de la table
        ligne = index.row()  # Récupérer l'indice de la ligne cliquée

        if isinstance(model, TableModel):
            # Récupère directement les données de la ligne grâce aux méthodes publiques
            row_data = model.get_row_data(ligne)

            col1 = row_data[0]  # ID
            col2 = row_data[1]  # Longueur (Len)
            col3 = row_data[2]  # Données hexadécimales

            print(f"Ligne sélectionnée : {ligne}\n"
                  f"ID : {col1}\n"
                  f"Nb Octets : {col2}\n"
                  f"Datas : {col3}")
        else:
            # Logique par défaut si un modèle autre qu'un buffer circulaire est utilisé
            col1 = model.data(model.index(ligne, 0), Qt.DisplayRole)
            col2 = model.data(model.index(ligne, 1), Qt.DisplayRole)
            col3 = model.data(model.index(ligne, 2), Qt.DisplayRole)

            print(f"Ligne sélectionnée : {ligne}\n"
                  f"ID : {col1}\n"
                  f"Nb Octets : {col2}\n"
                  f"Datas : {col3}")

        col1= col1.strip()
        if not col1.startswith("0x"):
            col1 = f"0x{col1}"

        id_msg = int(col1, 16)
        tout_id = self._nmea_2000.id(id_msg)

        # Affiche le résultat des octets avec leurs définitions.
        if col3:
            data = col3.split(" ")
            try:
                # Récupère les informations des octets.
                octetstuple = self._nmea_2000.octets(int(tout_id[0]),[int(octet,16) for octet in data])
                # Affiche toutes les informations sur le formulaire.
                self.lab_octet.setText("                             Ligne " + str(ligne+1)       # Numéro de ligne
                               + "\n PGN : "+ " " + str(tout_id[0])                               # PGN
                               + "       Prio : " + str(tout_id[3])                               # Priorité
                               + "   Source : " +  str(tout_id[1])                                # Source
                               + "    Dest. : " + str(tout_id[2]) + "\n\n"                        # Destination
                               + " " + str(octetstuple[0]) + ": "                                 # PGN1
                               + " " + str(octetstuple[3]) + "\n"                                 # Valeur 1
                               + " " + str(octetstuple[1]) + ": " + str(octetstuple[4]) + "\n"    # PGN2 : Valeur 2
                               + " " + str(octetstuple[2]) + ": " + str(octetstuple[5]) + "\n"    # PGN3 : Valeur 3
                               + " Table : " + str(octetstuple[6]) + ": " +                       # Table :
                               str(octetstuple[7]))                                               # Définition
            except Exception as e:
                print(f"Erreur dans l'appel à octets : {e}")

    # Méthode pour remplir la table venant d'un fichier. ---------------------------------------------------------------
    def affiche_trame_fichier(self, trame):
        self.add_to_buffer(trame)

    # Méthode pour remplir la table avec le buffer tournant. -----------------------------------------------------------
    def add_to_buffer(self, trame):
        # Ajout de la trame dans le buffer circulaire
        self._buffer[self._buffer_index] = trame

        # Incrémentation de l'index dans une logique circulaire.
        self._buffer_index = (self._buffer_index + 1) % self._buffer_capacity

        # Mise à jour du nombre de lignes si le buffer n'est pas encore rempli.
        if self._buffer_count < self._buffer_capacity:
            self._buffer_count += 1

        # Mise à jour de la table pour refléter les changements.
        self._model.update_buffer(self._buffer, self._buffer_index, self._buffer_count)

    # Méthode pour changement de la valeur de la capacité du buffer. ---------------------------------------------------
    def on_change_buffer_size(self):
        try:
            # Validation de la nouvelle taille
            new_size = int(self.line_table.text())
            if new_size <= 0:
                raise ValueError("La taille doit être supérieure à zéro.")

            # Réinitialise le buffer avec la nouvelle capacité
            self._buffer_capacity = new_size
            self._buffer = [("", "", "")] * self._buffer_capacity
            self._buffer_index = 0
            self._buffer_count = 0

            # Réinitialisation de la table
            self._model.update_buffer(self._buffer, self._buffer_index, self._buffer_count)

        except ValueError:
            # Gère les erreurs en affichant un message
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une taille valide (entier positif).")
            # Réinitialise la valeur précédente
            self.line_table.setText(str(self._buffer_capacity))
    # ================================ FIN DES METHODES LIEES A LA TABLE ===============================================


    # ============================== DEBUT DES METHODES LIEES A L'APPLICATION ==========================================
    # Méthode sur fermeture de la fenêtre sur événemnt. ----------------------------------------------------------------
    def closeEvent(self, event):
        # Appelle la méthode `close_both` pour gérer la fermeture proprement
        self.close_both()
        # Accepte l'événement pour continuer la fermeture
        event.accept()

    # Métode sur l'action sur le menu Quitter, on ferme tous. ----------------------------------------------------------
    def close_both(self):
        # self.on_click_stop()
        print("Fermeture des fenêtres...")
        # Fermer FenetreStatus si elle est ouverte
        self.can_interface_app.fermer_fenetre_status()
        print("La fenêtre est fermée")

        # Fermer la fenêtre principale.
        self.can_interface_app.on_click_close()
        print("Fermeture de la fenêtre principale")
        self.close()

    # Méthode sur la case à cocher. ------------------------------------------------------------------------------------
    def on_check_file_changed(self,state) :
        if state == Qt.Checked:
            if not self._file_path:
                QMessageBox.information(self, "ENREGISTREMENT",
                                        "Veuillez ouvrir un fichier avant de pouvoir l'enregistrer.")
                # Remet la case à False.
                self.check_file.setChecked(False)
        return self.check_file

    # Méthode pour voir le fichier prêt à enregister sur bus CAN en mode bloc-notes. -----------------------------------
    def on_click_voir(self):
        if self._file_path:
            if os.path.exists(self._file_path):
                subprocess.Popen(["notepad.exe", self._file_path])
        else:
            QMessageBox.information(self, "VOIR", "Veuillez ouvrir un fichier avant de le voir sur le bloc notes.")

    # Méthode pour ouvrir le fichier texte prêt à l'enregistrement. ----------------------------------------------------
    def on_click_file(self) -> os.path:
        self.setCursor(Qt.WaitCursor)
        __previous_file_path = self._file_path

        # Boîte de dialogue pour sélectionner un fichier ou en définir un nouveau
        selected_file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Créer un Fichier texte pour récupérer les trame du bus CAN",  # Titre de la boîte de dialogue
            self._file_path if self._file_path else ""
            ,  # Dossier initial
            "Fichier texte (*.txt);;Tous les fichiers (*.*)")

        if selected_file_path:
            self._file_path = selected_file_path
            # Si le fichier n'existe pas, le créer
            if not os.path.exists(self._file_path):
                with open(self._file_path, "w") as file:
                    file.write("")  # Crée un fichier vide
                print(f"Fichier créé : {self._file_path}")
                self.lab_file.setText(str(self._file_path))
            else:
                print(f"Fichier ouvert : {self._file_path}")
                self.lab_file.setText("Bus CAN     : " + str(self._file_path))

            self.actionImporter.setEnabled(True)
            self.actionVoir.setEnabled(True)
            self.actionExport.setEnabled(True)

        else:
            self._file_path = __previous_file_path
            print("Aucun fichier sélectionné.")

        self.unsetCursor()



    # Méthode pour importer les données du fichier sur la table. -------------------------------------------------------
    def on_click_import(self):
        if not self._file_path:
            QMessageBox.information(self, "IMPORTER LE FICHIER",
                                    "Veuillez ouvrir un fichier avant de l'importer sur la table.")
            return None

        # On défini la quantité de trames
        quantite = int(self.line_table.text())
        start_index = 0

        resultat = self.Qmessagebox_4_boutons( "Importer dans la table",
                                                  "Vous allez importer dans la table",
                                                  start_index,
                                                  "Précédent",
                                                  "Suivant",
                                                  "Valider",
                                                  quantite)

        if resultat is None:
            print("La boîte de dialogue a été fermée sans action (bouton 'X').")
            return
        else:
            print(f"L'importation commence à l'index : {resultat}")
            start_index = resultat

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            liste_tuples = []
            with open(self._file_path, 'r', encoding='utf-8', errors='replace') as fichier:
                for i, ligne in enumerate(fichier):
                    # Saute les lignes avant le `start_index`
                    if i < start_index:
                        continue

                    # Lire jusqu'à la quantité de lignes à partir de `start_index`
                    if i >= start_index + quantite:
                        break

                    # Supprimer les espaces inutiles.
                    ligne = ligne.strip()

                    # Défini l'espace comme séparateur.
                    valeurs = ligne.split(' ')

                    # Convertit la liste des valeurs en tuple.
                    ligne_tuple = tuple(valeurs)

                    # Ajoute le tuple à la liste.
                    liste_tuples.append(ligne_tuple)

            # Transformer la liste pour afficher seulement les colonnes souhaitées.
            # Les valeurs dans la table sont déjà en hexadécimales.
            liste_modifiee = [
                (
                    t[1] if len(t) > 1 else '',  # 2e élément ID
                    t[2] if len(t) > 2 else '',  # 3e élément Len
                    ' '.join(t[3:]) if len(t) > 3 else ''  # 4e élément Data avec join.
                )
                for t in liste_tuples
            ]

            # Appeler la fonction pour afficher les trames une par une.
            for trame in liste_modifiee:
                self.affiche_trame_fichier(trame)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de l'importation : {str(e)}")

        finally:
            QApplication.restoreOverrideCursor()

    # Méthode pour exporter le fichier texte vers le fichier NMEA 2000 en CSV. -----------------------------------------
    def on_click_Export(self):
        if not self._file_path_csv:
            # Récupérer le chemin du fichier où sauvegarder le CSV.
            self._file_path_csv, _ = QFileDialog.getSaveFileName(self,
                                                  "Créer un fichier CSV pour y inclure le NMEA 2000",
                                                  # Titre de la boîte de dialogue
                                                  "",  # Chemin initial vide
                                                  "Fichier csv (*.csv);;Tous les fichiers (*.*)")
        else:
            self._reply = QMessageBox.question(self, "EXPORTER LE FICHIER EN NMEA 2000",
                                               f"Voulez-vous créer un autre fichier CSV ?\n"
                                               f"Ou travailler avec celui-ci : {self._file_path_csv}")
            if self._reply == QMessageBox.Yes:
                # Récupérer le chemin du fichier où sauvegarder le CSV.
                self._file_path_csv, _ = QFileDialog.getSaveFileName(self,
                                                  "Créer un nouveau fichier CSV pour y inclure le NMEA 2000",
                                                  # Titre de la boîte de dialogue
                                                  "",  # Chemin initial vide
                                                  "Fichier csv (*.csv);;Tous les fichiers (*.*)")


        if not self._file_path_csv:
            return
        else:
            self.lab_csv.setText("NMEA 2000 : " + str(self._file_path_csv))

        nombre_lignes = int(self.line_nmea.text())  # C'est ici qu'on définit la taille du fichier NMEA 2000.

        # Récupérer le start_index à partir de la méthode de gestion des quatre boutons
        start_index = self.Qmessagebox_4_boutons("Exporter NMEA 2000",
                                                 f"Vous allez exporter dans le fichier "
                                                 f"{os.path.basename(self._file_path_csv)} en NMEA 2000",
                                                 0,
                                                 "Précédent",
                                                 "Suivant",
                                                 "Valider",
                                                 nombre_lignes)

        if start_index is None:
            print("La boîte de dialogue a été fermée sans action (bouton 'X').")
            return

        try:
            # Ouvrir le fichier source texte.
            with open(self._file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                # Lire toutes les lignes du fichier
                lignes = f.readlines()

            # Ignorer les lignes avant le `start_index` et limiter à nombre les lignes
            lignes_restees = lignes[start_index:start_index + nombre_lignes]

            # Transformer les lignes en données structurées
            resultat = (ligne.strip().split(" ") for ligne in lignes_restees if ligne.strip())

            # Ouvrir le fichier CSV pour écrire les résultats
            with open(self._file_path_csv, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')

                # Écrire l'en-tête du fichier CSV
                writer.writerow(("PGN", "Source","Destination", "Priorité","PGN1", "Valeur", "PGN2",
                                 "Valeur", "PGN3", "Valeur", "Table", "Définition"))

                for index, ligne in enumerate(resultat):
                    try:
                        # Vérifier que la ligne contient suffisamment de données
                        if len(ligne) < 1:
                            print(f"Données insuffisantes à l'index {index} : {ligne}")
                            continue

                        # Convertir et traiter les champs de la ligne avec la méthode _nmea_2000.pgn
                        pgn = self._nmea_2000.pgn(int(ligne[1], 16))  # Conversion hexadécimal -> entier

                        # Récupèrer la source
                        source = self._nmea_2000.source(int(ligne[1], 16))

                        # Récupèrer la destination
                        destination = self._nmea_2000.destination(int(ligne[1], 16))

                        # Récupèrer la priorité
                        priorite = self._nmea_2000.priorite(int(ligne[1], 16))

                        # Récupère la zone data qui est mise dans les colonnes 3 à 10
                        data = (ligne[i].strip() for i in range(3, 11) if i < len(ligne))

                        # Convertir les octets avec la méthode `_nmea_2000. octets`
                        result = self._nmea_2000.octets(pgn, [int(octet, 16) for octet in data])

                        # Écrire les résultats dans CSV sous forme d'un tuple.
                        writer.writerow((
                            pgn,        # Affiche PGN, Source, Destination, Priorité.
                            source,
                            destination,
                            priorite,
                            result[0],  # PGN1, Ces resultats viennent du tuple NMEA 2000.
                            result[3],  # Valeur1
                            result[1],  # PGN2
                            result[4],  # Valeur2
                            result[2],  # PGN3
                            result[5],  # Valeur3
                            result[6],  # Table
                            result[7]   # Définition de la table.
                        ))

                    except ValueError as ve:
                        print(f"Erreur de conversion à l'index {index} : {ligne}, Erreur : {ve}")
                    except Exception as ex:
                        print(f"Erreur inattendue à l'index {index} : {ex}")

            QMessageBox.information(self, "EXPORT CSV EN NMEA 2000", f"Exportation NMEA 2000 dans le fichier "
                                                        f"{os.path.basename(self._file_path_csv)} "
                                                        f"est terminée avec succès !\n"
                                                        f"Allez voir le fichier "
                                                        f"{os.path.basename(self._file_path_csv)}"
                                                        f" oû vous avez le résultat.")

        except FileNotFoundError:
            QMessageBox.critical(self, "EXPORT CSV EN NMEA 2000", "Fichier source introuvable ou non spécifié.")
        except Exception as e :
            print(f"Erreur inattendue : {e}")
            QMessageBox.critical(self, "EXPORT CSV", "Le fichier est dèjà ouvert!")

    # Méthode qui lance la "quart_app" ---------------------------------------------------------------------------------
    @staticmethod
    async def lancer_flask():
        """Lance le serveur Quart dans une boucle asyncio."""
        print("Démarrage du serveur Quart...")

        try:
            # S'assurer que quart_app est bien défini
            if quart_app is None:
                raise RuntimeError("quart_app n'est pas défini. Assurez-vous de l'initialiser correctement.")

            # Lancer le serveur Quart
            await quart_app.run_task(host="127.0.0.1", port=5001)

        except Exception as e:
            print(f"Erreur lors du démarrage du serveur Quart: {e}")

    # Méthode qui appelle "lancer_flask" en asynchtone -----------------------------------------------------------------
    def on_click_map(self) -> None:
        """Méthode pour lancer la tâche Flask et ouvrir la carte."""
        print("Bouton 'Map' cliqué !")

        # Lancer Flask comme une tâche asyncio
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        if not self.loop.is_running():
            print("Lancement de la boucle asyncio pour Quart...")
            self.loop.run_until_complete(self.lancer_flask())
        else:
            print("Boucle asyncio déjà en cours, ajout de Flask en tant que tâche...")
            # Lancer Flask dans la boucle en parallèle
            asyncio.ensure_future(self.lancer_flask())

        # Ouvrir la carte dans le navigateur
        webbrowser.open("http://127.0.0.1:5001/map")

    # Méthode appelée quand on a les coordonnées (toutes les 1/10 de scrutation) ---------------------------------------------
    @staticmethod
    async def update_coordinates(latitude, longitude):
        """Met à jour les coordonnées dans les variables globales."""
        global coordinates
        coordinates["latitude"] = latitude
        coordinates["longitude"] = longitude
        print(f"Coordonnées mises à jour : latitude={latitude}, longitude={longitude}")

    # Méthode pour avoir quatre boutons personalisés, qui sont le précédent, le suivant, valider et annuler ------------
    @staticmethod
    def Qmessagebox_4_boutons(titre="Importer",info="information",
                              start_index=None,
                              premier="Précedent",
                              deuxieme="Suivant",
                              troisieme = "Valider",
                              quantite = 5000):

        # Ce bouton n'a pas besoin d'être instancié.
        quatrieme = "Annuler"

        # Création du QMessageBox avec quatre boutons définis par l'utilisateur.
        try:
            msg_box = QMessageBox()
            msg_box.setWindowTitle(titre)
            msg_box.setWindowIcon(QIcon("icones/ps2.png"))

            # Ajout des quatre boutons personalisés.
            bouton_oui = msg_box.addButton(premier, QMessageBox.ActionRole)
            bouton_non = msg_box.addButton(deuxieme, QMessageBox.ActionRole)
            bouton_valider = msg_box.addButton(troisieme, QMessageBox.ActionRole)
            bouton_annuler = msg_box.addButton(quatrieme, QMessageBox.ActionRole)

            # Mettre le focus par défaut sur le 'Valider'
            msg_box.setDefaultButton(bouton_valider)

            continuer = True
            while continuer:
                msg_box.setText(f"{info}, les numéros des lignes de: {start_index + 1} à {start_index + quantite}")
                # Affichage de la boîte de dialogue.
                msg_box.exec_()

                # Détection du bouton 'Annuler'
                if msg_box.clickedButton() == bouton_annuler:
                    print("L'utilisateur a annulé la boîte de dialogue.")
                    return None

                # Détection du bouton cliqué
                if msg_box.clickedButton() == bouton_non:
                    start_index += quantite
                elif msg_box.clickedButton() == bouton_oui:
                    start_index = max(0, start_index - quantite)
                elif msg_box.clickedButton() == bouton_valider:
                    print(f"Vous avez validé l'importation des lignes {start_index + 1} à {start_index + quantite}.")
                    continuer = False

            return start_index

        except Exception as e:
            print("Erreur", f"Une erreur s'est produite lors de l'importation : {str(e)}")
            return None

    # Méthode ABOUT. ---------------------------------------------------------------------------------------------------
    @staticmethod
    def show_about_box()-> None:
        # Crée une boîte de dialogue "À propos"
            about_box = QMessageBox()
            about_box.setWindowTitle("À propos de l'application")
            about_box.setWindowIcon(QIcon("icones/ps2.png"))
            about_box.setText(
                "<h3>Application Huahine</h3>"
                "<p>Version 1.0</p>"
                "<p>© 2025 Alain Malvoisin</p>"
                "<p>Ceci est une application qui se connecte sur le bus CAN,</p>" 
                "et décode les trames en NMEA 2000."
            )
            about_box.setIcon(QMessageBox.Information)

            # Affiche la boîte de dialogue
            about_box.exec_()
# ======================================= FIN DES METHODES =============================================================


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Intégration asyncio avec PyQt5
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()

    # Intégration avec la boucle PyQt5
    with loop:
        loop.run_forever()