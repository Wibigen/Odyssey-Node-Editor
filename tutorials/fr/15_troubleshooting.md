# Dépannage

| Problème | Ce qu'il faut essayer |
|---|---|
| *Le catalogue de fonctions est vide* | Outils > Réglages : choisissez votre dossier OdysseyDecomp (avec `data/file_list.yml`) et extrayez le catalogue. |
| Une fonction renvoie `void` alors qu'elle ne devrait pas | Changez le type de retour (voir *Appeler et hooker des fonctions du jeu*). |
| L'onglet *Problèmes* liste quelque chose | Double-cliquez sur une ligne : le nœud est sélectionné. En général une entrée non reliée ou une variable manquante. |
| La compilation ne trouve pas un en-tête | Ajoutez-le dans l'onglet **Includes**, ou corrigez les dossiers d'inclusion de votre projet. |
| Le dossier de build est cassé | Outils > **Réparer la base exlaunch**. |
| Rien ne se passe dans le jeu | Le hook est-il installé (bon symbole) ? Le dossier du mod est-il celui que Ryujinx charge (onglet Ryujinx) ? Un autre mod est-il désactivé ? |
| Le jeu plante | Un pointeur est nul ou un offset est faux. Ajoutez des vérifications **Is null?** ; confirmez les offsets pour la version 1.0.0. |
| Un raccourci ne fonctionne pas | Outils > Raccourcis clavier : il a peut-être été modifié. |
| La disposition de la fenêtre est étrange | Affichage : affichez le panneau de sortie (Ctrl+J) ; faites glisser les panneaux là où vous le voulez. |

Si vous signalez un problème, joignez le journal **Build** (Enregistrer le journal sous…).
