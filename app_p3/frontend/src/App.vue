<script setup>
import axios from 'axios'
import { computed, onMounted, reactive, ref } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api'
const games = ref([])
const loading = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const adminToken = ref('')
const editingId = ref(null)
const form = reactive({
  title: '',
  description: '',
  year: '',
  genre: '',
  era: '',
  image: '',
  url: '',
})

const sortedGames = computed(() => [...games.value].sort((first, second) => first.title.localeCompare(second.title)))

function getError(error) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.error ?? error.message
  }
  return error instanceof Error ? error.message : 'Se produjo un error inesperado.'
}

async function loadGames() {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await axios.get(`${API_BASE_URL}/games`)
    if (!Array.isArray(data.games)) throw new Error('La respuesta de la API no tiene el formato esperado.')
    games.value = data.games
  } catch (error) {
    errorMessage.value = getError(error)
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, { title: '', description: '', year: '', genre: '', era: '', image: '', url: '' })
  editingId.value = null
}

function startEditing(game) {
  Object.assign(form, {
    title: game.title,
    description: game.description,
    year: game.year,
    genre: game.genre,
    era: game.era,
    image: game.image,
    url: game.url,
  })
  editingId.value = game.id
  statusMessage.value = ''
  errorMessage.value = ''
  document.querySelector('#game-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

async function saveGame() {
  errorMessage.value = ''
  statusMessage.value = ''
  if (!adminToken.value.trim()) {
    errorMessage.value = 'Introduce el token de administrador para guardar juegos.'
    return
  }

  try {
    const payload = { ...form, year: Number(form.year) }
    const config = { headers: { Authorization: `Bearer ${adminToken.value}` } }
    const wasEditing = editingId.value !== null
    if (wasEditing) {
      await axios.put(`${API_BASE_URL}/games/${editingId.value}`, payload, config)
    } else {
      await axios.post(`${API_BASE_URL}/games`, payload, config)
    }
    resetForm()
    await loadGames()
    statusMessage.value = wasEditing ? 'Juego actualizado.' : 'Juego añadido.'
  } catch (error) {
    errorMessage.value = getError(error)
  }
}

async function deleteGame(game) {
  errorMessage.value = ''
  statusMessage.value = ''
  if (!adminToken.value.trim()) {
    errorMessage.value = 'Introduce el token de administrador para eliminar juegos.'
    return
  }
  if (!window.confirm(`¿Eliminar "${game.title}"?`)) return

  try {
    await axios.delete(`${API_BASE_URL}/games/${game.id}`, {
      headers: { Authorization: `Bearer ${adminToken.value}` },
    })
    if (editingId.value === game.id) resetForm()
    await loadGames()
    statusMessage.value = 'Juego eliminado.'
  } catch (error) {
    errorMessage.value = getError(error)
  }
}

onMounted(loadGames)
</script>

<template>
  <main class="page-shell">
    <header class="header">
      <p class="eyebrow">EJERCICIO 2 · FLASK + POSTGRESQL</p>
      <h1>Catálogo de juegos</h1>
      <p class="tagline">Consulta pública y administración protegida por token.</p>
    </header>

    <section class="panel" aria-labelledby="catalog-title">
      <div class="section-heading">
        <h2 id="catalog-title">Juegos</h2>
        <button class="button" type="button" :disabled="loading" @click="loadGames">
          {{ loading ? 'Cargando...' : 'Actualizar' }}
        </button>
      </div>
      <p v-if="errorMessage" class="message error" role="alert">{{ errorMessage }}</p>
      <p v-else-if="loading && !games.length" class="message" role="status">Cargando juegos...</p>
      <p v-else-if="!games.length" class="message">No hay juegos. Comprueba que el backend está activo.</p>
      <div v-else class="game-grid">
        <article v-for="game in sortedGames" :key="game.id" class="game-card">
          <img v-if="game.image" :src="game.image.startsWith('/') ? '.' + game.image : game.image" :alt="`Imagen de ${game.title}`">          <div class="game-content">
            <p class="eyebrow">{{ game.genre }} · {{ game.year }}</p>
            <h3>{{ game.title }}</h3>
            <p>{{ game.description }}</p>
            <a :href="game.url" target="_blank" rel="noopener noreferrer">Más información ↗</a>
            <div class="card-actions">
              <button class="button" type="button" @click="startEditing(game)">Editar</button>
              <button class="button danger" type="button" @click="deleteGame(game)">Eliminar</button>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section id="game-form" class="panel" aria-labelledby="form-title">
      <p class="eyebrow">ESCRITURA PROTEGIDA · BEARER TOKEN</p>
      <h2 id="form-title">{{ editingId === null ? 'Añadir juego' : 'Editar juego' }}</h2>
      <label class="token-field">
        <span>Token de administrador</span>
        <input v-model="adminToken" type="password" autocomplete="off">
      </label>
      <form class="game-form" @submit.prevent="saveGame">
        <label><span>Título</span><input v-model.trim="form.title" maxlength="160" required></label>
        <label><span>Año</span><input v-model="form.year" type="number" min="1" max="9999" required></label>
        <label><span>Género</span><input v-model.trim="form.genre" maxlength="100" required></label>
        <label><span>Época</span><input v-model.trim="form.era" maxlength="40" required></label>
        <label class="wide"><span>Descripción</span><textarea v-model.trim="form.description" required></textarea></label>
        <label class="wide"><span>Imagen (URL o ruta)</span><input v-model.trim="form.image" maxlength="2048" required></label>
        <label class="wide"><span>Enlace informativo</span><input v-model.trim="form.url" type="url" maxlength="2048" required></label>
        <div class="form-actions wide">
          <button class="button" type="submit">{{ editingId === null ? 'Añadir juego' : 'Guardar cambios' }}</button>
          <button v-if="editingId !== null" class="button" type="button" @click="resetForm">Cancelar</button>
        </div>
      </form>
      <p v-if="errorMessage" class="message error" role="alert">{{ errorMessage }}</p>
      <p v-if="statusMessage" class="message success" role="status">{{ statusMessage }}</p>
    </section>
  </main>
</template>

<style>
* { box-sizing: border-box; }
body {
  min-width: 320px;
  min-height: 100vh;
  margin: 0;
  background: linear-gradient(180deg, #4d873c 0%, #24543a 42%, #173a2c 100%);
  color: #fff4d2;
  font-family: "Courier New", monospace;
}
.page-shell { width: min(100% - 32px, 1000px); margin: 0 auto; padding: 32px 0; }
.header { margin-bottom: 24px; text-align: center; }
.eyebrow { margin: 0; color: #f7d875; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }
h1 { margin: 8px 0; color: #fff2c3; font-size: clamp(28px, 5vw, 42px); text-shadow: 3px 3px #263c32; }
.tagline, .message { color: #d3ddbb; font-size: 13px; }
.panel { margin: 18px 0; padding: 20px; border: 2px solid rgba(255, 244, 210, .55); background: rgba(25, 48, 37, .85); }
.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
h2 { margin: 0 0 14px; color: #fff2c3; font-size: 22px; }
.section-heading h2 { margin: 0; }
.game-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap: 14px; margin-top: 18px; }
.game-card { overflow: hidden; border: 1px solid rgba(255, 244, 210, .55); background: #1f362a; }
.game-card img { display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; background: #203b30; }
.game-content { padding: 14px; }
.game-content h3 { margin: 7px 0; color: #fff2c3; }
.game-content > p:not(.eyebrow) { min-height: 40px; color: #d3ddbb; font-size: 13px; line-height: 1.5; }
a { color: #f7d875; font-size: 12px; }
.card-actions, .form-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.button { border: 1px solid #f7d875; background: #2d5a4f; color: #fff2c3; padding: 9px 12px; font: 700 11px "Courier New", monospace; cursor: pointer; }
.button:hover:not(:disabled) { background: #3d6c60; }
.button:disabled { opacity: .6; cursor: wait; }
.button:focus-visible, input:focus-visible, textarea:focus-visible { outline: 3px solid #f7d875; outline-offset: 2px; }
.danger { border-color: #e99a78; }
.token-field, .game-form label { display: grid; gap: 6px; color: #fff2c3; font-size: 11px; }
.token-field { max-width: 480px; }
input, textarea { width: 100%; min-height: 40px; border: 1px solid rgba(255, 244, 210, .7); background: #193025; color: #fff4d2; padding: 8px 10px; font: 13px "Courier New", monospace; }
textarea { min-height: 80px; resize: vertical; }
.game-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.wide { grid-column: 1 / -1; }
.error { color: #ffd1bd; }
.success { color: #c9edaa; }
@media (max-width: 540px) { .panel { padding: 14px; } .game-form { grid-template-columns: 1fr; } .wide { grid-column: auto; } }
</style>
