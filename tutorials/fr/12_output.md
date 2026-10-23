# Code, problèmes et compilation

Le panneau **Sortie** en bas a cinq onglets. Réduisez-le avec la flèche, **Ctrl+J**, ou un double-clic sur un onglet.

## Code C++

Aperçu en direct du fichier généré. Les lignes du **nœud sélectionné** sont surlignées. **Copier** et **Enregistrer sous…** l'exportent.

## Includes

Les en-têtes en haut du fichier (voir *Code personnalisé*).

## Problèmes

Ce qui manque ou ne va pas **avant** de compiler : entrées non reliées, variables inconnues, hooks vides. Double-cliquez sur une ligne pour aller au nœud.

## Build

* **Écrire dans le projet** (Ctrl+E) enregistre le code dans votre projet exlaunch.
* **Compiler** (F5) lance la commande de compilation et affiche la sortie. **Copier les erreurs** ne copie que les lignes d'erreur ; **Enregistrer le journal sous…** garde toute la console.
* **Réparer la base** (menu Outils) supprime `build/` et relance CMake.

## Ryujinx

Indiquez une fois l'émulateur, le fichier du jeu et un nom de mod. **Installer le mod et lancer** copie `subsdkN` et `main.npdm` de votre dossier de build vers le dossier des mods de Ryujinx et démarre le jeu. Les options comprennent compiler d'abord, désactiver les autres mods et le plein écran.

## Important

L'éditeur lui-même ne compile jamais pour la Switch : c'est la chaîne d'outils de votre projet qui le fait. Si une compilation échoue, copiez le journal (il indique exactement quel fichier et quelle ligne).
