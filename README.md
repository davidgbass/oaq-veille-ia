# Veille IA clinique

Site public de la veille sur l'usage de l'intelligence artificielle par les cliniciens
(action 2.2.2 du plan stratégique 2026-2029 de l'OAQ), préparée pour le CIDP.

- `data/rapports/AAAA-MM.json` : un rapport mensuel
- `data/references.json` : documents de référence antérieurs à la veille
- `python3 build.py` : régénère `index.html` et `rapports/*.html`

Le script refuse de générer le site si un résumé n'a pas une centaine de mots (80 à 130),
si un texte contient un tiret cadratin ou demi-cadratin, ou si un lien pointe vers Concerto.

La collecte vit dans le wiki OAQ-v2 (`scripts/veille_ia_clinique.py`). Seules des sources
publiques entrent ici. Les documents du portail Concerto du CIQ restent dans le courriel au CIDP.
