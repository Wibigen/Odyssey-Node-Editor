# Variables, valeurs et maths

## Variables (catégorie *Variables*)

| Bloc | Usage |
|---|---|
| **Declare variable** | Une variable locale (type, nom, valeur initiale facultative). Vit dans le flux où vous la déclarez. |
| **Set variable** | Affecter une nouvelle valeur. |
| **Get variable** | Lire la valeur actuelle (une sortie de valeur, sans broche d'exécution). |
| **Global variable** | Garde sa valeur entre les images et les appels. Un *Declare variable* qui n'est pas dans une fonction devient aussi une globale. |
| **Constant (value)** | Un nombre, du texte, un bool ou n'importe quelle valeur C++ que vous saisissez. |

Utilisez **Avancé** dans l'inspecteur pour les qualificateurs (`static`, `const`…) et les tableaux (taille et contenu).

> Une variable locale déclarée dans une branche n'existe que dans cette branche (comme en C++).

## Maths et logique

Dessinés comme de petits carrés :

* **Math (A + B)** : `+ - * / %` sur deux valeurs (choisissez le type).
* **Compare** : `== != < > <= >=`, donne un bool.
* **Logic** : AND / OR ; **NOT** inverse un bool.

Connectez le résultat à la condition d'un **Branch**, à une variable ou à un argument d'appel.

## Valeur fixe ou lien ?

Toute broche d'entrée peut être **reliée** à un nœud ou recevoir une **valeur fixe** (saisie dans l'inspecteur). Une entrée reliée masque sa valeur fixe.

## Types

Les couleurs des broches montrent les types ; l'éditeur ne vérifie pas les types de pointeurs entre les liens (par exemple `StageScene*` vers `al::LiveActor*` est une erreur C++ que vous verrez à la compilation). Utilisez **Cast** (Pointeurs et mémoire) quand vous devez convertir.
