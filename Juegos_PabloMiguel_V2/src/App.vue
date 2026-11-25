<script setup>
import { computed, ref } from 'vue'
import games from './games.json'
import PacmanGame from './PacmanGame.vue'

const searchQuery = ref('')
const sortOrder = ref('newest')
const selectedGame = ref(null)
const failedImages = ref(new Set())
const ignoredKeywords = new Set([
  'para', 'este', 'esta', 'estos', 'estas', 'con', 'una', 'unos', 'unas', 'por',
  'que', 'del', 'las', 'los', 'sus', 'tus', 'como', 'desde', 'entre', 'sobre',
])

function normalizeText(value) {
  return value
    .toLocaleLowerCase('es')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

const filteredGames = computed(() => {
  const searchTerms = normalizeText(searchQuery.value).split(/\s+/).filter(Boolean)

  return games
    .filter((game) => {
      const searchableText = normalizeText([
        game.title,
        game.description,
        game.year,
        game.genre,
        game.era,
        game.url,
      ].join(' '))

      return searchTerms.every((term) => searchableText.includes(term))
    })
    .sort((first, second) => sortOrder.value === 'oldest'
      ? first.year - second.year
      : second.year - first.year)
})

const keywords = computed(() => {
  const words = new Set()

  filteredGames.value.forEach((game) => {
    const descriptionWords = normalizeText(game.description).match(/[a-z0-9]{3,}/g) ?? []
    descriptionWords.forEach((word) => {
      if (!ignoredKeywords.has(word)) words.add(word)
    })
  })

  return [...words].sort((first, second) => first.localeCompare(second, 'es'))
})

function openGame(game) {
  if (game.title === 'Pac-Man') {
    selectedGame.value = game
  }
}

function closeGame() {
  selectedGame.value = null
}

function handleImageError(title) {
  failedImages.value = new Set(failedImages.value).add(title)
}
</script>

<template>
  <main class="page-shell">
    <template v-if="selectedGame">
      <PacmanGame @back="closeGame" />
    </template>

    <template v-else>
      <header class="header">
        <p class="eyebrow">ARCADE · EDICIÓN PIXEL</p>
        <h1>Mi Ggaleodeon</h1>
        <p class="tagline">Una Ggaleria de juegos con toda la informacion que puedas necesitar</p>
      </header>

      <section class="game-area" aria-label="Catálogo de videojuegos">
        <div class="catalog-heading">
          <div>
            <p class="eyebrow">BIBLIOTECA ARCADE</p>
            <h2>Panel de juegos</h2>
          </div>
        </div>
        <div class="catalog-controls">
          <label class="search-control">
            <span>Buscar juegos</span>
            <input
              v-model="searchQuery"
              type="search"
              placeholder="Nombre, descripción, género, año..."
            >
          </label>
          <label class="sort-control">
            <span>Ordenar por año</span>
            <select v-model="sortOrder">
              <option value="newest">Más recientes</option>
              <option value="oldest">Más antiguos</option>
            </select>
          </label>
        </div>
        <p class="results-count" aria-live="polite">
          {{ filteredGames.length }} {{ filteredGames.length === 1 ? 'juego encontrado' : 'juegos encontrados' }}
        </p>
        <div v-if="filteredGames.length" class="game-grid">
          <article v-for="game in filteredGames" :key="game.title" class="game-tile">
            <div class="game-image-wrap">
              <img
                v-if="game.image && !failedImages.has(game.title)"
                class="game-image"
                :src="game.image"
                :alt="`Imagen de ${game.title}`"
                loading="lazy"
                @error="handleImageError(game.title)"
              >
              <div v-else class="game-image-fallback">
                <span>{{ game.title }}</span>
                <strong>{{ game.year }}</strong>
              </div>
              <span class="game-era">{{ game.era }}</span>
            </div>
            <div class="game-content">
              <div class="game-meta">
                <span>{{ game.genre }}</span>
                <time :datetime="String(game.year)">{{ game.year }}</time>
              </div>
              <h3>{{ game.title }}</h3>
              <p class="game-description">{{ game.description }}</p>
              <div class="game-actions">
                <a class="game-link" :href="game.url" target="_blank" rel="noopener noreferrer">
                  Ver información <span aria-hidden="true">↗</span>
                </a>
                <button
                  v-if="game.title === 'Pac-Man'"
                  class="game-play"
                  type="button"
                  @click="openGame(game)"
                >
                  Jugar
                </button>
              </div>
            </div>
          </article>
        </div>
        <p v-else class="empty-state">No hay juegos que coincidan con la búsqueda.</p>
      </section>
      <footer class="page-footer">
        <p class="eyebrow">KEYWORDS DE LOS JUEGOS MOSTRADOS</p>
        <ul v-if="keywords.length" class="keyword-list" aria-label="Keywords extraídas de las descripciones">
          <li v-for="keyword in keywords" :key="keyword">{{ keyword }}</li>
        </ul>
        <p v-else class="empty-keywords">Sin keywords para mostrar</p>
      </footer>
    </template>
  </main>
</template>

<style scoped>
:global(body) {
  margin: 0;
  min-height: 100vh;
  background:
    linear-gradient(180deg, rgba(15, 35, 30, 0.2), rgba(15, 35, 30, 0.76)),
    repeating-linear-gradient(0deg, transparent 0 38px, rgba(15, 35, 30, 0.18) 38px 40px),
    linear-gradient(180deg, #83b84b 0%, #4d873c 42%, #24543a 42%, #173a2c 100%);
  color: #fff4d2;
  font-family: "Courier New", monospace;
}

:global(html, body, #app) {
  min-height: 100vh;
}

.page-shell {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 40px 24px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  z-index: 1;
  animation: arrive 500ms ease-out both;
}

.eyebrow,
.tagline,
.page-footer {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
}

.eyebrow {
  color: #f7d875;
}

h1 {
  margin: 0;
  font-size: 48px;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: #fff2c3;
  text-shadow:
    4px 4px 0 #87532f,
    8px 8px 0 #263c32;
  font-weight: 900;
  line-height: 1.2;
}

.tagline {
  margin-top: 8px;
  color: #f2f2cf;
  letter-spacing: 1px;
}

.game-area {
  width: min(100%, 960px);
  margin: 30px auto 0;
  animation: arrive 550ms 80ms ease-out both;
}

.catalog-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 2px solid rgba(255, 244, 210, 0.55);
}

.catalog-heading h2 {
  margin: 7px 0 0;
  color: #fff2c3;
  font-size: 25px;
  text-shadow: 3px 3px #263c32;
}

.catalog-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  align-items: end;
  gap: 14px;
  margin-bottom: 12px;
}

.search-control,
.sort-control {
  display: grid;
  gap: 7px;
  color: #fff2c3;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.search-control input,
.sort-control select {
  width: 100%;
  min-height: 42px;
  box-sizing: border-box;
  padding: 0 12px;
  border: 2px solid rgba(255, 244, 210, 0.75);
  border-radius: 2px;
  background: rgba(25, 48, 37, 0.92);
  color: #fff4d2;
  font: 12px "Courier New", monospace;
}

.search-control input::placeholder { color: #c1d0ae; }
.search-control input:focus-visible,
.sort-control select:focus-visible,
.game-link:focus-visible {
  outline: 3px solid #f7d875;
  outline-offset: 3px;
}

.results-count {
  margin: 0 0 14px;
  color: #d3ddbb;
  font-size: 11px;
}

.game-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 270px), 1fr));
  gap: 16px;
}

.game-tile {
  min-width: 0;
  box-sizing: border-box;
  border: 2px solid rgba(255, 244, 210, 0.7);
  background: rgba(31, 54, 42, 0.94);
  box-shadow: 4px 4px 0 rgba(19, 39, 31, 0.7);
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
}

.game-tile:hover,
.game-tile:focus-within {
  transform: translateY(-5px) scale(1.015);
  border-color: #f7d875;
  box-shadow: 7px 10px 0 rgba(19, 39, 31, 0.7);
}

.game-image-wrap {
  position: relative;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #203b30;
}

.game-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 220ms ease;
}

.game-tile:hover .game-image,
.game-tile:focus-within .game-image {
  transform: scale(1.06);
}

.game-image-fallback {
  display: grid;
  width: 100%;
  height: 100%;
  align-content: center;
  justify-items: center;
  gap: 8px;
  background: repeating-linear-gradient(135deg, #28543c 0 16px, #326b47 16px 32px);
  color: #fff2c3;
  text-align: center;
  text-shadow: 2px 2px #203b30;
}

.game-image-fallback span {
  max-width: 85%;
  font-size: 18px;
  font-weight: 900;
}

.game-image-fallback strong { color: #f7d875; font-size: 13px; }

.game-era {
  position: absolute;
  right: 9px;
  bottom: 9px;
  padding: 5px 7px;
  background: rgba(25, 48, 37, 0.92);
  color: #f7d875;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
}

.game-content { padding: 13px 14px 15px; }

.game-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #f7d875;
  font-size: 10px;
  text-transform: uppercase;
}

.game-tile h3 {
  margin: 9px 0 7px;
  color: #fff2c3;
  font-size: 16px;
  line-height: 1.35;
}

.game-description {
  min-height: 54px;
  margin: 0;
  color: #d3ddbb;
  font-size: 12px;
  line-height: 1.55;
}

.game-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 13px;
}

.game-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #f7d875;
  font-size: 11px;
  font-weight: 700;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
}

.game-play {
  border: 1px solid rgba(247, 216, 117, 0.65);
  background: #2d5a4f;
  color: #fff2c3;
  padding: 7px 10px;
  font: 700 10px "Courier New", monospace;
  letter-spacing: 1px;
  text-transform: uppercase;
  cursor: pointer;
}

.game-play:hover {
  border-color: #fff2c3;
  background: #3d6c60;
}

.game-link:hover { color: #fff2c3; }

.empty-state,
.empty-keywords {
  margin: 18px 0;
  color: #d3ddbb;
  font-size: 12px;
}

.page-footer {
  width: min(100%, 960px);
  box-sizing: border-box;
  margin: 34px auto 0;
  padding: 20px 0 4px;
  border-top: 2px solid rgba(255, 244, 210, 0.45);
  color: #f7e5af;
  text-shadow: 2px 2px #243d31;
}

.page-footer .eyebrow { text-align: center; }

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 7px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.keyword-list li {
  padding: 5px 8px;
  border: 1px solid rgba(247, 216, 117, 0.65);
  color: #fff2c3;
  font-size: 10px;
}

.empty-keywords { text-align: center; }

@keyframes arrive {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 520px) {
  .page-shell { padding: 24px 16px 16px; }
  h1 { font-size: 32px; }
  .game-area { margin-top: 20px; }
  .catalog-heading { align-items: start; }
  .catalog-heading h2 { font-size: 21px; }
  .catalog-controls { grid-template-columns: 1fr; }
  .game-description { min-height: 0; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
</style>
