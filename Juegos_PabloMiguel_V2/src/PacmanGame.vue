<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const emit = defineEmits(['back'])

const mazeWidth = 31
const mazeHeight = 21
const horizontalWalls = [
  { row: 4, start: 2, end: 12, gaps: [7] },
  { row: 4, start: 18, end: 28, gaps: [23] },
  { row: 8, start: 2, end: 12, gaps: [4, 10] },
  { row: 8, start: 18, end: 28, gaps: [21, 27] },
  { row: 12, start: 2, end: 12, gaps: [8] },
  { row: 12, start: 18, end: 28, gaps: [23] },
  { row: 16, start: 2, end: 12, gaps: [5, 10] },
  { row: 16, start: 18, end: 28, gaps: [20, 26] },
]
const verticalWalls = [
  { column: 6, start: 2, end: 18, gaps: [5, 14] },
  { column: 12, start: 2, end: 18, gaps: [10, 17] },
  { column: 18, start: 2, end: 18, gaps: [6, 13] },
  { column: 24, start: 2, end: 18, gaps: [9, 16] },
]

function createMaze() {
  const grid = Array.from({ length: mazeHeight }, (_, y) => Array.from({ length: mazeWidth }, (_, x) => (
    x === 0 || y === 0 || x === mazeWidth - 1 || y === mazeHeight - 1 ? '#' : '.'
  )))

  horizontalWalls.forEach(({ row, start, end, gaps }) => {
    for (let x = start; x <= end; x += 1) {
      if (!gaps.includes(x)) grid[row][x] = '#'
    }
  })
  verticalWalls.forEach(({ column, start, end, gaps }) => {
    for (let y = start; y <= end; y += 1) {
      if (!gaps.includes(y)) grid[y][column] = '#'
    }
  })
  ;[[3, 3], [27, 3], [3, 17], [27, 17]].forEach(([x, y]) => {
    grid[y][x] = 'o'
  })

  return grid.map((row) => row.join(''))
}

const initialMaze = createMaze()
const startPlayer = { x: 1, y: 1 }
const startGhosts = [
  { x: 27, y: 1, color: 'coral' },
  { x: 1, y: 19, color: 'pink' },
  { x: 27, y: 19, color: 'cyan' },
  { x: 15, y: 10, color: 'orange' },
]
const directions = {
  ArrowUp: { x: 0, y: -1 },
  w: { x: 0, y: -1 },
  ArrowDown: { x: 0, y: 1 },
  s: { x: 0, y: 1 },
  ArrowLeft: { x: -1, y: 0 },
  a: { x: -1, y: 0 },
  ArrowRight: { x: 1, y: 0 },
  d: { x: 1, y: 0 },
}
const ghostDirections = [
  { x: 0, y: -1 },
  { x: 0, y: 1 },
  { x: -1, y: 0 },
  { x: 1, y: 0 },
]

const maze = ref([])
const player = ref({ ...startPlayer })
const playerDirection = ref(null)
const queuedDirection = ref(null)
const ghosts = ref([])
const cherry = ref(null)
const score = ref(0)
const lives = ref(3)
const gameState = ref('playing')
const hasStarted = ref(false)
const frightened = ref(false)
const imageSources = ref({})
const message = computed(() => gameState.value === 'won'
  ? '¡Laberinto despejado!'
  : gameState.value === 'lost' ? 'Fin de la partida'
    : frightened.value ? '¡Fantasmas asustados! Cómelos para ganar 100 puntos'
    : hasStarted.value ? 'Come todos los puntos' : 'Elige una dirección con flechas o WASD')
let ghostTimer
let cherryTimer
let cherryExpiryTimer
let frightenedTimer

function resetGame() {
  window.clearTimeout(cherryExpiryTimer)
  window.clearTimeout(frightenedTimer)
  maze.value = initialMaze.map((row) => row.split(''))
  player.value = { ...startPlayer }
  playerDirection.value = null
  queuedDirection.value = null
  ghosts.value = startGhosts.map((ghost) => ({ ...ghost }))
  cherry.value = null
  score.value = 0
  lives.value = 3
  gameState.value = 'playing'
  hasStarted.value = false
  frightened.value = false
}

function spawnCherry() {
  if (gameState.value !== 'playing' || cherry.value) return

  const openCells = []
  maze.value.forEach((row, y) => row.forEach((tile, x) => {
    const isWall = tile === '#'
    const occupied = (player.value.x === x && player.value.y === y)
      || ghosts.value.some((ghost) => ghost.x === x && ghost.y === y)

    if (!isWall && !occupied) {
      openCells.push({ x, y })
    }
  }))

  if (!openCells.length) return

  const nextCherry = openCells[Math.floor(Math.random() * openCells.length)]
  cherry.value = nextCherry
  window.clearTimeout(cherryExpiryTimer)
  cherryExpiryTimer = window.setTimeout(() => {
    cherry.value = null
  }, 7000)
}

function activateFrightenedMode() {
  frightened.value = true
  window.clearTimeout(frightenedTimer)
  frightenedTimer = window.setTimeout(() => {
    frightened.value = false
  }, 6000)
}

function isWall(x, y) {
  return maze.value[y]?.[x] === '#' || maze.value[y]?.[x] === undefined
}

function requestDirection(direction) {
  if (gameState.value !== 'playing') return
  queuedDirection.value = direction
  movePlayer()
}

function movePlayer() {
  if (gameState.value !== 'playing') return

  const nextDirection = queuedDirection.value ?? playerDirection.value
  if (!nextDirection) return

  const nextX = player.value.x + nextDirection.x
  const nextY = player.value.y + nextDirection.y

  if (isWall(nextX, nextY)) {
    queuedDirection.value = null
    playerDirection.value = null
    return
  }

  playerDirection.value = nextDirection
  queuedDirection.value = null
  hasStarted.value = true
  player.value = { x: nextX, y: nextY }

  if (cherry.value?.x === nextX && cherry.value?.y === nextY) {
    score.value += 100
    cherry.value = null
    window.clearTimeout(cherryExpiryTimer)
    activateFrightenedMode()
  }

  const tile = maze.value[nextY][nextX]
  if (tile === '.' || tile === 'o') {
    score.value += tile === 'o' ? 50 : 10
    maze.value[nextY][nextX] = ' '
    if (!maze.value.some((row) => row.includes('.') || row.includes('o'))) {
      gameState.value = 'won'
    }
  }
  checkCollision()
}

function checkCollision() {
  const caughtGhosts = ghosts.value.filter((ghost) => ghost.x === player.value.x && ghost.y === player.value.y)
  if (!caughtGhosts.length) return
  if (frightened.value) {
    score.value += caughtGhosts.length * 100
    ghosts.value = ghosts.value.map((ghost) => {
      const spawn = startGhosts.find((item) => item.color === ghost.color)
      return caughtGhosts.includes(ghost) ? { ...ghost, x: spawn.x, y: spawn.y } : ghost
    })
    return
  }

  lives.value -= 1
  if (lives.value <= 0) {
    gameState.value = 'lost'
    return
  }
  player.value = { ...startPlayer }
  ghosts.value = startGhosts.map((ghost) => ({ ...ghost }))
}

function moveGhosts() {
  if (gameState.value !== 'playing' || !hasStarted.value) return
  ghosts.value = ghosts.value.map((ghost) => {
    const moves = ghostDirections
      .filter((direction) => !isWall(ghost.x + direction.x, ghost.y + direction.y))
    if (!moves.length) return ghost

    const distanceFromPlayer = (move) => Math.abs(ghost.x + move.x - player.value.x)
      + Math.abs(ghost.y + move.y - player.value.y)
    const distances = moves.map(distanceFromPlayer)
    const targetDistance = frightened.value ? Math.max(...distances) : Math.min(...distances)
    const preferredMoves = moves.filter((move) => {
      return distanceFromPlayer(move) === targetDistance
    })
    const move = preferredMoves[Math.floor(Math.random() * preferredMoves.length)]
    return { ...ghost, x: ghost.x + move.x, y: ghost.y + move.y }
  })
  checkCollision()
}

function handleKeydown(event) {
  const direction = directions[event.key] ?? directions[event.key.toLowerCase()]
  if (!direction) return
  event.preventDefault()
  requestDirection(direction)
}

function chooseImage(event, character) {
  const file = event.target.files?.[0]
  if (!file || !file.type.startsWith('image/')) return
  const reader = new FileReader()
  reader.onload = () => {
    imageSources.value = { ...imageSources.value, [character]: reader.result }
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

function resetImage(character) {
  const nextImages = { ...imageSources.value }
  delete nextImages[character]
  imageSources.value = nextImages
}

const boardCells = computed(() => maze.value.flatMap((row, y) => row.map((tile, x) => ({
  x,
  y,
  tile,
  player: player.value.x === x && player.value.y === y,
  cherry: cherry.value?.x === x && cherry.value?.y === y,
  ghost: ghosts.value.find((item) => item.x === x && item.y === y),
}))))

onMounted(() => {
  resetGame()
  window.addEventListener('keydown', handleKeydown)
  ghostTimer = window.setInterval(moveGhosts, 430)
  cherryTimer = window.setInterval(spawnCherry, 10000)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.clearInterval(ghostTimer)
  window.clearInterval(cherryTimer)
  window.clearTimeout(cherryExpiryTimer)
  window.clearTimeout(frightenedTimer)
})
</script>

<template>
  <main class="pacman-screen">
    <div class="game-topline">
      <button class="back-button" type="button" @click="emit('back')">← Volver al catálogo</button>
      <span class="game-label">ARCADE · 1980</span>
    </div>

    <header class="game-heading">
      <p class="game-kicker">INSERT COIN · READY PLAYER ONE</p>
      <h2>Pac<span>-</span>Man</h2>
      <p class="game-message" aria-live="polite">{{ message }}</p>
    </header>

    <section class="play-layout" aria-label="Partida de Pac-Man">
      <div class="board-column">
        <div class="scorebar" aria-label="Marcador">
          <div><span class="score-label">PUNTOS</span><strong>{{ String(score).padStart(4, '0') }}</strong></div>
          <div><span class="score-label">VIDAS</span><strong class="life-icons">{{ '● '.repeat(lives) || '—' }}</strong></div>
          <button class="restart-button" type="button" @click="resetGame">Reiniciar</button>
        </div>

        <div class="maze" role="grid" aria-label="Laberinto. Usa las flechas o WASD para moverte">
          <div
            v-for="cell in boardCells"
            :key="`${cell.x}-${cell.y}`"
            class="maze-cell"
            :class="{ wall: cell.tile === '#', corridor: cell.tile !== '#' }"
            role="gridcell"
          >
            <span v-if="cell.tile === '.'" class="pellet" aria-hidden="true"></span>
            <span v-else-if="cell.tile === 'o'" class="power-pellet" aria-hidden="true"></span>
            <span v-if="cell.cherry" class="cherry" role="img" aria-label="Cereza: activa la huida de los fantasmas"></span>
            <span v-if="cell.player" class="character pacman-character" aria-label="Pac-Man">
              <img v-if="imageSources.pacman" :src="imageSources.pacman" alt="">
              <span v-else class="pacman-default"></span>
            </span>
            <span v-else-if="cell.ghost" class="character ghost-character" :class="[cell.ghost.color, { frightened }]" :aria-label="`Fantasma ${cell.ghost.color}`">
              <img v-if="imageSources[cell.ghost.color]" :src="imageSources[cell.ghost.color]" :class="{ 'frightened-image': frightened }" alt="">
              <span v-else class="ghost-default"><i></i><i></i></span>
            </span>
          </div>
        </div>

        <div class="touch-controls" aria-label="Controles táctiles">
          <button type="button" aria-label="Arriba" @click="requestDirection(directions.ArrowUp)">↑</button>
          <div>
            <button type="button" aria-label="Izquierda" @click="requestDirection(directions.ArrowLeft)">←</button>
            <button type="button" aria-label="Abajo" @click="requestDirection(directions.ArrowDown)">↓</button>
            <button type="button" aria-label="Derecha" @click="requestDirection(directions.ArrowRight)">→</button>
          </div>
        </div>
      </div>

      <aside class="character-panel">
        <div class="panel-title"><span>01</span><h3>Personaliza</h3></div>
        <p class="panel-note">Elige una imagen de tu dispositivo para cada personaje.</p>
        <label class="character-picker">
          <span class="picker-preview pacman-swatch">
            <img v-if="imageSources.pacman" :src="imageSources.pacman" alt="">
            <span v-else class="pacman-default"></span>
          </span>
          <span class="picker-name">Pac-Man</span>
          <span class="picker-action">Elegir imagen</span>
          <input type="file" accept="image/*" @change="chooseImage($event, 'pacman')">
        </label>
        <label v-for="ghost in startGhosts" :key="ghost.color" class="character-picker">
          <span class="picker-preview" :class="ghost.color">
            <img v-if="imageSources[ghost.color]" :src="imageSources[ghost.color]" alt="">
            <span v-else class="ghost-default"><i></i><i></i></span>
          </span>
          <span class="picker-name">Fantasma {{ ghost.color }}</span>
          <span class="picker-action">Elegir imagen</span>
          <input type="file" accept="image/*" @change="chooseImage($event, ghost.color)">
        </label>
        <button v-if="Object.keys(imageSources).length" class="clear-images" type="button" @click="imageSources = {}">Restablecer imágenes</button>
      </aside>
    </section>
  </main>
</template>

<style scoped>
.pacman-screen {
  width: min(100%, 1200px);
  margin: 30px auto 0;
  padding: 22px;
  box-sizing: border-box;
  border: 2px solid rgba(255, 244, 210, 0.72);
  background: #172d2c;
  color: #f8edc6;
  box-shadow: 7px 7px 0 rgba(19, 39, 31, 0.64);
  animation: enter 360ms ease-out both;
}

.game-topline,
.scorebar,
.scorebar > div,
.panel-title,
.character-picker {
  display: flex;
  align-items: center;
}

.game-topline { justify-content: space-between; gap: 12px; }
.back-button,
.restart-button,
.touch-controls button {
  border: 1px solid rgba(248, 237, 198, 0.45);
  background: #203c37;
  color: #f8edc6;
  font: 700 11px "Courier New", monospace;
  cursor: pointer;
}
.back-button { padding: 8px 10px; }
.back-button:hover,
.restart-button:hover,
.touch-controls button:hover { border-color: #f5d65e; color: #f5d65e; }
.game-label,.game-kicker,.score-label { color: #f5d65e; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; }
.game-heading { padding: 24px 0 18px; text-align: center; }
.game-kicker { margin: 0 0 7px; }
.game-heading h2 { margin: 0; color: #ffdc52; font: 900 44px/1 "Courier New", monospace; text-shadow: 4px 4px #7c542e; }
.game-heading h2 span { color: #f8edc6; }
.game-message { min-height: 15px; margin: 12px 0 0; color: #bed3b4; font-size: 12px; }
.play-layout { display: grid; grid-template-columns: minmax(0, 1fr) 260px; gap: 22px; align-items: start; }
.board-column { min-width: 0; }
.scorebar { justify-content: space-between; gap: 10px; margin-bottom: 10px; padding: 9px 11px; border: 1px solid #405a4d; background: #203c37; }
.scorebar > div { align-items: baseline; gap: 8px; }
.scorebar strong { color: #fff4d2; font-size: 15px; }
.life-icons { color: #ffdc52 !important; letter-spacing: 1px; }
.restart-button { padding: 6px 9px; }
.maze { display: grid; grid-template-columns: repeat(31, minmax(0, 1fr)); width: 100%; max-width: 870px; margin: 0 auto; border: 4px solid #3986a1; background: #071b2c; }
.maze-cell { position: relative; display: grid; place-items: center; aspect-ratio: 1; min-width: 0; overflow: hidden; }
.maze-cell.wall { background: #123f58; box-shadow: inset 0 0 0 1px #246482; }
.pellet { width: 15%; aspect-ratio: 1; border-radius: 50%; background: #f8edc6; }
.power-pellet { width: 42%; aspect-ratio: 1; border-radius: 50%; background: #f8edc6; box-shadow: 0 0 9px #f8edc6; }
.cherry {
  position: absolute;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 58%;
  height: 58%;
  font-size: clamp(10px, 1.05vw, 18px);
  line-height: 1;
  pointer-events: none;
}
.cherry::before {
  content: "🍒";
  display: block;
  transform-origin: center;
  filter: drop-shadow(0 0 4px rgba(255, 76, 91, 0.8));
  animation: cherry-bob 650ms ease-in-out infinite alternate;
}
.character { position: absolute; z-index: 1; display: grid; width: 82%; height: 82%; place-items: center; }
.character img,.picker-preview img { display: block; width: 100%; height: 100%; object-fit: contain; }
.frightened-image { filter: hue-rotate(175deg) saturate(1.8) brightness(1.12); }
.pacman-default { display: block; width: 100%; height: 100%; border-radius: 50%; background: conic-gradient(from 45deg, transparent 0deg 90deg, #ffdc52 90deg 360deg); }
.ghost-character { border-radius: 50% 50% 0 0; }
.ghost-default { position: relative; display: flex; justify-content: center; gap: 16%; width: 100%; height: 82%; border-radius: 50% 50% 8% 8%; background: currentColor; }
.ghost-default::after { position: absolute; right: 0; bottom: -13%; left: 0; height: 25%; background: currentColor; content: ""; clip-path: polygon(0 0, 20% 100%, 40% 0, 60% 100%, 80% 0, 100% 100%, 100% 0); }
.ghost-default i { z-index: 1; width: 16%; height: 24%; margin-top: 34%; border-radius: 50%; background: #fff; }
.coral { color: #ff635c; }
.pink { color: #ff9bbb; }
.cyan { color: #53d7d4; }
.orange { color: #ffa743; }
.ghost-character.frightened { color: #488bff; animation: frightened-flash 260ms ease-in-out infinite alternate; }
.touch-controls { display: none; }
.character-panel { padding: 14px; border: 1px solid #405a4d; background: #203c37; }
.panel-title { gap: 10px; padding-bottom: 11px; border-bottom: 1px solid #526557; }
.panel-title > span { color: #f5d65e; font-size: 10px; }
.panel-title h3 { margin: 0; font-size: 14px; }
.panel-note { margin: 11px 0 8px; color: #bed3b4; font-size: 11px; line-height: 1.5; }
.character-picker { position: relative; min-height: 48px; gap: 9px; border-bottom: 1px solid rgba(190, 211, 180, 0.15); cursor: pointer; }
.character-picker:hover .picker-action { color: #fff4d2; text-decoration: underline; }
.character-picker input { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; clip-path: inset(50%); }
.character-picker:focus-within { outline: 2px solid #f5d65e; outline-offset: 2px; }
.picker-preview { display: grid; width: 28px; height: 28px; flex: 0 0 28px; place-items: center; }
.picker-preview .pacman-default { width: 24px; height: 24px; }
.picker-preview .ghost-default { width: 23px; height: 23px; }
.picker-name { flex: 1; color: #f8edc6; font-size: 11px; text-transform: capitalize; }
.picker-action { color: #f5d65e; font-size: 9px; white-space: nowrap; }
.clear-images { margin-top: 12px; padding: 0; border: 0; background: none; color: #bed3b4; font: 10px "Courier New", monospace; text-decoration: underline; cursor: pointer; }

@keyframes enter { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes cherry-bob { to { transform: translateY(-2px) scale(1.08); } }
@keyframes frightened-flash { to { filter: brightness(1.5); } }
@media (max-width: 760px) {
  .play-layout { grid-template-columns: 1fr; }
  .character-panel { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 12px; }
  .panel-title,.panel-note,.clear-images { grid-column: 1 / -1; }
  .character-picker { min-width: 0; }
}
@media (max-width: 520px) {
  .pacman-screen { margin-top: 20px; padding: 13px 10px; }
  .game-topline { align-items: flex-start; }
  .game-heading { padding: 19px 0 12px; }
  .game-heading h2 { font-size: 36px; }
  .game-label { padding-top: 8px; font-size: 9px; }
  .scorebar { flex-wrap: wrap; }
  .scorebar > div { gap: 5px; }
  .scorebar strong { font-size: 12px; }
  .maze { border-width: 3px; }
  .cherry { font-size: 14px; }
  .touch-controls { display: grid; justify-items: center; gap: 5px; margin-top: 12px; }
  .touch-controls > div { display: flex; gap: 5px; }
  .touch-controls button { width: 42px; height: 38px; font-size: 16px; touch-action: manipulation; }
  .character-panel { padding: 11px; }
  .picker-action { font-size: 8px; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }
</style>
