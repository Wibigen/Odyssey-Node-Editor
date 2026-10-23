# Plugins

Les plugins ajoutent des **nœuds**, des **catalogues de fonctions**, des **thèmes**, des **modèles** et des **tutoriels**.

## Explorateur de plugins

**Plugins > Explorateur de plugins** (Ctrl+Maj+P) : chaque plugin avec son image, son auteur, sa version et son contenu. **Activer / Désactiver**, **Installer…** (un `.zip` / `.odnp` ou un dossier), **Supprimer**, **Nouveau plugin…** (un squelette à modifier), **Afficher le dossier**.

Fournis avec le programme : *Entrées/sorties standard*, *Chaînes*, *Thèmes supplémentaires* et **Dear ImGui** (désactivé par défaut).

## Utiliser ce qu'un plugin ajoute

* Les nœuds apparaissent dans la liste **Blocs** sous les catégories du plugin, avec une douce lueur colorée sur le canevas.
* Un catalogue s'ouvre avec **Fonction de plugin…** (Ctrl+Maj+K, ou le bouton au-dessus de la liste des blocs, ou le menu sur un lien relâché).
* Modèles : **Fichier > Nouveau à partir d'un modèle**.
* Tutoriels : fenêtre **Tutoriels**, section *Tutoriels des plugins*.

## Plugins qui modifient votre projet

Certains plugins (Dear ImGui) ont besoin de fichiers et de lignes CMake dans votre projet exlaunch. L'éditeur vous le **propose** à l'activation : rien n'est écrasé, une sauvegarde de `CMakeLists.txt` est conservée, et *Explorateur de plugins > Base exlaunch…* retire exactement ce qui a été ajouté.

## Sécurité

Un plugin avec un fichier `plugin.py` exécute du Python avec les mêmes droits que l'éditeur. N'installez que des plugins de personnes de confiance.

## En écrire un

Voir `PLUGINS.md` (format, modèles de nœuds, thèmes, pages d'aide, réglages).
