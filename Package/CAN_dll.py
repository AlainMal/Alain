import ctypes
from ctypes import Structure, c_ubyte,c_long, c_int, POINTER, Array

class CanData(Array):
    _type_ = c_ubyte
    _length_ = 8


class CanMsg(Structure):
    _fields_ = (
        ("ID", c_long),
        ("TimeStamp", c_long),
        ("flags", c_ubyte),
        ("len", c_ubyte),
        ("data", CanData)
    )

# Défini les fonctions de la dll.
class CanError(Exception):
    pass

# ================================================== Classe Interface dll ==============================================
class CANDll:
    def __init__(self, stop_flag):
        self._etat = None
        self._msg = None
        self._stop_flag = stop_flag

        # Charger la DLL
        try:
            self._dll = ctypes.WinDLL("canusbdrv64.dll")
        except (OSError, FileNotFoundError) as err:
            print("Erreur DLL:", err)
            raise CanError

        # =============== DEFINITION DES FONCTIONS INTERFACE DLL ======================
        #
        # Fonction OPEN
        self._dll.canusb_Open.restype = c_long  # Type de retour : entier long
        # Fonction CLOSE
        self._dll.canusb_Close.argtypes = [c_long]
        # Fonction READ
        self._dll.canusb_Read.argtypes = [c_long, POINTER(CanMsg)]
        self._dll.canusb_Read.restype = c_int
        # Fonction STATUS
        self._dll.canusb_Status.restype = c_int
        # Il y en a d'autres, mais pour l'instant ne sont pas utiles

        self._handle = None

    # Méthode d'ouverture de l'adaptateur. Cette fonction est appelé par le bouton "OPEN".------------------------------
    def open(self, bitrate, acceptance_code, acceptance_mask, flags):
        # Ouvre l'adapateur et retourne son instance.
        self._handle = self._dll.canusb_Open(None, bitrate, acceptance_code, acceptance_mask, flags)
        if self._handle is None:
            raise CanError("Erreur ouverture canal CAN")
        else:
            return self._handle     # Retourne le handle dont on a besoin pour savoir si c'est ouvert

    # Méthode de lecture des trames du bus CAN en asychrone.------------------------------------------------------------
    def read_dll(self, stop_flag) -> CanMsg:       # Retourne un pointeur sur le CanMsg
        if self._handle is None:
           raise CanError("Channel not open")

        self._msg = CanMsg()     # Défini le format

        # Boucle pour attendre les trames CAN.
        while not stop_flag:
            if self._handle is None:
                self._handle = 0    # Marquer le handle en entier comme inactif

            if stop_flag:
                return self._msg

            result = self._dll.canusb_Read( self._handle,ctypes.byref(self._msg))

            # Résultat du CAN : on sort si une trame a été reçue : result == 1.
            # Sinon il a des valeurs négatives qui représente différent défaut,
            # dont le -7 qui indtque qu'il n'a pas reçu de tramrs.
            if result <= -2 and result != -7:
                # On ne traite pas les défauts, mais on le signale.
                print("Défaut CAN : ", str(result))
                # Affiche la fenêtre Status
                # main_window.on_click_status()

            if result == 1: # C'est qu'on a reçu un msg.
                break

        # Une fois une trame reçue, on la retourne
        return self._msg  # Retourne le CanMsg dont on aura besoin pour l'enregistrer

    # Méthode de fermeture de l'adaptateur. ----------------------------------------------------------------------------
    def close(self):
        if self._handle is not None:
            self._dll.canusb_Close(self._handle)
            self._handle = None

    # Méthode de lecture du status de l'adaptateur. --------------------------------------------------------------------
    def status(self):
        self._etat = self._dll.canusb_Status(self._handle)
        return self._etat
 # =====================================================================================================================