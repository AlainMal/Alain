import asyncio
import os

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox,QMainWindow, QTreeWidget, QTreeWidgetItem
from PyQt5.QtGui import QIcon

from Package.constante import *
from Package.CAN_dll import WindowsUSBCANInterface

# ****************************************** CLASSE POUR LA LECTURE DU BUS CAN *****************************************
class CANApplication(QMainWindow):
    # Tous les paramètres sont défini dans la classe MainWindow sur HUAHINE.py
    def __init__(self, main_window,traitement_can, file_path, lab_trame, lab_connection, check_file, check_buffer, check_nmea,
                 handle,actions=None):
        super().__init__()

        # Attribuez les actions si elles sont transmises
        self.actions = actions or {}
        self._main_window = main_window
        # Initialisez les attributs nécessaires ici
        self._fenetre_status = None
        self._status = None
        self._stop_flag = False  # Initialisation du flag stop
        self._can_interface = None
        self._traitement_can = traitement_can

        # Construire le chemin relatif vers Alain.ui (qui est dans le répertoire parent)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(current_dir, "..", "Alain.ui")
        # Charger le fichier .ui
        uic.loadUi(ui_path, self)

        self._can_interface = WindowsUSBCANInterface(self._stop_flag)

        # Gestion des tâches asynchrones et état
        self._handle = handle  # Handle CAN
        self._stop_flag = False  # Drapeau pour arrêter les boucles
        self.loop = None  # Boucle asyncio
        self.task = None  # Gestionnaire de la tâche principale

        # Composants CAN et gestion des fichiers
        self._traitement_can = traitement_can
        self._file_path = file_path

        # GUI widgets (passés à l'initialisation)
        self.lab_trame = lab_trame
        self.lab_connection = lab_connection
        self.check_file = check_file
        self.check_buffer = check_buffer
        self.check_nmea = check_nmea

        # Connecter les actions aux méthodes locales
        if self.actions.get("actionOpen"):
            self.actions["actionOpen"].triggered.connect(self.on_click_open)
        if self.actions.get("actionClose"):
            self.actions["actionClose"].triggered.connect(self.on_click_close)
        if self.actions.get("actionRead"):
            self.actions["actionRead"].triggered.connect(self.on_click_read)
        if self.actions.get("actionStop"):
            self.actions["actionStop"].triggered.connect(self.on_click_stop)
        if self.actions.get("actionStatus"):
            self.actions["actionStatus"].triggered.connect(self.on_click_status)

    # Méthode pour lire le bus CAN -------------------------------------------------------------------------------------
    async def read(self):
        print("On est entré dans la boucle de lecture.")
        self.lab_connection.setText("") # Initialise le texte
        n = 0

        self._stop_flag = False
        while not self._stop_flag:
            try:
                # Lecture bloquante déplacée dans un thread, avec un timeout
                msg = await asyncio.wait_for(
                    asyncio.to_thread(self._can_interface.read, self._stop_flag),
                    timeout=1.0
                )

                if msg:  # Si une trame est reçue
                    n += 1
                    self.lab_trame.setText(str(n))  # Mise à jour du nombre de trames reçues.

                    # Appeler la méthode du traitement en TempsReel.
                    await self._traitement_can.TempsReel(
                        msg,
                        self._file_path,
                        self.check_file.isChecked(),
                        self.check_buffer.isChecked(),
                        self.check_nmea.isChecked(),
                        self._main_window) # On lui fait passer le MainWindow()

                self.update_action_states(open_enabled=False,
                                          read_enabled=False,
                                          close_enabled=True,
                                          stop_enabled=True)

            except asyncio.TimeoutError:
                print("Aucune trame reçue depuis 1 seconde... Arrêt en cours.")
                self._stop_flag = True  # Arrêter la boucle si dépassement de temps
                self.lab_connection.setText("Il n'y a pas de trame arrivée.\nVérifiez que vous êtes bien raccordé. ")

            except Exception as e:
                print(f"Erreur pendant la lecture CAN : {e}")
                print(f"actionOpen attachée à : {self.actionOpen.associatedWidgets()}")

        print("Tâche read() terminée.")

    # Méthode pour lancer le Read de manière asynchrone ----------------------------------------------------------------
    async def main(self):
        """Méthode principale pour exécuter read()."""
        try:
            # Lancer la tâche principale et lire les données CAN
            await self.read()
        except asyncio.CancelledError:
            print("Tâche annulée proprement.")
        finally:
            print("Tâches principales terminées.")

    # Méthode pour mettre en Run les taches asyncrhones ----------------------------------------------------------------
    async def run(self):
        """Méthode qui initialise et exécute main."""
        self._stop_flag = False
        try:
            # Vérifie si le handle est valide
            if self._handle == 256:
                self.task = asyncio.create_task(self.main())
                await self.task
        except asyncio.CancelledError:
            print("Tâche annulée dans `run`.")
        finally:
            print("Tâche `run()` terminée.")

    # Méthode pour arrêter toutes les taches asynchrone ----------------------------------------------------------------
    async def stop(self):
        """Arrêter proprement toutes les tâches et la lecture CAN."""
        print("Arrêt des tâches demandé...")
        self._stop_flag = True  # Interrompre la boucle `read`

        if self.task:
            self.task.cancel()  # Annulation explicite de la tâche
            try:
                await self.task
            except asyncio.CancelledError:
                print("Tâche interrompue proprement.")
        print("Toutes les tâches ont été arrêtées.")

    # Méthode du bouton Read, mêt le fonction "run()" asynchone en route -----------------------------------------------
    def on_click_read(self) -> None:
        print("On est renté dans on_click_read")
        self.loop = asyncio.get_event_loop()
        if self.loop.is_running():  # Si une boucle tourne déjà
            print("Boucle existante détectée, dans le clique sur bouton read...")
            asyncio.ensure_future(self.run())  # Lancer en arrière-plan
        else:
            print("Lancement d'une nouvelle boucle avec run_until_complete...")
            self.loop.run_until_complete(self.run())  # Exécuter la tâche immédiatement

    # Méthode pour arrêter la lecture ----------------------------------------------------------------------------------
    def on_click_stop(self):
        print("C'est Arrêté ...")
        self.lab_connection.setText("")
        self.update_action_states(open_enabled=False,
                                  read_enabled=True,
                                  close_enabled=True,
                                  stop_enabled=False)

        self._stop_flag = True

    # Méthode pour ouvrir l'adaptateur CANUSB. -------------------------------------------------------------------------
    def on_click_open(self) -> int:
        print("C'est ouvert ...........")
        self.setCursor(Qt.WaitCursor)
        # Appelle cette fonction de manière explicite et la fait passer sur "interface".
        self._handle = self._can_interface.open(CAN_BAUD_250K,
                                                CANUSB_ACCEPTANCE_CODE_ALL,
                                                CANUSB_ACCEPTANCE_MASK_ALL,
                                                CANUSB_FLAG_TIMESTAMP)
        print(f"Résultat de l'appel : {self._handle}")
        if self._handle:  # Si l'adaptateur est ouvert.
            self.update_action_states(open_enabled=False,
                                      read_enabled=True,
                                      close_enabled=True,
                                      stop_enabled=False)
            print("C'est ouvert ...........")
        else:
            QMessageBox.information(self, "OUVERTURE DE L'ADAPTATEUR!",
                                    "Vérifiez que vous avez bien raccordé l'adapateur du bus CAN sur l'USB .")

        self.unsetCursor()
        return self._handle

    # Méthode pour fermer l'adaptateur. --------------------------------------------------------------------------------
    def on_click_close(self) -> None:
        self.setCursor(Qt.WaitCursor)
        self._stop_flag = True
        if self._handle == 256:
            self._can_interface.close()  # Ferme l'adaptateur
            print("C'est complétemet arrêté, sur le bouton de fermeture")
            # Met les boutons dans l'état voulu
            self.update_action_states(open_enabled=True,
                                      read_enabled=False,
                                      close_enabled=False,
                                      stop_enabled=False)
            self._handle = None

        self.lab_connection.setText("")
        self.unsetCursor()
        return None

    def on_click_status(self):
        try:
            self._status = self._can_interface.status()
            print("STATUS = " + str(self._status))
            # Crée la fenêtre `$FenetreStatus` avec une référence vers la fenêtre principale (passée dans "self.main_window")
            self._fenetre_status = FenetreStatus(self._status, self._main_window)
            # Afficher la fenêtre des Status
            self._fenetre_status.show()
            self._fenetre_status.align_with_main_window()

        except Exception as e:
            print(f"Erreur lors de l'ouverture de la fenêtre Status : {e}")

    # Méthode qui ferme la feneêtre Status -----------------------------------------------------------------------------
    def fermer_fenetre_status(self):
        """Méthode pour fermer la fenêtre de statut"""
        if self._fenetre_status:  # Vérifiez si la fenêtre existe
            self._fenetre_status.close()  # Fermez la fenêtre
            self._fenetre_status = None  # Réinitialisez la référence

    # Méthode qui active ou désactive les boutons ----------------------------------------------------------------------
    def update_action_states(self, open_enabled=False,
                             read_enabled=False,
                             close_enabled=False,
                             stop_enabled=False):
        # print(f"update_action_states: read_enabled={read_enabled}")
        self.actions["actionRead"].setEnabled(read_enabled)
        self.actions["actionClose"].setEnabled(close_enabled)
        self.actions["actionStop"].setEnabled(stop_enabled)
        self.actions["actionOpen"].setEnabled(open_enabled)

# *************************************** FIN DE LA CLASSE DE LECTURE **************************************************


# ************************************ FENETRE DU STATUS ***************************************************************
class FenetreStatus(QMainWindow):
    def __init__(self, status,main_window=None):
        super(FenetreStatus, self).__init__()
        self._main_window = main_window  # Référence à la fenêtre principale pour alignement

        print("Entrer dans la fenêtre Status")
        self._status = status
        self.setFixedSize(290, 230)
        self.setWindowTitle("Statuts")

        self.setWindowIcon(QIcon("icones/ps2.png"))

        # Création du QTreeWidget
        self._treewidget = QTreeWidget(self)
        self._treewidget.setColumnCount(2)
        self._treewidget.setHeaderLabels(["Désignations", "Etats"])
        self.setCentralWidget(self._treewidget)

        self._treewidget.setColumnWidth(0, 230)  # Définit la largeur de la première colonne à 200 pixels
        self._treewidget.setColumnWidth(1, 7)

        # Remplir le TreeWidget.
        self.remplir_treewidget()

    # ======================================= DEBUT DES METHODES STATUS ================================================
    def align_with_main_window(self):
        if self._main_window:
            # Récupérer les coordonnées de frameGeometry de la fenêtre principale
            main_geometry = self._main_window.frameGeometry()

            # Calculer les coordonnées pour FenetreStatus (en haut et à droite)
            new_x = main_geometry.x() + main_geometry.width() + 10
            new_y = main_geometry.y()

            # Déplacer la fenêtre FenetreStatus
            self.move(new_x, new_y)

    # Méthode pour remplir la TreeView ---------------------------------------------------------------------------------
    def remplir_treewidget(self):
        # La liste des différents défauts.
        status_data = (
            ("Pas de défaut", "CANSTATUS_NO_ERROR"),
            ("Buffer de réception plein", "CANSTATUS_RECEIVE_FIFO_FULL"),
            ("Buffer de transmission plein", "CANSTATUS_TRANSMIT_FIFO_FULL"),
            ("Avertissement erreur", "CANSTATUS_ERROR_WARNING"),
            ("Surcharge des Données", "CANSTATUS_DATA_OVERRUN"),
            ("Erreur passive", "CANSTATUS_ERROR_PASSIVE"),
            ("Défaut d'arbitrage", "CANSTATUS_ARBITRATION_LOST"),
            ("Erreur sur le bus", "CANSTATUS_BUS_ERROR"))

        # Vérifiez que le widget TreeWidget existe.
        if self._treewidget:
            # Parcourir les données et insérer dans le TreeWidget.
            for index, element in enumerate(status_data):
                designation = element[0]
                colonne_2 = "X" if (self._status == 0 and index == 0) else ""

                # Ajouter l'élément dans le TreeWidget.
                item = QTreeWidgetItem([designation, colonne_2])
                self._treewidget.addTopLevelItem(item)

            print("TREEWIDGET REMPLI")
# *************************************** FIN DE LA FENETRE STATUS *****************************************************