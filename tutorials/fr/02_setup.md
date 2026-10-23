# Configurer votre projet

Ouvrez **Outils > Réglages** (Ctrl+Maj+,). La fenêtre s'ouvre toute seule la première fois.

## 1. Le dossier OdysseyDecomp

Choisissez le dossier de votre copie d'[OdysseyDecomp](https://github.com/MonsterDruide1/OdysseyDecomp) (celui qui contient `data/file_list.yml`). L'éditeur construit alors le **catalogue de fonctions** (environ 17 700 fonctions) : noms, arguments, types de retour, offsets et symboles. Cela n'est fait qu'une fois puis enregistré. Il faut l'outil `c++filt` pour lire les noms mangés ; il est trouvé automatiquement, ou indiquez-le dans la même fenêtre.

Si le catalogue indique `void` pour une fonction qui renvoie en réalité quelque chose, vous pourrez corriger cela plus tard (voir *Appeler et hooker des fonctions du jeu*).

## 2. Votre projet exlaunch

* **Dossier du projet** : la racine de votre projet exlaunch (celle qui contient `CMakeLists.txt`). Les chemins Windows, `\\wsl$\Ubuntu\home\me\proj` et les chemins WSL sont compris.
* **Fichier généré** : l'endroit où le code est écrit. Vide = `src/program/main.cpp` ou `src/main.cpp`, selon celui qui existe.

## 3. La commande de compilation

Par défaut : `cmake --build build`. Choisissez où elle s'exécute : **Windows (cmd)**, **WSL** (choisissez la distribution, par exemple Ubuntu) ou le shell natif. Le premier *Compiler* vous le demande si ce n'est pas réglé.

## 4. Tester

Ouvrez l'onglet **Ryujinx** (en bas), indiquez une seule fois l'exécutable Ryujinx, le fichier du jeu et un nom de mod. *Installer le mod et lancer* copie votre build dans le dossier des mods de Ryujinx et démarre le jeu.

## Si quelque chose est introuvable

* Onglet **Problèmes** : ce dont le graphe a encore besoin.
* **Outils > Réparer la base exlaunch** : supprime le dossier `build` et relance CMake (répare une configuration cassée).
* Les Réglages peuvent être rouverts à tout moment ; rien n'est perdu.
