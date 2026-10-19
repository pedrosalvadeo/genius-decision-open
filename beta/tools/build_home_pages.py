"""Write the home page in English (/, static/index.html) and Spanish (/es, static/index.es.html).

One source keeps both languages in sync. The charts read static/world-indicators.json
(beta/tools/world_indicators.py) and the ring reads static/boundaries.json; the decision
animation in static/horizon.js uses the Earth twin (twin/cases/earth_2105). Run from the
repository root after editing:
    python beta/tools/build_home_pages.py
"""
import random
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "genius_beta" / "static"
REPO = "https://github.com/pedrosalvadeo/genius-decision-open"


def sky():
    rnd = random.Random(7)  # fixed stars, so rebuilding the page changes nothing
    stars = "".join(
        f'<circle class="star" cx="{rnd.uniform(0, 1440):.0f}" cy="{rnd.uniform(0, 560) ** 1.08 / 1.6:.0f}" r="{rnd.choice((0.8, 1, 1.2, 1.6)):.1f}"/>'
        for _ in range(90))
    return ('<div class="sky" aria-hidden="true"><svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMax slice">'
            '<defs><radialGradient id="sun" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff4cf"/><stop offset=".18" stop-color="#ffe6a8"/>'
            '<stop offset=".45" stop-color="#f0c27f" stop-opacity=".45"/><stop offset="1" stop-color="#f0c27f" stop-opacity="0"/></radialGradient>'
            '<linearGradient id="planet" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1f4a3c"/><stop offset=".25" stop-color="#0f2a24"/><stop offset="1" stop-color="#0a1b18"/></linearGradient>'
            '<linearGradient id="rim" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#9fd1b0" stop-opacity="0"/><stop offset=".5" stop-color="#fff1c4"/><stop offset="1" stop-color="#9fd1b0" stop-opacity="0"/></linearGradient></defs>'
            f'<g>{stars}</g>'
            '<g class="sun-glow"><circle cx="1010" cy="740" r="430" fill="url(#sun)"/><circle cx="1010" cy="742" r="54" fill="#fff4cf"/></g>'
            '<circle cx="720" cy="2380" r="1640" fill="url(#planet)"/><circle class="planet-rim" cx="720" cy="2380" r="1640"/>'
            '<g fill="none" stroke="#cfe3c4" stroke-opacity=".12"><ellipse cx="720" cy="900" rx="900" ry="120"/><ellipse cx="720" cy="900" rx="620" ry="70"/></g>'
            '</svg></div>')


def page(lang):
    en = lang == "en"
    t = lambda a, b: a if en else b
    home, other = t("/", "/es"), t("/es", "/")
    report, business, lab = t("/business/report", "/empresas/informe"), t("/business", "/empresas"), t("/lab", "/es/lab")
    goals = [
        (t("The nine planetary boundaries, back in the safe zone", "Los nueve límites planetarios, de vuelta en zona segura"),
         t("The conditions that keep Earth habitable for us and for the rest of life.", "Las condiciones que mantienen la Tierra habitable para nosotros y para el resto de la vida."),
         t("7 of 9 crossed", "7 de 9 cruzados"), t("0 crossed", "0 cruzados")),
        (t("Zero poverty and the Sustainable Development Goals", "Pobreza cero y los Objetivos de Desarrollo Sostenible"),
         t("No one living in poverty, and the 17 UN goals met without one being reached at the cost of another.", "Que nadie viva en la pobreza y que se cumplan los 17 objetivos de la ONU, sin que unos se logren a costa de otros."),
         t("1 in 10 people in extreme poverty", "1 de cada 10 personas en pobreza extrema"), t("0", "0")),
        ("Homo Genius",
         t("People with greater cognitive capacity, who see the consequences of their decisions for themselves, for others and for life.", "Personas con mayor capacidad cognitiva, que ven las consecuencias de sus decisiones para sí, para los demás y para la vida."),
         t("Not measured yet", "Todavía sin medición"), t("Every person", "Cada persona")),
        (t("A world where life is sustained and thrives", "Un mundo donde la vida se sostiene y prospera"),
         t("Every decision raises the wellbeing and the probability of sustained life (PVS) of everyone it touches.", "Cada decisión aumenta el bienestar y la probabilidad de vida sostenida (PVS) de todos los que afecta."),
         t("Earth's climate path: PVS 0", "Ruta climática de la Tierra: PVS 0"), "PVS 1"),
    ]
    goal_items = "".join(
        f'<li><h3>{h}</h3><p>{p}</p><dl class="goal-now"><dt>{t("TODAY", "HOY")}</dt><dd>{now}</dd><dt>{t("GOAL", "META")}</dt><dd>{goal}</dd></dl></li>'
        for h, p, now, goal in goals)
    steps = [
        (t("The decision", "La decisión"),
         t("Which path of emissions and deforestation does humanity take from 2025 to 2105? Four routes, from reaching zero by 2045 to keeping current policies.",
           "¿Qué ruta de emisiones y deforestación toma la humanidad de 2025 a 2105? Cuatro rutas, desde llegar a cero en 2045 hasta seguir con las políticas actuales."),
         t("Four routes humanity could take.", "Cuatro rutas que la humanidad podría tomar.")),
        (t("The scenarios", "Los escenarios"),
         t("Nobody knows how strongly the climate will respond to each tonne of CO₂. Each scenario has its own budget before passing 2 °C.",
           "Nadie sabe cuánto va a responder el clima a cada tonelada de CO₂. Cada escenario tiene su propio presupuesto antes de pasar 2 °C."),
         t("Three ways the climate could respond. The yellow line is each one's 2 °C budget.", "Tres formas en que el clima podría responder. La línea amarilla es el presupuesto de 2 °C de cada uno.")),
        (t("The kernel walks every route", "El kernel recorre cada ruta"),
         t("Decade by decade, in every scenario, it adds the CO₂ of each route and checks the life condition: never exceed the budget.",
           "Década por década y en cada escenario, suma el CO₂ de cada ruta y comprueba la condición de vida: no superar nunca el presupuesto."),
         t("Twelve trajectories, computed exactly. Red means the budget was exceeded in that decade.", "Doce trayectorias calculadas con exactitud. El rojo marca la década en que se superó el presupuesto.")),
        (t("The probability of sustained life", "La probabilidad de vida sostenida"),
         t("PVS is the probability that a route keeps life across the scenarios. With each scenario at one third, current policies get PVS 0.",
           "La PVS es la probabilidad de que una ruta conserve la vida entre los escenarios. Con un tercio para cada escenario, las políticas actuales tienen PVS 0."),
         t("PVS for each route, scenario by scenario.", "La PVS de cada ruta, escenario por escenario.")),
        (t("Life first", "Primero, la vida"),
         t("Any route that loses life in some scenario is set aside. No other benefit makes up for it.",
           "Toda ruta que pierde la vida en algún escenario queda fuera. Ningún otro beneficio la compensa."),
         t("Only one route keeps life in all three scenarios.", "Sólo una ruta conserva la vida en los tres escenarios.")),
        (t("The best route for each one affected", "Lo mejor para cada afectado"),
         t("Genius looks for the best route for each carrier separately and shows the conflicts. It never adds criteria into one number.",
           "Genius busca la mejor ruta para cada portador por separado y muestra los conflictos. Nunca suma criterios en un solo número."),
         t("Future generations, other species and fossil economies, each with its own wellbeing.", "Generaciones futuras, otras especies y economías fósiles, cada uno con su bienestar.")),
        (t("The recommendation", "La recomendación"),
         t("Reaching zero by 2045 is the only route that keeps life in every scenario: PVS 1. It is also the best for every carrier among the routes that keep life.",
           "Llegar a cero en 2045 es la única ruta que conserva la vida en todos los escenarios: PVS 1. También es la mejor para cada portador entre las rutas que la conservan."),
         t("Zero by 2045: PVS 1.", "A cero en 2045: PVS 1.")),
    ]
    step_items = "".join(
        f'<li data-caption="{cap}"><button type="button"><span class="n">{i + 1}</span><strong>{h}</strong><p>{p}</p></button></li>'
        for i, (h, p, cap) in enumerate(steps))
    return f'''<!doctype html>
<html lang="{t("en", "es-AR")}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{t("Genius calculates which decisions sustain life and wellbeing in every scenario, toward a horizon where the nine planetary boundaries are safe again.", "Genius calcula qué decisiones sostienen la vida y el bienestar en cada escenario, hacia un horizonte con los nueve límites planetarios de nuevo en zona segura.")}">
  <meta name="referrer" content="no-referrer">
  <meta name="theme-color" content="#0a1b18">
  <meta property="og:title" content="{t("Genius · Toward a horizon where life thrives", "Genius · Hacia un horizonte donde la vida prospera")}">
  <meta property="og:description" content="{t("Decisions computed scenario by scenario, so life is sustained and thrives.", "Decisiones calculadas escenario por escenario, para que la vida se sostenga y prospere.")}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://geniusdecision.app{home}">
  <link rel="canonical" href="https://geniusdecision.app{home}">
  <link rel="alternate" hreflang="en" href="https://geniusdecision.app/">
  <link rel="alternate" hreflang="es" href="https://geniusdecision.app/es">
  <link rel="stylesheet" href="/static/home.css">
  <link rel="stylesheet" href="/static/horizon.css">
  <link rel="service-desc" type="application/vnd.oai.openapi+json" href="/openapi.json">
  <title>{t("Genius · Toward a horizon where life thrives", "Genius · Hacia un horizonte donde la vida prospera")}</title>
</head>
<body>
<a class="skip-link" href="#main">{t("Skip to content", "Ir al contenido")}</a>
<div class="horizon-hero">
{sky()}
<header class="site-header">
  <a class="brand" href="{home}" aria-label="{t("Genius Decision, home", "Genius Decision, inicio")}"><span class="brand-mark" aria-hidden="true">g</span><span>genius<small>DECISION</small></span></a>
  <nav aria-label="{t("Main navigation", "Navegación principal")}"><a href="#horizonte">{t("The horizon", "El horizonte")}</a><a href="#progreso">{t("The world can turn", "El mundo puede girar")}</a><a href="#como">{t("How Genius decides", "Cómo decide Genius")}</a><a href="#producto">{t("Product", "Producto")}</a><a href="{lab}">{t("Lab", "Laboratorio")}</a></nav>
  <a class="lang-switch" href="{other}" hreflang="{t("es", "en")}" lang="{t("es", "en")}" title="{t("Leer esta página en español", "Read this page in English")}">{t("Español", "English")}</a>
  <a class="header-entry" href="{report}">{t("Make a decision", "Tomar una decisión")} <span aria-hidden="true">↗</span></a>
</header>
<section class="hero-inner section-wrap" aria-labelledby="hero-title">
  <p class="eyebrow"><span class="status-dot" aria-hidden="true"></span> {t("OPEN RESEARCH · PUBLIC BETA", "INVESTIGACIÓN ABIERTA · BETA PÚBLICA")}</p>
  <h1 id="hero-title">{t("Toward a horizon <br><em>where life thrives.</em>", "Hacia un horizonte <br><em>donde la vida prospera.</em>")}</h1>
  <p class="hero-lead">{t("Every second, decisions shape the future: making a sandwich, launching a product, setting up an economic system. Genius calculates which ones sustain life and the wellbeing of everyone they touch, in every possible scenario.", "Cada segundo, las decisiones dan forma al futuro: hacer un sándwich, lanzar un producto, establecer un sistema económico. Genius calcula cuáles sostienen la vida y el bienestar de todos los que afectan, en cada escenario posible.")}</p>
  <div class="actions"><a class="button dawn" href="{report}">{t("Decide within the planetary boundaries", "Decidir dentro de los límites planetarios")} <span aria-hidden="true">↗</span></a><a class="text-link" href="#como">{t("See how Genius decides ↓", "Ver cómo decide Genius ↓")}</a></div>
</section>
</div>
<main id="main">
  <section id="horizonte" class="goals-section" aria-labelledby="goals-title"><div class="section-wrap">
    <div class="section-heading"><p class="eyebrow">01 / {t("THE HORIZON", "EL HORIZONTE")}</p><div><h2 id="goals-title">{t("Where we are <br>going together.", "Hacia dónde <br>vamos juntos.")}</h2><p class="section-lead">{t("Four goals, one way to reach them: changing how decisions are made, and which ones, every second.", "Cuatro metas y un solo camino para alcanzarlas: cambiar cómo y qué decisiones se toman, cada segundo.")}</p></div></div>
    <ol class="goal-line">{goal_items}</ol>
    <p class="goal-note">{t(f'Sources: 7 of 9 boundaries crossed, <a href="https://www.planetaryhealthcheck.org/">Planetary Health Check 2025</a>. Extreme poverty in 2024, World Bank (chart below). Climate path PVS, <a href="{REPO}/tree/main/twin/cases/earth_2105">Earth twin</a>, a model with declared hypotheses that only includes climate and forests.', f'Fuentes: 7 de 9 límites cruzados, <a href="https://www.planetaryhealthcheck.org/">Planetary Health Check 2025</a>. Pobreza extrema en 2024, Banco Mundial (gráfico más abajo). PVS de la ruta climática, <a href="{REPO}/tree/main/twin/cases/earth_2105">gemelo de la Tierra</a>, un modelo con hipótesis declaradas que sólo incluye clima y bosques.')}</p>
  </div></section>

  <section id="progreso" class="progress-section section-wrap" aria-labelledby="progress-title">
    <div class="section-heading"><p class="eyebrow">02 / {t("THE WORLD CAN TURN", "EL MUNDO PUEDE GIRAR")}</p><div><h2 id="progress-title">{t("When humanity decides <br>differently, the world changes.", "Cuando la humanidad decide <br>distinto, el mundo cambia.")}</h2><p class="section-lead">{t("These are world indicators from public sources. Each one moved because millions of decisions changed.", "Son indicadores mundiales de fuentes públicas. Cada uno se movió porque cambiaron millones de decisiones.")}</p></div></div>
    <div id="indicator-grid" class="indicator-grid"><p class="indicator loading">{t("Loading the indicators…", "Cargando los indicadores…")}</p></div>
    <div class="reality-check"><h3>{t("It is not enough yet.", "Todavía no alcanza.")}</h3><p>{t("The ozone layer shows a planetary boundary can be protected when the world agrees to decide differently (Montreal Protocol, 1987). But <strong>7 of the 9 boundaries are crossed</strong>, and the current climate path keeps life in none of the scenarios. Decisions have to change everywhere, and faster.", "La capa de ozono muestra que un límite planetario se puede proteger cuando el mundo acuerda decidir distinto (Protocolo de Montreal, 1987). Pero <strong>7 de los 9 límites están cruzados</strong>, y la ruta climática actual no conserva la vida en ninguno de los escenarios. Las decisiones tienen que cambiar en todas partes, y más rápido.")}</p></div>
  </section>

  <section id="como" class="decide-section" aria-labelledby="decide-title"><div class="section-wrap">
    <div class="section-heading"><p class="eyebrow">03 / {t("HOW GENIUS DECIDES", "CÓMO DECIDE GENIUS")}</p><div><h2 id="decide-title">{t("From a question <br>to the best decision.", "De una pregunta <br>a la mejor decisión.")}</h2><p class="section-lead">{t("An AI can draft the model of a decision, but it does not choose. The Genius kernel computes every route in every scenario. Here it is, step by step, with Earth's climate.", "Una IA puede redactar el modelo de una decisión, pero no elige. El kernel de Genius calcula cada ruta en cada escenario. Acá lo ves paso a paso, con el clima de la Tierra.")}</p></div></div>
    <div class="decide">
      <div><ol id="decide-steps" class="decide-steps">{step_items}</ol>
        <div class="decide-controls"><button type="button" id="decide-prev">← {t("Back", "Atrás")}</button><button type="button" id="decide-play" aria-pressed="false">{t("Play", "Reproducir")}</button><button type="button" id="decide-next">{t("Next", "Siguiente")} →</button></div></div>
      <div id="decide-stage" class="decide-stage" data-step="0" aria-live="polite">
        <p class="stage-caption"></p>
        <div class="matrix"></div>
        <div class="carriers"></div>
        <div class="stage-legend"><span><i></i>{t("CO₂ emitted, within budget", "CO₂ emitido, dentro del presupuesto")}</span><span><i class="lose"></i>{t("budget exceeded: life is lost", "presupuesto superado: se pierde la vida")}</span><span><i class="line"></i>{t("2 °C budget", "presupuesto de 2 °C")}</span></div>
      </div>
    </div>
    <p class="decide-foot">{t(f'Data: the <a href="{REPO}/tree/main/twin/cases/earth_2105">Earth twin 2025–2105</a>. 2 °C budgets from IPCC AR6, 42.2 GtCO₂ emitted in 2025 (Global Carbon Budget 2025), one third for each scenario because the IPCC gives no likelihoods. It only includes climate and forests; with the other crossed boundaries, the PVS can only be equal or lower.', f'Datos: el <a href="{REPO}/tree/main/twin/cases/earth_2105">gemelo de la Tierra 2025–2105</a>. Presupuestos de 2 °C del IPCC AR6, 42,2 GtCO₂ emitidas en 2025 (Global Carbon Budget 2025) y un tercio para cada escenario, porque el IPCC no da probabilidades. Sólo incluye clima y bosques; con los demás límites cruzados, la PVS sólo puede ser igual o menor.')}</p>
  </div></section>

  <section id="producto" class="product-section section-wrap" aria-labelledby="product-title">
    <div class="section-heading"><p class="eyebrow">04 / {t("THE FIRST PRODUCT", "EL PRIMER PRODUCTO")}</p><div><h2 id="product-title">{t("Decide within <br>the nine boundaries.", "Decidir dentro <br>de los nueve límites.")}</h2><p class="section-lead">{t("A decision report for companies and organizations: every route of a decision, in every scenario, against the planetary boundaries.", "Un informe de decisión para empresas y organizaciones: cada ruta de una decisión, en cada escenario, frente a los límites planetarios.")}</p></div></div>
    <div class="product">
      <div class="boundary-visual"><div id="boundary-ring"></div><ul id="boundary-list" class="boundary-list"></ul></div>
      <div class="product-copy">
        <h3>{t("A supplier, a plant, a product, a goal.", "Un proveedor, una planta, un producto, una meta.")}</h3>
        <p>{t("You describe the decision in your words. Genius returns which routes keep life, where each one leaves each boundary, and what is best for the company, its workers, the community and nature.", "Describís la decisión con tus palabras. Genius devuelve qué rutas conservan la vida, dónde deja cada una cada límite y qué es lo mejor para la empresa, sus trabajadores, la comunidad y la naturaleza.")}</p>
        <ol class="product-steps">
          <li><span>1</span>{t("An AI drafts the model: routes, scenarios and everyone affected, with each assumed number marked as a hypothesis.", "Una IA arma el modelo: rutas, escenarios y todos los afectados, con cada número supuesto marcado como hipótesis.")}</li>
          <li><span>2</span>{t("The kernel computes every route in every scenario: life condition, PVS and the best route for each one affected.", "El kernel calcula cada ruta en cada escenario: condición de vida, PVS y la mejor ruta para cada afectado.")}</li>
          <li><span>3</span>{t("You get a printable report, with the laws that apply and every hypothesis editable.", "Recibís un informe imprimible, con las leyes que aplican y cada hipótesis editable.")}</li>
        </ol>
        <div class="actions"><a class="button primary" href="{report}">{t("Generate a report", "Generar un informe")} <span aria-hidden="true">↗</span></a><a class="text-link" href="{business}">{t("Genius for companies", "Genius para empresas")}</a></div>
        <p class="product-source">{t("Free in beta with an account. Boundaries: Planetary Health Check 2025.", "Gratis en la beta, con cuenta. Límites: Planetary Health Check 2025.")}</p>
      </div>
    </div>
  </section>

  <section class="roots-section" aria-labelledby="roots-title"><div class="section-wrap">
    <div class="section-heading"><p class="eyebrow">05 / {t("FOUNDATIONS", "FUNDAMENTOS")}</p><div><h2 id="roots-title">{t("A philosophy <br>and a mathematics.", "Una filosofía <br>y una matemática.")}</h2></div></div>
    <div class="roots">
      <article><h3>Homo Genius</h3><p>{t("A philosophical proposal by Pedro Salvadeo: direct intelligence toward protecting life, enriching its diversity and widening the possibilities of wellbeing.", "Una propuesta filosófica de Pedro Salvadeo: orientar la inteligencia a proteger la vida, enriquecer su diversidad y ampliar las posibilidades de bienestar.")}</p><a href="{REPO}/blob/main/capsule/HOMO_GENIUS.md">{t("Read Homo Genius", "Leer Homo Genius")} ↗</a></article>
      <article><h3>{t("Genius Mathematics", "Matemática Genius")}</h3><p>{t("Eight modules to represent systems, explore futures and compare decisions by wellbeing, generative capacity and the probability of sustained life, without adding criteria into one number.", "Ocho módulos para representar sistemas, explorar futuros y comparar decisiones por bienestar, capacidad generativa y probabilidad de vida sostenida, sin sumar criterios en un solo número.")}</p><a href="{REPO}/blob/main/GENIUS_PROGRAM/theory/sources/S1_READABLE.md">{t("Read Genius Mathematics", "Leer Matemática Genius")} ↗</a></article>
    </div>
  </div></section>

  <section class="lab-teaser section-wrap" aria-labelledby="lab-title">
    <div><p class="eyebrow">06 / {t("THE LAB", "EL LABORATORIO")}</p><h2 id="lab-title">{t("Where Genius learns.", "Donde Genius aprende.")}</h2><p>{t("Real cases of water, blood and Earth's climate, dynamic twins, and tools for AI agents and developers. They are first steps in a few domains, with many more still to reach.", "Casos reales de agua, sangre y el clima de la Tierra, gemelos dinámicos y herramientas para agentes de IA y desarrolladores. Son primeros pasos en pocos dominios, con muchos más por alcanzar.")}</p></div>
    <div class="lab-links"><a href="{lab}">{t("Visit the lab", "Visitar el laboratorio")} <span aria-hidden="true">→</span></a><a href="/app?next=/twin/">{t("Open the dynamic twin", "Abrir el gemelo dinámico")} <span aria-hidden="true">↗</span></a><a href="/agents">{t("I am an AI agent", "Soy un agente de IA")} <span aria-hidden="true">↗</span></a><a href="{REPO}">{t("Open code on GitHub", "Código abierto en GitHub")} <span aria-hidden="true">↗</span></a></div>
  </section>
</main>
<footer class="site-footer section-wrap"><a class="brand" href="{home}" aria-label="{t("Back to home", "Volver al inicio")}"><span class="brand-mark" aria-hidden="true">g</span><span>genius<small>DECISION</small></span></a><p>{t("An initiative by Pedro Salvadeo. <br>Philosophy, mathematics and technology in service of life.", "Una iniciativa de Pedro Salvadeo. <br>Filosofía, matemática y tecnología al servicio de la vida.")}</p><nav aria-label="{t("Footer links", "Enlaces del pie")}"><a href="{business}">{t("For companies", "Empresas")}</a><a href="{lab}">{t("Lab", "Laboratorio")}</a><a href="/agents">{t("Agents", "Agentes")}</a><a href="/app">{t("Application", "Aplicación")}</a><a href="/static/privacy.html">{t("Privacy", "Privacidad")}</a><a href="{other}" hreflang="{t("es", "en")}" lang="{t("es", "en")}">{t("Español", "English")}</a><a href="{REPO}">GitHub <span aria-hidden="true">↗</span></a></nav></footer>
<script src="/static/horizon.js" defer></script>
</body>
</html>
'''


if __name__ == "__main__":
    (STATIC / "index.html").write_text(page("en"), encoding="utf-8")
    (STATIC / "index.es.html").write_text(page("es"), encoding="utf-8")
