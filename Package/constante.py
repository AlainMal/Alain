
# Variables systèmes sur PC
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

# Constante pour initialiser le bus CAN
CAN_BAUD_250K = b"250"
CANUSB_ACCEPTANCE_CODE_ALL = 0x0
CANUSB_ACCEPTANCE_MASK_ALL = 0xFFFFFFFF
FLUSH_WAIT = 0x0
FLUSH_DONTWAIT = 0x1
CANUSB_FLAG_TIMESTAMP = 0x1

# Résulltat des Read et Write
CANSTATUS_NO_ERROR = 0x0
CANSTATUS_RECEIVE_FIFO_FULL = 0x1
CANSTATUS_TRANSMIT_FIFO_FULL = 0x2
CANSTATUS_ERROR_WARNING = 0x4
CANSTATUS_DATA_OVERRUN = 0x8
CANSTATUS_ERROR_PASSIVE = 0x20
CANSTATUS_ARBITRATION_LOST = 0x40
CANSTATUS_BUS_ERROR = 0x80

# Liste des PGN nécésitant la mise en mémoire
PGN_129038 = 0
PGN_129039 = 1
PGN_129049 = 2
PGN_127506 = 3
PGN_126464 = 4
# Liste à compléter...

# Liste des huits octets
MEMOIRE_PGN_a0 = 0
MEMOIRE_PGN_a1 = 1
MEMOIRE_PGN_a2 = 2
MEMOIRE_PGN_a3 = 3
MEMOIRE_PGN_a4 = 4
MEMOIRE_PGN_a5 = 5
MEMOIRE_PGN_a6 = 6
MEMOIRE_PGN_a7 = 7

# ------------------------- Dictionnaire des significations des valeurs reçues dans les tables --------------------------------------
# Table des températures.
TEMPERATURE = {
0:	"Température de la mer",
1:	"Température extérieure",
2:	"Température intérieure",
3:	"Température de la salle des machines",
4:	"Température de la cabine principale",
5:	"Température du vivier",
6:	"Température du puits d’appât",
7:	"Température de réfrigération",
8:	"Température du système de chauffage",
9:	"Température du point de rosée",
10:	"Température apparente de refroidissement éolien",
11:	"Température théorique de refroidissement éolien",
12:	"Indice de chaleur Température",
13:	"Température du congélateur",
14:	"Température des gaz d’échappement",
15:	"Température du joint d’arbre"
}

# Table des vents.
VENT = {
    0: "Vent Ground",
    1: "Vent Magnétique",
    2: "Vent Apparent",
    3: "Vent Vrai Fond",
    4: "Vent Vrai"
}

# Table des vitesses sur l'eau.
WATER_SPEED ={
0:	"Roue à aubes",
1:	"Tube de Pitot",
2:	"Doppler",
3:	"Corrélation (ultrasons)",
4:	"Électromagnétique"
}

# Table des niveaux des réservoirs.
RESERVOIR = {
0:	"Combustible",
1:	"Eau",
2:	"Eaux grises",
3:	"Bien vivre",
4:	"Huile",
5:	"Eaux noires"
}

# Table des pressions.
PRESSION ={
0:	"Atmosphérique",
1:	"Eau",
2:	"Vapeur",
3:	"Air comprimé",
4:	"Hydraulique",
5:	"Filtre",
6:	"AltimètreRéglage",
7:	"Huile",
8:	"Combustible"
}

# Table de l'XTE.
MODE_XTE ={
0:	"Autonome",
1:	"Différentiel amélioré",
2:	"Estimatif",
3:	"Simulateur",
4:	"Manuelle"
}

# Table de source d'energie.
ENERGIE_DC ={
0:	"Batterie",
1:	"Alternateur",
2:	"Convertisseur",
3:	"Cellule photovoltaïque",
4:	"Aérogénérateur"
}

# A compléter...
