#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère le site de la veille IA clinique à partir des données JSON.

  data/rapports/AAAA-MM.json  un rapport mensuel (résumé, rubriques, documents, questions)
  data/references.json        documents de référence antérieurs à la veille

Sorties : index.html (liste des rapports + références) et rapports/AAAA-MM.html.
Le site est public (GitHub Pages) : seules des sources publiques y entrent.
Les documents du portail Concerto du CIQ n'y vont jamais.

Champ facultatif « audio » : une ou deux phrases (au plus 45 mots) sur ce qui
s'applique aux audioprothésistes, seulement quand le document s'y applique.
Un document qui ne vise que le réseau public ou le gouvernement n'en a pas.

Règles de contenu : au plus 5 documents par rapport (charge mentale du comité),
et chaque document porte un résumé d'une centaine de mots (80 à 130). Le script
refuse de générer le site si un rapport dépasse 5 documents, si un résumé sort
de cette fourchette ou si un texte contient un tiret cadratin ou demi-cadratin.
"""
import os, re, sys, json, glob, html, datetime

RACINE = os.path.dirname(os.path.abspath(__file__))
MOTS_MIN, MOTS_MAX = 80, 130
DOCS_MAX = 5
AUDIO_MAX = 45
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]

def e(s):
    return html.escape(s, quote=True)

def nb_mots(s):
    return len(re.findall(r"[\wÀ-ÿ'’%,.-]+", s))

def verifier(rapports, refs):
    erreurs = []
    def doc(d, ou):
        n = nb_mots(d["resume"])
        if not MOTS_MIN <= n <= MOTS_MAX:
            erreurs.append(f"{ou} : « {d['titre'][:60]} » a {n} mots (attendu {MOTS_MIN} à {MOTS_MAX})")
        if d.get("audio") and nb_mots(d["audio"]) > AUDIO_MAX:
            erreurs.append(f"{ou} : la note « Pour les audioprothésistes » de « {d['titre'][:60]} » dépasse {AUDIO_MAX} mots")
        for champ in ("titre", "resume", "audio"):
            if re.search("[—–]", d.get(champ, "")):
                erreurs.append(f"{ou} : tiret dans le champ {champ} de « {d['titre'][:60]} »")
        if "concerto" in d["url"].lower():
            erreurs.append(f"{ou} : lien Concerto interdit sur le site public")
    for r in rapports:
        if nb_docs(r) > DOCS_MAX:
            erreurs.append(f"{r['mois']} : {nb_docs(r)} documents, maximum {DOCS_MAX}")
        for rub in r["rubriques"]:
            for d in rub["documents"]:
                doc(d, r["mois"])
        for t in [r["resume"]] + r["questions"]:
            if re.search("[—–]", t):
                erreurs.append(f"{r['mois']} : tiret dans le résumé ou une question")
    for d in refs:
        doc(d, "références")
    return erreurs

def page(titre, corps, css, entete):
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titre)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,600;0,700;1,400&amp;display=swap">
<link rel="stylesheet" href="{css}">
</head>
<body>
<header class="bandeau">
  <div class="cadre">
{entete}
  </div>
</header>
<main>
  <div class="cadre">
{corps}
  </div>
</main>
<footer>
  <div class="cadre">
    <p>Veille préparée par David Gélinas, président de l'Ordre, pour le comité d'innovation et de développement professionnel. Chaque résumé décrit le contenu du document cité et n'engage pas l'Ordre.</p>
    <p>Sources externes, à titre informatif. Elles ne proviennent pas de l'OAQ ni de la réglementation.</p>
    <p>Les notes « Pour les audioprothésistes » sont une lecture de la veille, non opposable. Elles ne constituent ni une position de l'Ordre ni un avis juridique.</p>
  </div>
</footer>
</body>
</html>
"""

SURTITRE = '    <span class="surtitre">Ordre des audioprothésistes du Québec · Plan stratégique 2026-2029, action 2.2.2</span>'

def bloc_doc(d):
    return f"""        <div class="doc">
          <div class="meta"><span class="org">{e(d['organisme'])}</span><time datetime="{e(d['date'])}">{e(d['date_texte'])}</time><span class="puce">{e(d['categorie'])}</span></div>
          <div class="corps">
            <h4><a href="{e(d['url'])}">{e(d['titre'])}</a></h4>
            <p>{e(d['resume'])}</p>{bloc_audio(d)}
          </div>
        </div>"""

def bloc_audio(d):
    # facultatif : seulement quand le document s'applique à la pratique des audioprothésistes
    if not d.get("audio"):
        return ""
    return f'\n            <p class="audio"><span class="audio-tag">Pour les audioprothésistes</span> {e(d["audio"])}</p>'

def nb_docs(r):
    return sum(len(rub["documents"]) for rub in r["rubriques"])

def page_rapport(r):
    rubriques = "\n".join(
        f'      <div class="rubrique">\n        <h3>{e(rub["titre"])}</h3>\n'
        + "\n".join(bloc_doc(d) for d in rub["documents"]) + "\n      </div>"
        for rub in r["rubriques"] if rub["documents"])
    questions = ""
    if r["questions"]:
        questions = ('      <div class="questions">\n        <h3>Questions pour le CIDP</h3>\n        <ol>\n'
                     + "\n".join(f"          <li>{e(q)}</li>" for q in r["questions"])
                     + "\n        </ol>\n      </div>")
    corps = f"""    <article class="rapport" aria-labelledby="t-rapport">
      <div class="rapport-tete">
        <span class="surtitre">Rapport mensuel · {nb_docs(r)} documents</span>
        <h2 id="t-rapport">{e(r['titre'])}</h2>
        <p class="resume">{e(r['resume'])}</p>
      </div>
{rubriques}
{questions}
    </article>"""
    entete = f"""{SURTITRE}
    <h1>Veille IA clinique</h1>
    <a class="retour" href="../index.html">Tous les rapports</a>"""
    return page(f"Veille IA clinique, {r['titre']}", corps, "../assets/style.css", entete)

def prochain(mois):
    a, m = map(int, mois.split("-"))
    a2, m2 = (a + 1, 1) if m == 12 else (a, m + 1)
    a3, m3 = (a2 + 1, 1) if m2 == 12 else (a2, m2 + 1)
    return f"{MOIS[m2 - 1].capitalize()} {a2}", f"Prévu le 1er {MOIS[m3 - 1]} {a3}"

def page_accueil(rapports, refs):
    lignes = []
    if rapports:
        titre, prevu = prochain(rapports[0]["mois"])
        lignes.append(f"""        <div class="rapport-ligne a-venir">
          <div><div class="mois">{titre}</div><div class="compte">{prevu}</div></div>
          <p>Collecte en cours.</p>
        </div>""")
    for r in rapports:
        lignes.append(f"""        <div class="rapport-ligne">
          <div><div class="mois">{e(r['titre'])}</div><div class="compte">{nb_docs(r)} documents</div></div>
          <p>{e(r['resume'])} <a href="rapports/{r['mois']}.html">Lire le rapport</a></p>
        </div>""")
    corps = f"""    <section id="rapports" aria-labelledby="t-rapports">
      <div>
        <h2 id="t-rapports">Rapports</h2>
        <p class="intro">Chaque rapport couvre un mois. Il regroupe les publications retenues par catégorie d'usage et propose quelques questions au comité.</p>
      </div>
      <div class="liste-rapports">
{chr(10).join(lignes)}
      </div>
    </section>
    <section id="references" aria-labelledby="t-ref">
      <div>
        <h2 id="t-ref">Documents de référence</h2>
        <p class="intro">Les textes de fond publiés avant octobre 2026 par des autorités publiques, des ordres et des chercheurs : cadres, plans, lignes directrices et propositions de normes. Seuls les documents de haut niveau y figurent.</p>
      </div>
      <div class="rapport">
        <div class="rubrique">
{chr(10).join(bloc_doc(d) for d in sorted(refs, key=lambda d: d['date'], reverse=True))}
        </div>
      </div>
    </section>"""
    entete = f"""{SURTITRE}
    <h1>Veille IA clinique</h1>
    <p class="sous-titre">Ce que publient les instances de santé, les ordres et la presse sur l'usage de l'intelligence artificielle par les cliniciens. Un rapport par mois, préparé pour le comité d'innovation et de développement professionnel (CIDP).</p>
    <nav class="onglets" aria-label="Sections">
      <a href="#rapports">Rapports</a>
      <a href="#references">Documents de référence</a>
    </nav>"""
    return page("Veille IA clinique", corps, "assets/style.css", entete)

def main():
    rapports = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RACINE, "data", "rapports", "*.json")), reverse=True)]
    refs = json.load(open(os.path.join(RACINE, "data", "references.json")))
    erreurs = verifier(rapports, refs)
    if erreurs:
        print("Site non généré :")
        for x in erreurs:
            print("  -", x)
        return 1
    os.makedirs(os.path.join(RACINE, "rapports"), exist_ok=True)
    for r in rapports:
        open(os.path.join(RACINE, "rapports", f"{r['mois']}.html"), "w").write(page_rapport(r))
    open(os.path.join(RACINE, "index.html"), "w").write(page_accueil(rapports, refs))
    print(f"Site généré : {len(rapports)} rapport(s), {sum(nb_docs(r) for r in rapports)} document(s), {len(refs)} référence(s).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
