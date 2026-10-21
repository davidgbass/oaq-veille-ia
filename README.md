# Veille IA clinique

Site public de la veille sur l'usage de l'intelligence artificielle par les cliniciens
(action 2.2.2 du plan stratégique 2026-2029 de l'OAQ), préparée pour le CIDP.

- `data/rapports/AAAA-MM.json` : un rapport mensuel
- `data/references.json` : documents de référence antérieurs à la veille
- `python3 build.py` : régénère `index.html` et `rapports/*.html`

Le script refuse de générer le site si un résumé n'a pas une centaine de mots (80 à 130),
si un texte contient un tiret cadratin ou demi-cadratin, ou si un lien pointe vers Concerto.

## Sélection : au plus 5 documents par mois

Le rapport doit se lire en dix minutes. Un mois tranquille compte 2 ou 3 documents ; un mois
sans rien de marquant le dit dans son résumé. Ordre de priorité :

1. Orientation ou consigne d'une autorité québécoise sur l'usage clinique de l'IA (MSSS,
   Collège des médecins et autres ordres de la santé, CAI, CIQ, INESSS).
2. Données sur l'usage réel par les cliniciens (sondages, portraits).
3. Ce qui touche directement l'audioprothésie ou l'audiologie, ici ou ailleurs.
4. Déploiements sur le terrain au Québec.
5. Presse internationale, seulement si elle est exceptionnelle.

Exclus : l'IA des fabricants et des appareils, les outils destinés aux citoyens, les études
scientifiques (le CIDP en fait déjà la revue) et les doublons (deux articles sur la même
initiative donnent un seul document).

La collecte vit dans le wiki OAQ-v2 (`scripts/veille_ia_clinique.py`). Seules des sources
publiques entrent ici. Les documents du portail Concerto du CIQ restent dans le courriel au CIDP.
