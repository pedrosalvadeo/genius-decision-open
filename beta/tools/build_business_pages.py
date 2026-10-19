"""Write the Genius for companies pages (/business in English, /empresas in Spanish) from one source.

The nine planetary boundaries and the laws come from static/boundaries.json, which the
decision report reads too. Run from the repository root after changing either:
    python beta/tools/build_business_pages.py
"""
import html
import json
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "genius_beta" / "static"


def page(lang, data):
    en = lang == "en"
    t = lambda a, b: a if en else b
    rep = t("/business/report", "/empresas/informe")
    home = t("/", "/es")
    name = {b["id"]: b[lang]["name"] for b in data["boundaries"]}

    def li(n, h, p, s):
        return f'<li><span class="roadmap-number">{n}</span><div><h3>{h}</h3><p>{p}</p></div><span class="roadmap-state">{s}</span></li>'

    checks = "".join(
        f'<article class="check {"crossed" if b["crossed"] else "safe"}"><span class="state">'
        f'{t("CROSSED", "CRUZADO") if b["crossed"] else t("SAFE ZONE", "ZONA SEGURA")}</span>'
        f'<h3>{html.escape(b[lang]["name"])}</h3><p>{html.escape(b[lang]["company"])}</p></article>'
        for b in data["boundaries"])
    crossed = sum(b["crossed"] for b in data["boundaries"])
    lower = [
        li("01", t("Measure the room each route leaves", "Medir el margen que deja cada ruta"),
           t("Each report finds the boundaries a decision touches and calculates where every route leaves them, at the end and at the worst moment, in every scenario.",
             "Cada informe encuentra los límites que toca una decisión y calcula dónde los deja cada ruta, al final y en el peor momento, en cada escenario."), t("PER DECISION", "POR DECISIÓN")),
        li("02", t("Drop the routes that lose life", "Descartar las rutas que pierden la vida"),
           t("A route that breaks the life condition of people or living systems in any scenario is flagged first, however profitable it looks.",
             "Una ruta que rompe la condición de vida de personas o sistemas vivos en algún escenario queda marcada primero, aunque parezca rentable."), t("FIRST FILTER", "PRIMER FILTRO")),
        li("03", t("Show the route that leaves the most room, and who pays", "Mostrar la ruta que más margen deja, y quién paga"),
           t("Among the routes that keep life, the report shows which ones leave each boundary with the most room and what each affected party gains or loses, without adding them into one score.",
             "Entre las rutas que conservan la vida, el informe muestra cuáles dejan más margen en cada límite y qué gana o pierde cada afectado, sin sumarlo en un puntaje."), t("NO SUMS", "SIN SUMAS")),
        li("04", t("Add decisions up, and check against reality", "Sumar decisiones y contrastar con la realidad"),
           t("A boundary is crossed by millions of decisions and comes back the same way. Calculated decisions are followed against what happens, and the Earth twin measures the progress: today it covers climate and forests.",
             "Un límite se cruza por millones de decisiones y vuelve de la misma manera. Las decisiones calculadas se siguen contra lo que pasa, y el gemelo de la Tierra mide el avance: hoy cubre clima y bosques."), t("PLANET", "PLANETA")),
    ]
    laws = "".join(
        f'<tr><td><a href="{html.escape(x["url"])}">{html.escape(x[lang]["name"])}</a></td><td>{html.escape(x[lang]["asks"])}</td>'
        f'<td>{html.escape(x[lang]["who"])}</td><td>{html.escape(", ".join(name[b] for b in x["boundaries"]))}</td></tr>'
        for x in data["laws"])
    gives = [
        li("01", t("Life and PVS for every route and scenario", "Vida y PVS para cada ruta y escenario"),
           t("Which routes keep the life condition of the people and living systems affected in every scenario, and their probability of sustained life (PVS).",
             "Qué rutas conservan la condición de vida de las personas y los sistemas vivos afectados en cada escenario, y su probabilidad de vida sostenida (PVS)."), t("FIRST FILTER", "PRIMER FILTRO")),
        li("02", t("The nine boundaries, and the ones this decision touches", "Los nueve límites, y los que toca esta decisión"),
           t("Where each route leaves each boundary the decision touches, and which routes leave the most room.",
             "Dónde deja cada ruta cada límite que toca la decisión, y qué rutas dejan más margen."), t("9 CHECKS", "9 CHECKS")),
        li("03", t("What is best for each affected party", "Lo mejor para cada afectado"),
           t("The company, its workers, the community and nature each get their best routes. When they disagree, the report shows the conflict.",
             "La empresa, sus trabajadores, la comunidad y la naturaleza tienen cada uno sus mejores rutas. Cuando no coinciden, el informe muestra el conflicto."), t("NO SUMS", "SIN SUMAS")),
        li("04", t("The laws that apply", "Las leyes que aplican"),
           t("For each boundary the decision touches, the frameworks that already ask companies to assess it, so the report can feed their analysis.",
             "Para cada límite que toca la decisión, los marcos que ya piden a las empresas evaluarlo, para que el informe alimente ese análisis."), t("COMPLIANCE", "CUMPLIMIENTO")),
        li("05", t("Every hypothesis in view, and editable", "Cada hipótesis a la vista, y editable"),
           t("Every number the AI had to assume is marked. Your team corrects it with real data and the kernel recalculates in seconds, without the AI. The report prints or saves as PDF.",
             "Cada número que la IA tuvo que suponer queda marcado. Tu equipo lo corrige con datos reales y el kernel recalcula en segundos, sin la IA. El informe se imprime o se guarda en PDF."), t("AUDITABLE", "AUDITABLE")),
    ]

    def card(idx, tag, title, desc, body, links=""):
        return (f'<details class="component" open><summary><span class="component-top"><span class="component-index">{idx}</span><span class="tag">{tag}</span></span>'
                f'<strong>{title}</strong><span class="component-description">{desc}</span><span class="expand" aria-hidden="true">+</span></summary>'
                f'<div class="component-body"><p>{body}</p>{links}</div></details>')

    plans = [
        card(t("ANY TEAM", "CUALQUIER EQUIPO"), t("Available in beta", "Disponible en beta"), t("Decision report", "Informe de decisión"),
             t("One decision, modelled and calculated in about a minute.", "Una decisión, modelada y calculada en cerca de un minuto."),
             t("Free during the beta with a Genius account, up to 20 reports per day. The description is not stored.", "Gratis durante la beta con una cuenta de Genius, hasta 20 informes por día. La descripción no se guarda."),
             f'<a href="{rep}">{t("Generate a report", "Generar un informe")} <span aria-hidden="true">↗</span></a>'),
        card(t("ONE REAL DECISION", "UNA DECISIÓN REAL"), t("Opening soon", "Próximamente"), t("Pilot", "Piloto"),
             t("Your decision, modelled with your team and your data.", "Tu decisión, modelada con tu equipo y tus datos."),
             t("We build the model with your data and sources, run it as a living twin and follow it against what happens.", "Armamos el modelo con tus datos y fuentes, lo corremos como un gemelo vivo y lo seguimos contra lo que pasa.")),
        card(t("SUSTAINABILITY AND STRATEGY", "SOSTENIBILIDAD Y ESTRATEGIA"), t("Opening soon", "Próximamente"), t("Company", "Empresa"),
             t("The year's important decisions, for the whole team.", "Las decisiones importantes del año, para todo el equipo."),
             t("Team accounts, decisions saved with permission, reports for double-materiality and scenario analysis, and access by API and MCP.", "Cuentas de equipo, decisiones guardadas con permiso, informes para el análisis de doble materialidad y de escenarios, y acceso por API y MCP.")),
        card(t("ADVISORS", "CONSULTORAS"), t("Opening soon", "Próximamente"), t("Consultancy", "Consultora"),
             t("Calculation behind your scenario workshops.", "Cálculo detrás de tus talleres de escenarios."),
             t("Use Genius with your clients: the same report, with your own cases.", "Usá Genius con tus clientes: el mismo informe, con tus propios casos.")),
    ]
    uses = t(["Switching a supplier of cotton, soy or minerals", "Opening a plant or farm in a water-stressed basin", "Launching a product or a new packaging", "Setting the path to an emissions or nature target", "Choosing between investments or sites"],
             ["Cambiar de proveedor de algodón, soja o minerales", "Abrir una planta o una finca en una cuenca con poca agua", "Lanzar un producto o un envase nuevo", "Fijar el camino a una meta de emisiones o de naturaleza", "Elegir entre inversiones o ubicaciones"])
    src = data["source"]
    return f'''<!doctype html>
<html lang="{t('en', 'es-AR')}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{t('Genius for companies: decisions that bring the nine planetary boundaries back to the safe zone, calculated route by route and scenario by scenario.', 'Genius para empresas: decisiones que llevan los nueve límites planetarios de vuelta a la zona segura, calculadas ruta por ruta y escenario por escenario.')}">
  <meta name="referrer" content="no-referrer">
  <meta name="theme-color" content="#173f35">
  <link rel="canonical" href="https://geniusdecision.app{t('/business', '/empresas')}">
  <link rel="alternate" hreflang="en" href="https://geniusdecision.app/business">
  <link rel="alternate" hreflang="es" href="https://geniusdecision.app/empresas">
  <link rel="stylesheet" href="/static/home.css">
  <link rel="stylesheet" href="/static/organisms.css">
  <link rel="stylesheet" href="/static/business.css">
  <title>{t('Genius for companies · Decisions within the planetary boundaries', 'Genius para empresas · Decisiones dentro de los límites planetarios')}</title>
</head>
<body>
<a class="skip-link" href="#main">{t('Skip to content', 'Ir al contenido')}</a>
<header class="site-header">
  <a class="brand" href="{home}" aria-label="{t('Genius Decision, home', 'Genius Decision, inicio')}"><span class="brand-mark" aria-hidden="true">g</span><span>genius<small>DECISION</small></span></a>
  <nav aria-label="{t('Companies', 'Empresas')}"><a href="#checks">{t('9 checks', '9 checks')}</a><a href="#laws">{t('The law', 'La ley')}</a><a href="#report">{t('The report', 'El informe')}</a><a href="#plans">{t('Plans', 'Planes')}</a></nav>
  <a class="lang-switch" href="{t('/empresas', '/business')}" hreflang="{t('es', 'en')}" lang="{t('es', 'en')}">{t('Español', 'English')}</a>
  <a class="header-entry" href="{rep}">{t('Try it', 'Probar')} <span aria-hidden="true">↗</span></a>
</header>
<main id="main">
  <section class="hero solo-hero section-wrap" aria-labelledby="hero-title">
    <div class="hero-copy">
      <p class="eyebrow"><span class="status-dot" aria-hidden="true"></span> {t('GENIUS FOR COMPANIES · PUBLIC BETA', 'GENIUS PARA EMPRESAS · BETA PÚBLICA')}</p>
      <h1 id="hero-title">{t('Bring the <br>nine checks <br><em>back to zero.</em>', 'Llevar los <br>nueve checks <br><em>de vuelta a cero.</em>')}</h1>
      <p class="hero-lead">{t(f'Earth has crossed {crossed} of the nine planetary boundaries that keep it habitable. They were crossed one decision at a time, and that is how they come back: Genius calculates each company decision route by route, so the one that leaves the most room for life can be chosen before deciding.', f'La Tierra cruzó {crossed} de los nueve límites planetarios que la mantienen habitable. Se cruzaron de a una decisión por vez, y así vuelven: Genius calcula cada decisión de una empresa ruta por ruta, para elegir antes de decidir la que más margen deja a la vida.')}</p>
      <p class="hero-description">{t('And the law already asks companies to assess these impacts.', 'Y la ley ya les pide a las empresas evaluar esos impactos.')}</p>
      <div class="actions"><a class="button primary" href="{rep}">{t('Generate a decision report', 'Generar un informe de decisión')} <span aria-hidden="true">↗</span></a><a class="text-link" href="#checks">{t('See the nine checks ↓', 'Ver los nueve checks ↓')}</a></div>
    </div>
  </section>

  <section id="checks" class="horizon-section" aria-labelledby="checks-title"><div class="section-wrap">
    <div class="section-heading"><p class="eyebrow">01 / {t('THE NINE CHECKS', 'LOS NUEVE CHECKS')}</p><div><h2 id="checks-title">{t(f'{crossed} of 9 crossed. <br>The goal is zero.', f'{crossed} de 9 cruzados. <br>La meta es cero.')}</h2><p class="section-lead">{t('Each boundary, its state today and what a company decision moves in it.', 'Cada límite, su estado hoy y qué mueve en él una decisión de empresa.')} <a href="{src['url']}">{html.escape(src[lang])}</a>.</p></div></div>
    <div class="checks">{checks}</div>
    <h3 class="sub-title">{t('How Genius helps bring them down', 'Cómo ayuda Genius a bajarlos')}</h3>
    <ol class="roadmap">{''.join(lower)}</ol>
  </div></section>

  <section id="laws" class="math-section section-wrap" aria-labelledby="laws-title">
    <div class="section-heading"><p class="eyebrow">02 / {t('THE LAW ALREADY ASKS', 'LA LEY YA LO PIDE')}</p><div><h2 id="laws-title">{t('Assessing impacts <br>is no longer optional.', 'Evaluar los impactos <br>ya no es opcional.')}</h2><p class="section-lead">{t('These frameworks ask companies to identify their impacts on the boundaries, often with scenario analysis. Genius gives that analysis a calculation: routes, scenarios, everyone affected and every hypothesis in view.', 'Estos marcos piden a las empresas identificar sus impactos sobre los límites, muchas veces con análisis de escenarios. Genius le da a ese análisis un cálculo: rutas, escenarios, todos los afectados y cada hipótesis a la vista.')}</p></div></div>
    <div class="law-wrap"><table class="law-table"><thead><tr><th>{t('Law or framework', 'Ley o marco')}</th><th>{t('What it asks', 'Qué pide')}</th><th>{t('Who and from when', 'A quién y desde cuándo')}</th><th>{t('Boundaries', 'Límites')}</th></tr></thead><tbody>{laws}</tbody></table></div>
    <p class="progress-link">{t('A guide to orient the analysis, not legal advice. Dates as of October 2026.', 'Una guía para orientar el análisis, no asesoramiento legal. Fechas a octubre de 2026.')}</p>
  </section>

  <section id="report" class="horizon-section" aria-labelledby="report-title"><div class="section-wrap">
    <div class="section-heading"><p class="eyebrow">03 / {t('THE REPORT', 'EL INFORME')}</p><div><h2 id="report-title">{t('What your team <br>gets for each decision.', 'Lo que recibe tu equipo <br>por cada decisión.')}</h2><p class="section-lead">{t('Read from the kernel and never added into a single score.', 'Leído del kernel y nunca sumado en un puntaje único.')}</p></div></div>
    <ol class="roadmap">{''.join(gives)}</ol>
  </div></section>

  <section id="uses" class="ecosystem-section section-wrap" aria-labelledby="uses-title">
    <div class="section-heading"><p class="eyebrow">04 / {t('USES', 'USOS')}</p><div><h2 id="uses-title">{t('Decisions that <br>move the checks.', 'Decisiones que <br>mueven los checks.')}</h2><p class="section-lead">{t('For sustainability, strategy and operations teams, and for the advisors who support them.', 'Para equipos de sostenibilidad, estrategia y operaciones, y para las consultoras que los acompañan.')}</p></div></div>
    <ul class="roadmap">{''.join(f'<li><span class="roadmap-number">→</span><div><h3>{u}</h3></div><span class="roadmap-state"></span></li>' for u in uses)}</ul>
  </section>

  <section id="plans" class="ecosystem-section plans-section section-wrap" aria-labelledby="plans-title">
    <div class="section-heading"><p class="eyebrow">05 / {t('PLANS', 'PLANES')}</p><div><h2 id="plans-title">{t('Start with one decision.', 'Empezá con una decisión.')}</h2><p class="section-lead">{t('The report is free during the beta. Pilots and team plans are opening soon.', 'El informe es gratis durante la beta. Los pilotos y los planes para equipos se abren pronto.')}</p></div></div>
    <div class="component-grid">{''.join(plans)}</div>
  </section>

  <section class="join-section section-wrap" aria-labelledby="join-title"><p class="eyebrow">{t('OPEN AND VERIFIABLE', 'ABIERTO Y VERIFICABLE')}</p><h2 id="join-title">{t('A calculation you <br>can examine.', 'Un cálculo que <br>se puede examinar.')}</h2><p>{t('The kernel and the mathematics are open source under Apache-2.0. Every result can be reproduced from the model it comes from.', 'El kernel y la matemática son de código abierto, con licencia Apache-2.0. Cada resultado se puede reproducir a partir del modelo del que sale.')}</p><div class="actions"><a class="button primary" href="{rep}">{t('Generate a report', 'Generar un informe')} <span aria-hidden="true">↗</span></a><a class="text-link" href="https://github.com/pedrosalvadeo/genius-decision-open">{t('Code on GitHub', 'Código en GitHub')} <span aria-hidden="true">↗</span></a></div></section>
</main>
<footer class="site-footer section-wrap"><a class="brand" href="{home}" aria-label="{t('Back to home', 'Volver al inicio')}"><span class="brand-mark" aria-hidden="true">g</span><span>genius<small>DECISION</small></span></a><p>{t('An initiative by Pedro Salvadeo. <br>Philosophy, mathematics and technology in service of life.', 'Una iniciativa de Pedro Salvadeo. <br>Filosofía, matemática y tecnología al servicio de la vida.')}</p><nav aria-label="{t('Footer links', 'Enlaces del pie')}"><a href="/app">{t('Application', 'Aplicación')}</a><a href="/agents">{t('Agents', 'Agentes')}</a><a href="/static/privacy.html">{t('Privacy', 'Privacidad')}</a><a href="https://github.com/pedrosalvadeo/genius-decision-open">GitHub <span aria-hidden="true">↗</span></a></nav></footer>
</body>
</html>
'''


def main():
    data = json.loads((STATIC / "boundaries.json").read_text())
    (STATIC / "business.html").write_text(page("en", data))
    (STATIC / "empresas.html").write_text(page("es", data))


if __name__ == "__main__":
    main()
