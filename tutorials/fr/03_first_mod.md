# Votre premier mod

Objectif : exécuter quelque chose **une fois par seconde** pendant le jeu. Le graphe d'exemple le fait ; ici vous le construisez vous-même pour connaître chaque partie.

## 1. Hooker une fonction du jeu

1. Cliquez sur **Fonction du jeu…** (bouton rouge, ou Ctrl+Maj+F).
2. Cherchez `exePlay`, sélectionnez **StageScene::exePlay** (elle s'exécute à chaque image pendant que vous jouez).
3. Choisissez **Hooker cette fonction**, gardez le mode *Exécuter l'original d'abord, puis mon graphe*, cliquez sur **Ajouter au graphe**.

Un nœud rouge **Hook StageScene::exePlay** apparaît. Sa broche blanche **next** est le point de départ de votre logique.

## 2. Compter les images

1. Ajoutez une **Variable globale** (Variables) : type `int`, nom `frames`, valeur initiale `0`. Une variable globale garde sa valeur d'une image à l'autre.
2. Ajoutez **Set variable**, choisissez `frames`, connectez **hook next → in**.
3. Ajoutez **Get variable** `frames` et **Math (A + B)** de type `int`, B = `1` ; connectez *Get → A*, *Math out → Set v*.

## 3. Faire quelque chose toutes les 60 images

1. Ajoutez **Branch (if / else)** après le Set variable.
2. Condition : **Compare** `(frames % 60) == 0` (un nœud *Math* avec `%` et 60 qui alimente un *Compare* avec `== 0`). Connectez le résultat à la broche **c** du Branch.
3. Mettez ce que vous voulez sur le chemin **then**, par exemple une **Custom statement** `/* mon code ici */`, ou un appel de fonction du jeu.

## 4. Regarder le code

Ouvrez l'onglet **Code C++** : le hook, la variable et le `if` y sont. Sélectionnez un nœud : ses lignes sont surlignées.

## 5. Compiler et essayer

1. L'onglet **Problèmes** est vide ? Parfait.
2. **Écrire dans le projet** (Ctrl+E), puis **Compiler** (F5).
3. Onglet **Ryujinx** > *Installer le mod et lancer*.

> Départ plus rapide : **Fichier > Nouveau à partir d'un modèle** (ou le graphe d'exemple dans Préférences > Ouvrir sur) donne un graphe prêt à l'emploi.
