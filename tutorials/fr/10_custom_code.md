# Code personnalisé et import de C++

Les nœuds couvrent beaucoup, pas tout. Deux issues de secours vous permettent d'avancer.

## Blocs personnalisés

* **Custom expression** : n'importe quelle expression C++ utilisée comme valeur.
* **Custom statement** : n'importe quelle instruction C++ dans le flux.

Reliez jusqu'à huit entrées et nommez-les `$a` … `$h` dans votre texte :

```
sead::Mathf::sqrt($a * $a + $b * $b)
```

## Fichiers d'inclusion

L'onglet **Includes** (en bas) liste les lignes `#include` du fichier généré. Ajoutez les en-têtes dont votre code personnalisé a besoin.

## Importer du C++

**Fichier > Importer un fichier C++…** (Ctrl+I) transforme un `.cpp` en graphe dans la mesure où il le comprend. Il lit le code que cet outil écrit et les schémas courants écrits à la main ; les templates, classes et macros inhabituelles sont conservés comme code personnalisé. Vérifiez ensuite l'onglet *Problèmes*.
