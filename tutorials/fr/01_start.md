# Commencer ici

L'**Odyssey Node Editor** vous permet de créer un mod pour **Super Mario Odyssey 1.0.0** sans écrire de C++ à la main. Vous connectez des **nœuds** sur un canevas et l'éditeur écrit le code [exlaunch](https://github.com/shadowninja108/exlaunch) à votre place. Vous le compilez toujours avec votre propre projet exlaunch.

## L'idée en une minute

1. Un nœud **hook** dit *« quand le jeu exécute cette fonction, exécute mon graphe »*.
2. Vous connectez ensuite des nœuds : appeler des fonctions du jeu, modifier des variables, tester des conditions, faire des boucles.
3. L'onglet **Code C++** affiche le résultat en direct.
4. **Écrire dans le projet** place le code dans votre projet exlaunch, **Compiler** le construit, l'onglet **Ryujinx** lance le jeu avec votre mod.

## Ce qu'il vous faut

* Un dossier **OdysseyDecomp** (l'éditeur lit sa liste de symboles pour connaître chaque fonction du jeu).
* Un **projet exlaunch** (par exemple une copie de SMO-Exlaunch-Base) que vous pouvez compiler.
* *(facultatif)* Ryujinx, pour tester.

## La fenêtre

| Zone | Ce que c'est |
|---|---|
| Menus + barre d'outils | Fichier, Édition, Bibliothèque, Affichage, Outils, Plugins, Aide ; les icônes les plus utilisées |
| **Blocs** (gauche) | Tous les blocs que vous pouvez ajouter, avec recherche |
| **Canevas** (centre) | Votre graphe |
| **Inspecteur** (droite) | Réglages du nœud sélectionné |
| **Sortie** (bas) | Code C++, Includes, Problèmes, Build, Ryujinx |

Utilisez **Aide > Visite de l'interface** pour une présentation guidée, puis suivez les tutoriels dans l'ordre :

1. *Configurer votre projet*
2. *Votre premier mod*
3. *Le canevas*, puis les sujets dont vous avez besoin.

**Bon à savoir :** l'éditeur ne compile jamais lui-même pour la Switch et ne touche jamais à vos fichiers du jeu : il écrit du C++ dans le projet que vous lui indiquez.
