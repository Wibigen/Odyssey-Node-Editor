# Appeler et hooker des fonctions du jeu

Cliquez sur **Fonction du jeu…** (Ctrl+Maj+F) pour chercher dans le catalogue des fonctions de Super Mario Odyssey.

## Le navigateur

* Tapez une partie d'un nom, d'une classe ou d'une description. Les catégories à gauche réduisent la liste.
* Sélectionnez une fonction pour voir sa **signature, son type de retour, son offset et son symbole**.
* L'étoile ☆ marque les **favoris** ; **Ouvrir sur GitHub** lance une recherche dans OdysseyDecomp (utile pour lire ce qu'elle fait vraiment).

## Appeler ou hooker ?

| | **Appeler cette fonction depuis mon mod** | **Hooker cette fonction** |
|---|---|---|
| Sens | *Mon graphe appelle cette fonction du jeu* | *Quand le jeu l'appelle, mon graphe s'exécute* |
| Nœud | Un nœud dans votre flux | Un nœud d'entrée rouge (sans entrée) |
| Usage typique | `al::setPos(actor, …)`, `kill`, lire une valeur | Exécuter votre code à chaque image, à un coup, à un ramassage |

### Arguments d'un appel

Chaque argument est soit **Connecter un nœud** (relier une valeur), soit une **Valeur fixe** : un nombre, du texte, un bool, un `Vector3` (champs X/Y/Z) ou n'importe quelle expression C++.

### Résultat

Un appel qui renvoie une valeur peut **l'enregistrer dans une variable** (nommez-la dans l'inspecteur) ou être utilisé **directement comme valeur** dans un autre nœud (*Utiliser comme valeur* dans l'inspecteur ou le menu clic droit).

## Modes du hook

| Mode | Ce qui s'exécute |
|---|---|
| **Exécuter l'original d'abord, puis mon graphe** | La fonction du jeu, puis votre logique (par défaut). |
| **Exécuter mon graphe d'abord, puis l'original** | Votre logique, puis celle du jeu. |
| **Remplacer l'original** | Seulement votre graphe. |
| **Manuel** | Vous placez des nœuds **Call original (Orig)** où vous voulez dans votre graphe. |

En mode *avant* avec une valeur de retour, une sortie **original result** vous donne ce que le jeu a renvoyé. Changez le type de retour ou les noms d'arguments dans l'inspecteur si besoin.

## Mauvais type de retour ?

Le catalogue devine les types de retour d'après les en-têtes. Si une fonction indique `void` mais renvoie quelque chose, utilisez **Changer…** à côté du type de retour (un avertissement demande confirmation). Le choix est mémorisé.

## Appel par nom

Pour ce qui n'est pas dans le catalogue, utilisez **Call by name** (Fonctions) : n'importe quelle fonction C++ écrite par son nom, p. ex. `sead::Mathf::sqrt(x)`. **Get scene object** couvre `al::getSceneObj<T>(…)`.

## Style d'appel

*Préférences > Avancé* : les appels sont du C++ simple par défaut (`rs::getPlayerActor(scene)`), ou par adresse. Un nœud isolé peut le remplacer (*Style d'appel* dans l'inspecteur). Les hooks s'installent **par symbole** par défaut ; la forme par offset est le recours.
