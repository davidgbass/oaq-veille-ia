#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère le site de la veille IA clinique à partir des données JSON.

  data/rapports/AAAA-MM.json  un rapport mensuel (résumé, rubriques, documents, questions)
  data/references.json        documents de référence antérieurs à la veille

Sorties : index.html (liste des rapports, références, à propos) et rapports/AAAA-MM.html.
Le site est public (GitHub Pages) : seules des sources publiques y entrent.
Les documents du portail Concerto du CIQ n'y vont jamais.

Champ obligatoire « audio » : une ou deux phrases (au plus 45 mots) qui disent en
quoi le document touche les audioprothésistes ou l'Ordre, de près ou de loin.
Un document qui ne les touche pas n'a pas sa place sur le site (règle de David,
2026-10-21) : le script refuse de générer le site s'il manque une note.

Règles de contenu : au plus 5 documents par rapport (charge mentale du comité),
et chaque document porte un résumé d'une centaine de mots (80 à 130). Le script
refuse de générer le site si un rapport dépasse 5 documents, si un résumé sort
de cette fourchette ou si un texte contient un tiret cadratin ou demi-cadratin.
"""
import os, re, sys, json, glob, html, unicodedata
from urllib.parse import urlparse

RACINE = os.path.dirname(os.path.abspath(__file__))
MOTS_MIN, MOTS_MAX = 80, 130
DOCS_MAX = 5
AUDIO_MAX = 45
MOTS_MINUTE = 200
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]

def e(s):
    return html.escape(s, quote=True)

def nb_mots(s):
    return len(re.findall(r"[\wÀ-ÿ'’%,.-]+", s))

def slug(s, n=60):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].rstrip("-")

# ---------------- Contrôles ----------------
def verifier(rapports, refs):
    erreurs = []
    def doc(d, ou):
        n = nb_mots(d["resume"])
        if not MOTS_MIN <= n <= MOTS_MAX:
            erreurs.append(f"{ou} : « {d['titre'][:60]} » a {n} mots (attendu {MOTS_MIN} à {MOTS_MAX})")
        if not d.get("audio"):
            erreurs.append(f"{ou} : « {d['titre'][:60]} » n'a pas de note « Pour les audioprothésistes » : s'il ne nous touche pas, il ne va pas sur le site")
        elif nb_mots(d["audio"]) > AUDIO_MAX:
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

# ---------------- Aides ----------------
def docs_de(r):
    return [d for rub in r["rubriques"] for d in rub["documents"]]

def nb_docs(r):
    return len(docs_de(r))

def minutes(r):
    mots = nb_mots(r["resume"]) + sum(nb_mots(d["resume"]) + nb_mots(d.get("audio", "")) for d in docs_de(r)) \
        + sum(nb_mots(q) for q in r["questions"])
    return max(1, round(mots / MOTS_MINUTE))

def type_lien(url):
    hote = urlparse(url).netloc.removeprefix("www.").removeprefix("cms.")
    genre = "PDF" if url.lower().split("?")[0].endswith(".pdf") else "Page Web"
    return f"{genre} · {hote}"

def date_longue(iso):
    a, m, j = iso.split("-")
    return f"{int(j)}{'er' if j == '01' else ''} {MOIS[int(m) - 1]} {a}"

def prochain(mois):
    a, m = map(int, mois.split("-"))
    a2, m2 = (a + 1, 1) if m == 12 else (a, m + 1)
    a3, m3 = (a2 + 1, 1) if m2 == 12 else (a2, m2 + 1)
    return f"{MOIS[m2 - 1].capitalize()} {a2}", f"Prévu le 1er {MOIS[m3 - 1]} {a3}"

# ---------------- Gabarit ----------------
SCRIPT = """<script>
(function () {
  if (window.matchMedia && window.matchMedia("(max-width: 860px)").matches) {
    document.querySelectorAll(".sommaire details").forEach(function (d) { d.open = false; });
  }
  document.querySelectorAll("button.copier").forEach(function (b) {
    b.addEventListener("click", function () {
      var url = location.href.split("#")[0] + "#" + b.getAttribute("data-ancre");
      var fini = function () { b.textContent = "Lien copié"; setTimeout(function () { b.textContent = "Copier le lien"; }, 2000); };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(fini, function () { location.hash = b.getAttribute("data-ancre"); });
      else location.hash = b.getAttribute("data-ancre");
    });
  });
})();
</script>"""

def page(titre, corps, prefixe, entete, actif):
    liens = [("rapports", "Rapports"), ("references", "Documents de référence"), ("a-propos", "À propos")]
    nav = "\n".join(
        f'      <a href="{prefixe}index.html#{a}"{" aria-current=\"page\"" if a == actif else ""}>{t}</a>' for a, t in liens)
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titre)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,600;0,700;1,400&amp;display=swap">
<link rel="stylesheet" href="{prefixe}assets/style.css">
</head>
<body>
<a class="sauter" href="#contenu">Aller au contenu</a>
<nav class="barre" aria-label="Navigation principale">
  <div class="cadre barre-interieur">
    <a class="marque" href="{prefixe}index.html">Veille IA clinique</a>
    <div class="barre-liens">
{nav}
    </div>
  </div>
</nav>
<header class="bandeau">
  <div class="cadre">
{entete}
  </div>
</header>
<main id="contenu">
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
{SCRIPT}
</body>
</html>
"""

SURTITRE = '    <span class="surtitre">Ordre des audioprothésistes du Québec · Plan stratégique 2026-2029, actions 2.2.1 et 2.2.2</span>'

def bloc_doc(d, ancre):
    audio = ""
    if d.get("audio"):
        # facultatif : seulement quand le document s'applique à la pratique des audioprothésistes
        audio = f'\n            <p class="audio"><span class="audio-tag">Pour les audioprothésistes</span> {e(d["audio"])}</p>'
    return f"""        <div class="doc" id="{ancre}">
          <div class="meta"><span class="org">{e(d['organisme'])}</span><time datetime="{e(d['date'])}">{e(d['date_texte'])}</time><span class="puce">{e(d['categorie'])}</span></div>
          <div class="corps">
            <h4><a href="{e(d['url'])}" target="_blank" rel="noopener">{e(d['titre'])}</a></h4>
            <div class="source">{e(type_lien(d['url']))} <button type="button" class="copier" data-ancre="{ancre}">Copier le lien</button></div>
            <p>{e(d['resume'])}</p>{audio}
          </div>
        </div>"""

# ---------------- Pages ----------------
def page_rapport(r, precedent, suivant):
    ancres, sommaire, rubriques = {}, [], []
    for rub in r["rubriques"]:
        if not rub["documents"]:
            continue
        items, blocs = [], []
        for d in rub["documents"]:
            a = slug(d["titre"])
            ancres[d["titre"]] = a
            items.append(f'            <li><a href="#{a}">{e(d["organisme"])}</a></li>')
            blocs.append(bloc_doc(d, a))
        sommaire.append(f'        <li><span class="som-rub">{e(rub["titre"])}</span>\n          <ol>\n' + "\n".join(items) + "\n          </ol></li>")
        rubriques.append(f'      <div class="rubrique">\n        <h3>{e(rub["titre"])}</h3>\n' + "\n".join(blocs) + "\n      </div>")
    if not rubriques:
        rubriques.append('      <p class="vide">Rien de marquant ce mois-ci.</p>')
    questions = ""
    if r["questions"]:
        sommaire.append('        <li><a class="som-rub" href="#questions">Questions pour le CIDP</a></li>')
        questions = ('      <div class="questions" id="questions">\n        <h3>Questions pour le CIDP</h3>\n        <ol>\n'
                     + "\n".join(f"          <li>{e(q)}</li>" for q in r["questions"]) + "\n        </ol>\n      </div>")
    nav_rapports = '    <nav class="suite" aria-label="Autres rapports">\n'
    nav_rapports += (f'      <a href="{precedent["mois"]}.html" rel="prev">← {e(precedent["titre"])}</a>\n' if precedent else "      <span></span>\n")
    nav_rapports += (f'      <a href="{suivant["mois"]}.html" rel="next">{e(suivant["titre"])} →</a>\n' if suivant else "      <span></span>\n")
    nav_rapports += "    </nav>"
    docs = docs_de(r)
    corps = f"""    <div class="rapport-grille">
      <aside class="sommaire" aria-label="Dans ce rapport">
        <details open>
          <summary>Dans ce rapport</summary>
          <ol>
{chr(10).join(sommaire)}
          </ol>
        </details>
      </aside>
      <article class="rapport" id="documents" aria-labelledby="t-rapport">
{chr(10).join(rubriques)}
{questions}
      </article>
    </div>
{nav_rapports}"""
    entete = f"""{SURTITRE}
    <h1 id="t-rapport">{e(r['titre'])}</h1>
    <p class="sous-titre">{e(r['resume'])}</p>
    <p class="faits"><span>{len(docs)} documents</span><span>Lecture : {minutes(r)} min</span><span>Publié le {date_longue(r['publie'])}</span></p>
    <a class="retour" href="../index.html#rapports">← Tous les rapports</a>"""
    return page(f"Veille IA clinique, {r['titre']}", corps, "../", entete, "rapports")

def est_ordre(d):
    return d["organisme"].startswith(("Ordre", "Collège", "Chambre", "Barreau"))

def rubriques_refs(refs):
    groupes = [("Ordres professionnels", [d for d in refs if est_ordre(d)]),
               ("Autorités publiques et recherche", [d for d in refs if not est_ordre(d)])]
    return "\n".join(
        f'        <div class="rubrique">\n          <h3>{t}</h3>\n' + "\n".join(bloc_doc(d, "ref-" + slug(d["titre"])) for d in g) + "\n        </div>"
        for t, g in groupes if g)

def page_accueil(rapports, refs):
    lignes = []
    if rapports:
        titre, prevu = prochain(rapports[0]["mois"])
        lignes.append(f"""        <div class="rapport-ligne a-venir">
          <div><div class="mois">{titre}</div><div class="compte">{prevu}</div></div>
          <p>Collecte en cours.</p>
        </div>""")
    for r in rapports:
        docs = docs_de(r)
        lignes.append(f"""        <a class="rapport-ligne lien-bloc" href="rapports/{r['mois']}.html">
          <div><div class="mois">{e(r['titre'])}</div><div class="compte">{len(docs)} documents · {minutes(r)} min</div></div>
          <p>{e(r['resume'])} <span class="lire">Lire le rapport →</span></p>
        </a>""")
    refs = sorted(refs, key=lambda d: d["date"], reverse=True)
    corps = f"""    <section id="rapports" aria-labelledby="t-rapports">
      <div>
        <h2 id="t-rapports">Rapports</h2>
        <p class="intro">Un rapport par mois, au plus cinq documents, qui se lit en quelques minutes. Chacun se termine par quelques questions pour le comité.</p>
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
      <div class="rapport" id="liste-references">
{rubriques_refs(refs)}
      </div>
    </section>
    <section id="a-propos" aria-labelledby="t-apropos">
      <div>
        <h2 id="t-apropos">À propos</h2>
      </div>
      <div class="apropos">
        <p>Cette veille répond à deux actions du plan stratégique 2026-2029 de l'Ordre, toutes deux confiées au comité d'innovation et de développement professionnel : suivre l'évolution des usages de l'IA dans la pratique audioprothétique (2.2.2), et assurer la vigie des travaux du Conseil interprofessionnel du Québec (CIQ) sur l'IA (2.2.1). Elle porte sur l'usage de l'IA par les cliniciens, et non sur l'IA intégrée aux aides auditives.</p>
        <ul>
          <li>Les sources sont les instances de santé du Québec et du Canada, les 46 ordres professionnels du Québec et la presse. Les ordres de la santé et des relations humaines passent en premier.</li>
          <li>Chaque mois, au plus cinq documents sont retenus, en priorité les orientations d'une autorité québécoise et les données sur l'usage réel.</li>
          <li>Chaque document porte un résumé d'une centaine de mots, rédigé à partir du texte complet.</li>
          <li>Un document n'est retenu que s'il touche les audioprothésistes ou l'Ordre, de près ou de loin. Sa note « Pour les audioprothésistes » dit en quoi.</li>
          <li>Les études scientifiques sont exclues, car le comité en fait déjà la revue.</li>
          <li>Le suivi des travaux du CIQ réservés à ses membres est transmis au comité par courriel et ne figure pas sur ce site.</li>
        </ul>
      </div>
    </section>"""
    entete = f"""{SURTITRE}
    <h1>Veille IA clinique</h1>
    <p class="sous-titre">Ce que publient les instances de santé, les ordres et la presse sur l'usage de l'intelligence artificielle par les cliniciens. Un rapport par mois, préparé pour le comité d'innovation et de développement professionnel (CIDP).</p>"""
    if rapports:
        r = rapports[0]
        entete += f"""
    <a class="dernier" href="rapports/{r['mois']}.html">Dernier rapport : {e(r['titre'])} →</a>"""
    return page("Veille IA clinique", corps, "", entete, None)

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
    # rapports triés du plus récent au plus ancien : le « précédent » est le suivant dans la liste
    for i, r in enumerate(rapports):
        precedent = rapports[i + 1] if i + 1 < len(rapports) else None
        suivant = rapports[i - 1] if i > 0 else None
        open(os.path.join(RACINE, "rapports", f"{r['mois']}.html"), "w").write(page_rapport(r, precedent, suivant))
    open(os.path.join(RACINE, "index.html"), "w").write(page_accueil(rapports, refs))
    print(f"Site généré : {len(rapports)} rapport(s), {sum(nb_docs(r) for r in rapports)} document(s), {len(refs)} référence(s).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
