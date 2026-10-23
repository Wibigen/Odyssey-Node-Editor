# Le canevas : nœuds, broches et liens

## Nœuds et broches

Un nœud a des **broches d'entrée** à gauche et des **broches de sortie** à droite.

* Les **broches à flèche blanche** sont l'**ordre d'exécution** : le nœud s'exécute après celui relié à sa broche *in*, puis continue par *next*.
* Les **ronds colorés** sont des **valeurs**. La couleur dépend du type (nombre, pointeur, bool, texte…). Un rond plein est relié ; un rond vide est libre.
* Une entrée non reliée affiche une **valeur fixe** que vous saisissez dans l'inspecteur (`= 60`).

## Relier

* **Glissez d'une broche vers une autre** (une sortie vers une entrée).
* Une sortie de valeur peut alimenter **plusieurs** entrées ; une sortie d'exécution mène à **un seul** nœud suivant.
* **Relâchez dans le vide** : un menu propose *Fonction du jeu…*, *Fonction de plugin…* (quand un plugin a un catalogue) et tous les blocs qui conviennent ; le nouveau nœud est créé et connecté pour vous. (Désactivable dans les Préférences.)
* Sélectionnez un nœud et appuyez sur **Suppr** pour le supprimer ; *Inspecteur > Déconnecter* ne retire que ses liens.

## Se déplacer

| Action | Comment |
|---|---|
| Zoom | Molette de la souris (Ctrl +/-) |
| Déplacer la vue | Maintenez le **bouton du milieu** et glissez |
| Tout ajuster à l'écran | **F** |
| Sélectionner plusieurs nœuds | Tracez un rectangle sur un espace vide ; Ctrl+A pour tout |
| Dupliquer / supprimer | Ctrl+D / Suppr |
| Annuler / rétablir | Ctrl+Z / Ctrl+Y |
| Trouver un nœud | Ctrl+F dans le graphe (l'icône de recherche) |
| Ranger | Ctrl+L organise les nœuds automatiquement |

## Ajouter des blocs

* **Double-cliquez** ou **glissez** un bloc depuis la liste **Blocs**.
* **Clic droit** sur le canevas vide pour les mêmes choix, plus *Commenter ici*.
* La zone de filtre au-dessus de la liste cherche dans les noms et les descriptions.

## Couleurs

Chaque type de nœud a sa propre couleur d'en-tête. Les nœuds qui viennent d'un **plugin** ont aussi une douce lueur à la couleur du plugin, pour les repérer d'un coup d'œil.
