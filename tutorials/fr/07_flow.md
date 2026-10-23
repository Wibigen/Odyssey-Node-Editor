# Contrôle de flux

Les blocs **Flow** décident *quels* nœuds s'exécutent et *combien de fois*.

| Bloc | Ce qu'il fait |
|---|---|
| **Branch (if / else)** | Condition **c** : exécute le chemin **then** ou le chemin **else**, puis continue. |
| **Switch** | Choisit un chemin d'après une valeur entière ; modifiez les cas dans de petites cases avec le bouton **+**. |
| **For loop** | Répète un chemin N fois ; l'indice est une sortie. |
| **While loop** | Répète tant qu'une condition est vraie. |
| **Return** | Quitte la fonction ou le hook en cours, éventuellement avec une valeur. |

## Lire le flux

Suivez les flèches blanches. Un nœud avec deux sorties à flèche (Branch) a deux suites possibles ; toutes deux peuvent ensuite rejoindre un nœud commun.

## Conseils

* Gardez une boucle courte : les hooks s'exécutent sur le thread principal du jeu, à chaque image.
* Pour faire quelque chose **une seule fois** à chaque changement de condition, stockez l'état précédent dans une **Variable globale**.
* Regroupez une idée répétée dans votre propre fonction (tutoriel suivant).
