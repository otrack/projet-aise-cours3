# wikidiff : quatre tâches pour un agent de code

Ce projet sert à mettre en pratique les quatre cas d'usage du cours 3
(section 5, « Le développement agentique : autonomie et pratique ») :
pour chacun, une tâche que vous déléguez à un agent de code, et dont vous supervisez la réalisation.

## Installation : opencode et un modèle

L'agent de code est [opencode](https://opencode.ai), en version 2.2.5 ou plus récente. Sous Linux,
installez-le avec :

```sh
curl -fsSL https://opencode.ai/v2/install | bash
```

Pour les autres systèmes, suivez les [instructions officielles](https://opencode.ai/download).
Vérifiez ensuite la version avec `opencode --version`.

Il lui faut ensuite un modèle. Deux options :

| option | coût | vitesse | ce qu'il faut |
|---|---|---|---|
| A. Mistral, avec une clé d'API | gratuit (plan *Experiment*), avec des limites de débit | rapide | un compte Mistral (une adresse e-mail suffit) |
| B. un modèle local, avec Ollama | gratuit | correcte avec un GPU dédié, très lente sinon | Ollama (cours 1), et une machine assez puissante (voir ci-dessous) |

Dans les deux cas, le modèle est le même : Ministral 3B, que vous utilisez depuis le cours 1.

### Option A : Mistral, avec une clé d'API

**Attention : vos données peuvent servir à entraîner les modèles de Mistral.** Avec cette
option, vos prompts, votre code et les sorties des commandes sont envoyés à Mistral, qui, sur le
plan gratuit *Experiment*, peut les utiliser pour entraîner ses modèles. C'est sans conséquence
pour ce projet, qui est public ; mais n'utilisez jamais cette option avec du code ou des données
confidentiels (un projet d'entreprise ou de stage, des données personnelles).

1. Sur <https://mistral.ai>, cliquez sur *Log in*, puis choisissez *Studio* (et non *Vibe*).
   Connectez-vous avec un compte personnel (Google, Microsoft, ou une adresse e-mail, même jetable).
2. Dans *API Keys*, cliquez sur *Create new key*. Donnez-lui un nom, et une date d'expiration
   après la fin du cours. Copiez la clé : elle ne sera plus affichée.
3. Lancez `opencode` depuis ce répertoire, et donnez-lui la clé : `Ctrl+P`, puis *Switch model* ;
   dans la liste des modèles, `Ctrl+A` pour choisir l'intégration, sélectionnez *Mistral*, puis
   collez la clé. opencode la garde hors du projet : ne la mettez jamais dans un fichier du
   dépôt.
4. Choisissez ensuite, dans la même liste, le modèle *Ministral 3B*
   (`mistral/ministral-3b-latest`). C'est le modèle que vous utilisez depuis le cours 1 avec
   Ollama (`ministral-3:3b`), mais servi par Mistral : sans la compression (quantification) de
   la version locale, et bien plus vite. S'il
   peine sur une tâche, essayez un modèle plus gros, comme *Ministral 8B*
   (`mistral/ministral-8b-latest`).

### Option B : un modèle local, avec Ollama

Le modèle est `ministral-3:3b`, que vous avez téléchargé avec Ollama au cours 1 (voir
`exercices/cours1/README.md`). Avec la fenêtre de contexte qu'exige opencode, il occupe environ
6 Go de mémoire. Pour qu'il tourne sans peine, il faut au minimum :

- soit une carte graphique dédiée avec 8 Go de mémoire vidéo (par exemple une NVIDIA RTX 3060 ou
  4060) ;
- soit un Mac à puce Apple (M1 ou plus récent) avec 16 Go de mémoire.

Sans cela (un GPU intégré à un processeur, ou le CPU seul, même récents), le modèle fonctionne,
mais chaque réponse prend plusieurs minutes : préférez l'option A. Dans tous les cas, un modèle
de 3 milliards de paramètres échoue souvent : attendez-vous à des appels d'outils ratés, et à
des boucles. C'est aussi l'occasion de voir pourquoi la supervision compte.

1. Créez une variante de `ministral-3:3b` avec une fenêtre de contexte de 32k tokens, et une
   température de 0. Le *system prompt* et les outils d'opencode occupent à eux seuls plusieurs
   milliers de tokens, et chaque fichier lu, chaque sortie de test ou du benchmark s'y ajoute :
   une tâche de ce projet envoie au modèle des prompts d'une dizaine de milliers de tokens, bien
   plus que la fenêtre par défaut d'Ollama sur une machine modeste (4096 tokens). Ces réglages
   sont fixés dans `.opencode/Modelfile` :

   ```sh
   cd exercices/cours3/project
   ollama create ministral-3:3b-32k -f .opencode/Modelfile
   ```

2. Lancez `opencode` depuis ce répertoire : `.opencode/opencode.json` le branche sur Ollama, et
   choisit par défaut le modèle `ministral-3:3b-32k`. Vérifiez, après une première demande, la
   fenêtre réellement utilisée : c'est la colonne `CONTEXT` de `ollama ps` (pas `ollama show`,
   qui donne la taille maximale que le modèle accepte). Si la colonne `PROCESSOR` montre que le
   modèle déborde sur le CPU, tout ralentit ; ramenez `num_ctx` à 16384 dans le `Modelfile`, et
   recréez le modèle.

### Dans opencode

- tapez votre demande, puis Entrée ; opencode lit `AGENTS.md` au début de chaque session ;
- `Tab` passe de l'agent *build* (il lit, écrit et exécute) à l'agent *plan* (il lit et
  propose, sans rien modifier) : c'est le mode plan du cours ;
- `/new` ouvre une session neuve, `/undo` annule la dernière modification de l'agent,
  `/models` change de modèle ; ouvrez une session neuve à chaque tâche, pour repartir
  d'un contexte vide ;
- l'agent est en laisse courte : il demande votre accord avant chaque modification et
  chaque commande (`"permission"` de l'agent `build`, dans `.opencode/opencode.json` ; l'agent
  `plan`, lui, ne modifie jamais rien). Pour la longue itération, remplacez `"ask"` par
  `"allow"` ; le mode YOLO, qui approuve tout, se lance avec
  `opencode --auto`.

### Voir l'échange entre l'agent et le modèle

`debug/trace.py` se place entre opencode et le modèle, et affiche chaque échange : ce que le modèle
reçoit, et ce qu'il répond. C'est la boucle agentique du cours, vue de l'intérieur. Il fonctionne
avec les deux options.

1. Dans un premier terminal, depuis ce répertoire, lancez `debug/trace.py` avec votre option :

   ```sh
   export MISTRAL_API_KEY=...       # option A : votre clé, que trace.py ajoute aux requêtes
   python debug/trace.py mistral

   python debug/trace.py            # option B : Ollama
   ```

   Ajoutez `-f` pour voir les messages en entier ; sinon, ils sont coupés à 600 caractères.

2. Dans un second terminal, lancez `opencode`, puis choisissez avec `/models` le modèle tracé :
   *Ministral 3B (traced)* pour l'option A, *Ministral 3 3B (32k context, traced)* pour
   l'option B. Ses requêtes passent alors par `trace.py` (port 11436 pour Mistral, 11435 pour
   Ollama), au lieu d'aller directement au modèle.

Pour chaque requête, `trace.py` affiche le nombre de messages et d'outils envoyés, puis les seuls
messages ajoutés depuis la dernière réponse du modèle (au début d'une conversation, le
*system prompt* et la liste des outils), et enfin la réponse : du texte, des appels d'outils, et
le nombre de tokens du prompt. Observez par exemple :

- la taille du *system prompt* d'opencode, et la liste des outils offerts au modèle ;
- l'historique, renvoyé en entier à chaque requête : le nombre de tokens du prompt grandit à
  chaque tour de la boucle ;
- chaque appel d'outil, suivi de son résultat dans la requête suivante ;
- les requêtes qu'opencode fait pour son propre compte, comme le titre de la session.

## Le programme

`wikidiff.py` prend une recherche Wikipedia, retient la première page trouvée, puis télécharge
toutes ses versions (ses *révisions*) avec la
[MediaWiki Action API](https://www.mediawiki.org/wiki/API:Revisions) : d'abord la liste de leurs
identifiants, puis leur contenu, par lots de 50, un lot après l'autre. Il affiche enfin sur la
sortie standard le diff de chaque révision avec la précédente, de la création de la page
jusqu'à sa dernière version.

```sh
python wikidiff.py vector clock              # Wikipedia anglaise
python wikidiff.py --lang fr horloge vectorielle
python wikidiff.py vector clock | less
```

Python 3.10 ou plus, bibliothèque standard uniquement ; le programme, le test d'intégration et
le benchmark ont besoin du réseau.

| fichier | rôle |
|---|---|
| `wikidiff.py` | le programme |
| `tests/test_units.py` | les tests unitaires, sans réseau |
| `tests/test_integration.py` | le test d'intégration, sur la vraie Wikipedia |
| `tests/test_perf.py` | le benchmark : le temps de téléchargement des révisions d'une page |
| `debug/trace.py` | affiche les échanges entre opencode et le modèle |
| `AGENTS.md` | le contexte du projet, pour l'agent |
| `.opencode/opencode.json`, `.opencode/Modelfile` | la configuration d'opencode, et du modèle |
| `.opencode/skills/python-unit-tests/` | une skill pour lancer les tests, qu'opencode charge au besoin |

Lancez toutes les commandes depuis la racine du projet :

```sh
python -m unittest -v                     # tous les tests
python -m unittest tests.test_integration # un seul fichier de tests
python -m tests.test_perf                 # le benchmark (unittest ne le lance pas)
```

**Le test d'intégration échoue : c'est voulu**, c'est l'objet de la tâche 3.

## Avant chaque tâche

- commitez, puis créez une branche pour la tâche : `git diff` montrera exactement ce que l'agent
  a changé, et `git restore .` l'annulera ;
- avant de déléguer, répondez par écrit aux quatre questions du cours :
  **quel mode ? qu'est-ce qui dit « fini » ? quel contexte donner ? qu'est-ce qui peut mal tourner ?**
- à la fin, lisez le diff, pas le résumé de l'agent ; une tâche = un commit.

Les prompts ci-dessous sont des points de départ : adaptez-les.

## Tâche 1 : comprendre un code inconnu

> Lis `wikidiff.py`, sans le modifier, puis réponds à deux questions, en donnant pour chaque
> réponse le numéro de la ligne concernée :
> 1. Dans `list_revision_ids`, quelle condition arrête la boucle ?
> 2. Pour une page de 340 révisions, combien de fois `fetch_revisions` appelle-t-elle
>    `api_get` ? Compte séparément les appels faits par `list_revision_ids` et ceux faits par
>    `fetch_batch`, puis additionne.

À superviser :

- l'agent ne doit rien écrire : utilisez le mode plan (`Tab`) ;
- ouvrez ses numéros de ligne, et vérifiez qu'ils disent bien ce qu'il affirme ;
- confrontez sa réponse au réel : `python -m tests.test_perf` télécharge une page de 340
  révisions ;
  combien de requêtes cela fait-il d'après la
  [documentation de l'API](https://www.mediawiki.org/wiki/API:Revisions) (`rvlimit`) ?

## Tâche 2 : optimiser les performances

1. En mode plan :
   > `fetch_revisions`, dans `wikidiff.py`, télécharge les lots de révisions l'un après
   > l'autre, et c'est lent. Lance `python -m tests.test_perf` pour le mesurer. Puis propose une nouvelle
   > version de `fetch_revisions` qui appelle `fetch_batch` sur les lots en parallèle, avec
   > `concurrent.futures.ThreadPoolExecutor(max_workers=4)` et `pool.map`, en gardant l'ordre
   > des lots. Montre le code complet de la nouvelle fonction.
2. Relisez la proposition ; si elle vous convient, passez en mode *build* :
   > Remplace maintenant `fetch_revisions` dans `wikidiff.py` par le code que tu as proposé,
   > avec l'outil `edit`. Puis lance `python -m tests.test_perf`.

   Si l'agent annonce ce qu'il va faire, puis s'arrête sans rien modifier (un défaut courant
   des petits modèles), relancez-le : « Fais-le maintenant, avec l'outil `edit`. »

À superviser :

- laisse courte : relisez la proposition avant de l'accepter, puis un changement à la fois ;
- deux oracles : le benchmark doit aller plus vite **et** afficher le même hash qu'avant
  (notez-le avant de commencer), et les tests unitaires doivent toujours passer ;
- le benchmark est hors de portée de l'agent (voir `AGENTS.md`) : vérifiez avec
  `git diff tests/test_perf.py` ;
- pièges classiques : des révisions perdues ou en double, un ordre chronologique qui n'est plus
  garanti, trop de requêtes simultanées (Wikipedia répond alors `429 Too Many Requests`) ;
- le test d'intégration échoue toujours : ce n'est pas l'objet de cette tâche, l'agent ne doit
  pas s'en occuper.

## Tâche 3 : corriger un test qui échoue

> `tests/test_integration.py` échoue avec une `KeyError`.
> 1. Lance `python -m unittest tests.test_integration -v`, et lis la trace de l'erreur.
> 2. Lis, dans `wikidiff.py`, la fonction où l'erreur se produit.
> 3. Explique la cause en une phrase.
> 4. Corrige cette fonction avec l'outil `edit`, sans modifier les tests, puis relance
>    `python -m unittest -v`.

À superviser :

- longue itération : le test qui échoue est un oracle tout prêt ; la tâche est finie quand il
  passe, avec le reste de la suite ;
- donnez à l'agent le message d'erreur et la commande qui le reproduit, pas votre hypothèse
  sur la cause ;
- exigez la cause avant la correction, et vérifiez-la vous-même dans l'API (que renvoie-t-elle
  pour la révision 721990679 ?) ;
- méfiez-vous d'une correction du symptôme (un `try/except`, une valeur par défaut) plutôt que
  de la cause ;
- vérifiez que le test est intact : `git diff tests/` doit être vide.

## Tâche 4 : ajouter une fonctionnalité, les tests d'abord

On ajoute une option `--api rest`, qui fait la recherche et la liste des identifiants des
révisions avec la [MediaWiki REST API](https://www.mediawiki.org/wiki/API:REST_API/Reference),
plus moderne ; `--api action` reste le défaut. Le contenu des révisions reste téléchargé par
`fetch_batch`, avec l'Action API : la REST API ne donne le contenu que d'une révision à la fois.

Cette fois, c'est à vous d'écrire les prompts, et de décider de ce qui dit « fini ».
Remplacez chaque `TODO` ci-dessous avant de passer à l'étape suivante.

0. Les quatre questions, pour chaque étape :

   | étape | quel mode ? | qu'est-ce qui dit « fini » ? | quel contexte donner ? | qu'est-ce qui peut mal tourner ? |
   |---|---|---|---|---|
   | le plan | TODO | TODO | TODO | TODO |
   | les tests | TODO | TODO | TODO | TODO |
   | l'implémentation | TODO | TODO | TODO | TODO |

1. Le plan. Demandez à l'agent quels endpoints de la REST API utiliser, quelles fonctions ajouter
   (par exemple `rest_search_title` et `rest_list_revision_ids`, sur le modèle de `search_title`
   et `list_revision_ids`), et quels tests écrire ; il ne doit pas écrire de code.
   > TODO : votre prompt.

   Relisez le plan avec la documentation de la REST API : comment y obtient-on l'historique
   d'une page, par combien de révisions, et dans quel ordre ? Combien de requêtes faut-il pour
   une page de N révisions, comparé à l'Action API ? Corrigez le plan maintenant, quand c'est
   peu cher.

2. Les tests. Avant de les demander à l'agent, listez les cas qu'ils doivent couvrir :
   - TODO
   - TODO
   - TODO

   Quelques pistes : la pagination de l'historique, l'ordre des identifiants, un titre avec des
   espaces, une apostrophe ou un `/` (`AC/DC`), une page qui n'existe pas, une recherche sans
   résultat. Puis faites écrire les tests, sans réseau, sans l'implémentation :
   > TODO : votre prompt.

3. Relisez les tests : couvrent-ils vos cas ? Échouent-ils tous, faute d'implémentation ?
   Puis commitez-les.

4. L'implémentation.
   > TODO : votre prompt.

5. La validation. Écrivez les commandes qui montrent que la tâche est finie :
   ```sh
   # TODO : les tests relus à l'étape 3 sont intacts
   # TODO : tous les tests passent
   # TODO : les deux API donnent les mêmes révisions, sur une page de plus de 20 révisions
   ```
   Comparez enfin le nombre de requêtes des deux API, pour une page de N révisions.
