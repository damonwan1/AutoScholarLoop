<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const lang = ref('en')

const zh = {
  app: 'AI SCHOLAR LOOP',
  title: 'AI Scholar Loop',
  lead: '\u6559\u6388\u51b3\u7b56\u3001\u535a\u58eb\u6267\u884c\u3001\u5199\u4f5c\u4e0e\u8d28\u91cf\u5ba1\u8ba1\u7684\u5168\u6d41\u7a0b\u81ea\u52a8\u5316\u79d1\u7814\u5faa\u73af\u3002',
  language: 'English',
  configured: '\u6a21\u578b\u5df2\u914d\u7f6e',
  configure: '\u914d\u7f6e\u6a21\u578b API',
  setup: '\u5927\u6a21\u578b API \u914d\u7f6e',
  providerPreset: '\u63d0\u4f9b\u65b9\u9884\u8bbe',
  provider: '\u63d0\u4f9b\u65b9',
  model: '\u6a21\u578b',
  baseUrl: 'Base URL',
  apiKey: 'API Key',
  trustEnv: '\u4f7f\u7528\u7cfb\u7edf\u4ee3\u7406\u73af\u5883\u53d8\u91cf',
  save: '\u4fdd\u5b58\u914d\u7f6e',
  later: '\u7a0d\u540e\u518d\u8bf4',
  brief: '\u542f\u52a8\u4e00\u4e2a\u79d1\u7814\u95ed\u73af',
  seed: '\u7814\u7a76\u65b9\u5411 / \u521d\u59cb\u60f3\u6cd5',
  venue: '\u76ee\u6807\u4f1a\u8bae / \u671f\u520a',
  format: '\u8bba\u6587\u683c\u5f0f',
  loopMode: 'Loop \u6a21\u5f0f',
  ideas: '\u5019\u9009 idea \u6570',
  literature: '\u6587\u732e\u68c0\u7d22',
  backend: '\u5b9e\u9a8c\u540e\u7aef\uff08\u9ed8\u8ba4\u672c\u673a\u8fd0\u884c\uff09',
  decisionRounds: '\u6559\u6388\u51b3\u7b56\u8f6e\u6b21',
  executionRounds: '\u535a\u58eb\u6267\u884c\u8f6e\u6b21',
  writingRounds: '\u5199\u4f5c\u5ba1\u7a3f\u8f6e\u6b21',
  bigLoops: '\u5168\u5c40\u5927\u5faa\u73af\u6b21\u6570',
  compilePdf: '\u5c1d\u8bd5\u7f16\u8bd1 PDF\uff08\u9700\u8981\u672c\u5730 LaTeX\uff09',
  demoMode: 'Demo mode\uff08\u672a\u914d\u7f6e\u5927\u6a21\u578b\u65f6\u624d\u5141\u8bb8\u672c\u5730\u5feb\u901f\u6f14\u793a\uff09',
  upload: '\u4e0a\u4f20\u8fd1\u671f\u8bba\u6587 PDF / notes',
  uploadEmpty: '\u9009\u62e9 3-10 \u4efd\u53c2\u8003\u6750\u6599',
  start: '\u542f\u52a8 Auto Loop',
  starting: '\u542f\u52a8\u4e2d...',
  observability: '\u79d1\u7814\u7ec4\u8fdb\u5c55',
  currentAction: '\u5f53\u524d\u52a8\u4f5c',
  liveLog: '\u5c55\u5f00\u8fd0\u884c\u65e5\u5fd7',
  hideLog: '\u6536\u8d77\u8fd0\u884c\u65e5\u5fd7',
  downloads: '\u4e0b\u8f7d\u4ea7\u7269',
  noDownloads: '\u5b8c\u6210 LaTeX/PDF \u751f\u6210\u540e\u4f1a\u5728\u8fd9\u91cc\u663e\u793a\u3002',
  emptyStages: '\u4efb\u52a1\u542f\u52a8\u540e\uff0c\u8fd9\u91cc\u4f1a\u663e\u793a S00 \u5efa\u6863\u3001S01 \u51b3\u7b56\u3001S02 \u6267\u884c\u3001S03 \u5199\u4f5c\u3001S04 \u5ba1\u8ba1\u548c Release \u72b6\u6001\u3002',
  checkpoints: '\u9636\u6bb5\u6027\u7ed3\u679c',
  selectCheckpoint: '\u9009\u62e9\u4e00\u4e2a checkpoint \u67e5\u770b\u5185\u5bb9\u3002',
  githubTitle: 'GitHub \u5f00\u6e90\u4ed3\u5e93',
  githubText: '\u67e5\u770b\u4ee3\u7801\u3001\u6587\u6863\u548c\u540e\u7eed\u66f4\u65b0\u3002',
  githubButton: '\u6253\u5f00 GitHub',
  localWarning: '\u5f53\u524d\u662f Local deterministic provider\uff0c\u53ea\u9002\u5408 demo\uff0c\u4e0d\u4f1a\u751f\u6210\u771f\u5b9e\u79d1\u7814\u7ed3\u8bba\u3002',
  saved: '\u6a21\u578b\u914d\u7f6e\u5df2\u4fdd\u5b58\u3002',
  needSeed: '\u8bf7\u5148\u586b\u5199\u7814\u7a76\u65b9\u5411\u6216\u521d\u59cb\u60f3\u6cd5\u3002',
  launching: '\u6b63\u5728\u542f\u52a8 AUTO Research loop\u3002',
  failed: '\u542f\u52a8\u5931\u8d25',
  placeholders: {
    seed: '\u4f8b\u5982\uff1a\u7814\u7a76\u591a\u667a\u80fd\u4f53\u81ea\u52a8\u79d1\u7814\u7cfb\u7edf\u5982\u4f55\u964d\u4f4e\u8bba\u6587\u5199\u4f5c\u4e2d\u7684\u4f2a\u521b\u65b0\u548c\u4f2a\u5f15\u7528\u3002',
    venue: 'NeurIPS / ACL / IEEE TNNLS / \u4e2d\u6587\u6838\u5fc3\u7b49',
    apiSaved: '\u5df2\u4fdd\u5b58\uff0c\u7559\u7a7a\u4e0d\u4fee\u6539',
    apiNew: '\u771f\u5b9e\u8fd0\u884c\u9700\u8981\u586b\u5199',
  },
}

const en = {
  app: 'AI SCHOLAR LOOP',
  title: 'AI Scholar Loop',
  lead: 'An automated research loop for professor decision, PhD execution, writing, and quality audit.',
  language: '\u4e2d\u6587',
  configured: 'Model Configured',
  configure: 'Configure Model API',
  setup: 'Large Model API Setup',
  providerPreset: 'Provider Preset',
  provider: 'Provider',
  model: 'Model',
  baseUrl: 'Base URL',
  apiKey: 'API Key',
  trustEnv: 'Use system proxy environment variables',
  save: 'Save Configuration',
  later: 'Later',
  brief: 'Start A Research Loop',
  seed: 'Research Direction / Initial Idea',
  venue: 'Target Conference / Journal',
  format: 'Paper Format',
  loopMode: 'Loop Mode',
  ideas: 'Candidate Ideas',
  literature: 'Literature Backend',
  backend: 'Execution Backend (local by default)',
  decisionRounds: 'Professor Decision Rounds',
  executionRounds: 'PhD Execution Rounds',
  writingRounds: 'Writing Review Rounds',
  bigLoops: 'Global Big Loops',
  compilePdf: 'Attempt PDF Compilation (requires local LaTeX)',
  demoMode: 'Demo mode (allows local deterministic run without a model API)',
  upload: 'Upload Recent Papers / Notes',
  uploadEmpty: 'Select 3-10 reference files',
  start: 'Start Auto Loop',
  starting: 'Starting...',
  observability: 'Research Group Progress',
  currentAction: 'Current Action',
  liveLog: 'Expand Runtime Log',
  hideLog: 'Collapse Runtime Log',
  downloads: 'Downloads',
  noDownloads: 'LaTeX/PDF artifacts will appear here after they are generated.',
  emptyStages: 'After launch, this area shows S00 archive, S01 decision, S02 execution, S03 writing, S04 audit, and release status.',
  checkpoints: 'Stage Checkpoints',
  selectCheckpoint: 'Select a checkpoint to preview.',
  githubTitle: 'GitHub Repository',
  githubText: 'View source code, documentation, and future updates.',
  githubButton: 'Open GitHub',
  localWarning: 'Current provider is Local deterministic. It is only a demo mode and will not produce real scientific results.',
  saved: 'Model configuration saved.',
  needSeed: 'Please enter a research direction or initial idea first.',
  launching: 'Launching AUTO Research loop.',
  failed: 'Launch failed',
  placeholders: {
    seed: 'Example: I want to study how multi-agent research systems reduce false novelty and false citations in paper writing.',
    venue: 'NeurIPS / ACL / IEEE TNNLS / Chinese core journal, etc.',
    apiSaved: 'Saved. Leave empty to keep unchanged.',
    apiNew: 'Required for real model-backed runs',
  },
}

const tips = {
  provider: {
    en: 'local is a deterministic offline demo. openai-compatible calls a real model API.',
    zh: 'local \u662f\u79bb\u7ebf\u6f14\u793a\uff1bopenai-compatible \u4f1a\u8c03\u7528\u771f\u5b9e\u5927\u6a21\u578b API\u3002',
  },
  loopMode: {
    en: 'Preset depth. Custom round counts below override this preset.',
    zh: '\u9884\u8bbe\u5faa\u73af\u6df1\u5ea6\uff1b\u4e0b\u65b9\u81ea\u5b9a\u4e49\u8f6e\u6b21\u4f1a\u8986\u76d6\u8be5\u9884\u8bbe\u3002',
  },
  decisionRounds: {
    en: 'How many rounds the professor group uses to generate, attack, refine, and select ideas.',
    zh: '\u6559\u6388\u7ec4\u7528\u4e8e\u751f\u6210\u3001\u653b\u51fb\u3001\u4fee\u6b63\u548c\u9009\u62e9 idea \u7684\u8f6e\u6b21\u3002',
  },
  executionRounds: {
    en: 'How many executor-review rounds the PhD group uses for baseline, implementation, experiment, and failure feedback.',
    zh: '\u535a\u58eb\u7ec4\u7528\u4e8e baseline\u3001\u5b9e\u73b0\u3001\u5b9e\u9a8c\u548c\u5931\u8d25\u53cd\u9988\u7684\u8f6e\u6b21\u3002',
  },
  writingRounds: {
    en: 'How many writing-review rounds are used to convert evidence into a manuscript.',
    zh: '\u5199\u4f5c\u7ec4\u5c06\u8bc1\u636e\u8f6c\u6210\u8bba\u6587\u5e76\u4fee\u6539\u7684\u8f6e\u6b21\u3002',
  },
  compilePdf: {
    en: 'Always writes LaTeX. PDF is attempted only if a local LaTeX toolchain and required class files exist.',
    zh: '\u7cfb\u7edf\u603b\u662f\u751f\u6210 LaTeX\uff1b\u53ea\u6709\u672c\u5730\u5b89\u88c5 LaTeX \u548c\u6240\u9700 class \u6587\u4ef6\u65f6\u624d\u4f1a\u7f16\u8bd1 PDF\u3002',
  },
}

const formats = computed(() => [
  { key: 'ieee', label: 'IEEE', note: lang.value === 'en' ? 'two-column article draft' : 'IEEE \u53cc\u680f\u8bba\u6587\u8349\u7a3f' },
  { key: 'acm', label: 'ACM', note: lang.value === 'en' ? 'ACM-style article draft' : 'ACM \u98ce\u683c\u8bba\u6587\u8349\u7a3f' },
  { key: 'springer_lncs', label: 'Springer LNCS', note: lang.value === 'en' ? 'LNCS proceedings draft' : 'LNCS \u4f1a\u8bae\u8bba\u6587\u8349\u7a3f' },
  { key: 'chinese_thesis', label: lang.value === 'en' ? 'Chinese Thesis' : '\u4e2d\u6587\u5b66\u4f4d\u8bba\u6587', note: lang.value === 'en' ? 'chapter-based thesis draft' : '\u7ae0\u8282\u5f0f\u5b66\u4f4d\u8bba\u6587\u8349\u7a3f' },
])

const providerPresets = [
  {
    key: 'local',
    label: 'Local demo',
    provider: 'local',
    model: 'local-researcher',
    baseUrl: '',
    trustEnv: true,
  },
  {
    key: 'deepseek',
    label: 'DeepSeek',
    provider: 'openai-compatible',
    model: 'deepseek-chat',
    baseUrl: 'https://api.deepseek.com/v1',
    trustEnv: false,
  },
  {
    key: 'openai',
    label: 'OpenAI',
    provider: 'openai-compatible',
    model: 'gpt-4.1',
    baseUrl: 'https://api.openai.com/v1',
    trustEnv: true,
  },
  {
    key: 'custom',
    label: 'Custom OpenAI-compatible',
    provider: 'openai-compatible',
    model: '',
    baseUrl: '',
    trustEnv: true,
  },
]

const stageText = {
  S00_field_archive: { en: 'S00 Field Archive', zh: 'S00 \u9886\u57df\u5efa\u6863' },
  S01_professor_decision_loop: { en: 'S01 Professor Decision', zh: 'S01 \u6559\u6388\u51b3\u7b56' },
  S02_execution_review_loop: { en: 'S02 PhD Execution', zh: 'S02 \u535a\u58eb\u6267\u884c' },
  S03_writing_review_loop: { en: 'S03 Writing Review', zh: 'S03 \u5199\u4f5c\u5ba1\u7a3f' },
  S04_quality_gate: { en: 'S04 Quality Gate', zh: 'S04 \u8d28\u91cf\u95e8\u63a7' },
  release: { en: 'Release', zh: '\u53d1\u5e03\u5305' },
}

const statusText = {
  idle: { en: 'idle', zh: '\u7a7a\u95f2' },
  queued: { en: 'queued', zh: '\u6392\u961f\u4e2d' },
  running: { en: 'running', zh: '\u8fd0\u884c\u4e2d' },
  completed: { en: 'completed', zh: '\u5df2\u5b8c\u6210' },
  failed: { en: 'failed', zh: '\u5931\u8d25' },
  pending: { en: 'pending', zh: '\u7b49\u5f85\u4e2d' },
  active: { en: 'active', zh: '\u8fdb\u884c\u4e2d' },
  needs_revision: { en: 'needs revision', zh: '\u9700\u8981\u56de\u9000\u4fee\u6539' },
}

const config = reactive({
  preset: 'local',
  provider: 'local',
  model: 'local-researcher',
  base_url: '',
  api_key: '',
  has_api_key: false,
  http_trust_env: true,
})
const form = reactive({
  seed: '',
  target_venue: '',
  paper_format: 'ieee',
  loop_mode: 'standard',
  decision_rounds: 10,
  execution_rounds: 5,
  writing_rounds: 5,
  max_big_loops: 2,
  num_ideas: 3,
  literature: 'local',
  execution_backend: 'shell',
  compile_pdf: true,
  demo_mode: false,
})

const selectedFiles = ref([])
const runState = ref(null)
const activeArtifact = ref(null)
const artifactText = ref('')
const logOpen = ref(false)
const loading = ref(false)
const configOpen = ref(false)
const message = ref('')
let pollTimer = null

const t = computed(() => (lang.value === 'en' ? en : zh))
const configured = computed(() => config.provider !== 'openai-compatible' || config.has_api_key || config.api_key.length > 0)
const canRun = computed(() => configured.value && (config.provider !== 'local' || form.demo_mode))
const progressText = computed(() => `${runState.value?.progress || 0}%`)
const stageGroups = computed(() => runState.value?.stages || [])

onMounted(async () => {
  await loadConfig()
  configOpen.value = config.provider === 'openai-compatible' && !configured.value
})

function trStatus(status) {
  return statusText[status]?.[lang.value] || status
}

function trStage(stage) {
  return stageText[stage.key]?.[lang.value] || stage.label
}

function tip(key) {
  return tips[key]?.[lang.value] || ''
}

async function loadConfig() {
  try {
    const response = await fetch(`${API_BASE}/api/config`)
    const data = await response.json()
    Object.assign(config, {
      preset: inferPreset(data),
      provider: data.provider || 'local',
      model: data.model || 'local-researcher',
      base_url: data.base_url || '',
      api_key: '',
      has_api_key: Boolean(data.has_api_key),
      http_trust_env: data.http_trust_env !== false,
    })
  } catch {
    message.value = 'Cannot connect to backend API.'
  }
}

async function saveConfig() {
  const response = await fetch(`${API_BASE}/api/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!response.ok) {
    message.value = lang.value === 'en' ? 'Failed to save model configuration.' : '\u6a21\u578b\u914d\u7f6e\u4fdd\u5b58\u5931\u8d25\u3002'
    return
  }
  const data = await response.json()
  config.has_api_key = Boolean(data.has_api_key)
  config.api_key = ''
  configOpen.value = false
  message.value = t.value.saved
}

function onFiles(event) {
  selectedFiles.value = Array.from(event.target.files || [])
}

function inferPreset(data) {
  if ((data.provider || 'local') === 'local') return 'local'
  if (data.model === 'deepseek-chat' || data.base_url === 'https://api.deepseek.com/v1') return 'deepseek'
  if ((data.base_url || '').includes('api.openai.com')) return 'openai'
  return 'custom'
}

function applyProviderPreset() {
  const preset = providerPresets.find((item) => item.key === config.preset)
  if (!preset) return
  config.provider = preset.provider
  config.model = preset.model
  config.base_url = preset.baseUrl
  config.http_trust_env = preset.trustEnv
}

function applyPreset() {
  if (form.loop_mode === 'fast') {
    Object.assign(form, { decision_rounds: 3, execution_rounds: 2, writing_rounds: 3, max_big_loops: 1 })
  } else if (form.loop_mode === 'standard') {
    Object.assign(form, { decision_rounds: 10, execution_rounds: 5, writing_rounds: 5, max_big_loops: 2 })
  } else {
    Object.assign(form, { decision_rounds: 12, execution_rounds: 6, writing_rounds: 7, max_big_loops: 3 })
  }
}

async function startRun() {
  if (!form.seed.trim()) {
    message.value = t.value.needSeed
    return
  }
  if (!canRun.value) {
    message.value = config.provider === 'local'
      ? t.value.localWarning
      : 'Please configure a model API key before launching.'
    return
  }
  loading.value = true
  activeArtifact.value = null
  artifactText.value = ''
  message.value = t.value.launching
  const body = new FormData()
  for (const [key, value] of Object.entries(form)) body.append(key, value)
  body.append('provider', config.provider)
  body.append('model', config.model)
  body.append('base_url', config.base_url || '')
  body.append('api_key', config.api_key || '')
  body.append('http_trust_env', config.http_trust_env)
  selectedFiles.value.forEach((file) => body.append('files', file))
  try {
    const response = await fetch(`${API_BASE}/api/runs`, { method: 'POST', body })
    if (!response.ok) throw new Error(await response.text())
    const data = await response.json()
    await pollRun(data.job_id)
    pollTimer = window.setInterval(() => pollRun(data.job_id), 1600)
  } catch (error) {
    message.value = `${t.value.failed}: ${error.message}`
  } finally {
    loading.value = false
  }
}

async function pollRun(jobId) {
  const response = await fetch(`${API_BASE}/api/runs/${jobId}`)
  runState.value = await response.json()
  if (['completed', 'failed', 'needs_revision'].includes(runState.value.status) && pollTimer) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
}

async function openArtifact(item) {
  if (!runState.value) return
  activeArtifact.value = item
  const params = new URLSearchParams({ path: item.path })
  const response = await fetch(`${API_BASE}/api/runs/${runState.value.job_id}/artifact?${params}`)
  artifactText.value = await response.text()
}

function downloadUrl(item) {
  const params = new URLSearchParams({ path: item.path })
  return `${API_BASE}/api/runs/${runState.value.job_id}/download?${params}`
}
</script>

<template>
  <main class="shell">
    <section class="hero">
      <div>
        <p class="eyebrow">{{ t.app }}</p>
        <h1>{{ t.title }}</h1>
        <p class="lead">{{ t.lead }}</p>
      </div>
      <div class="top-actions">
        <button class="ghost compact" type="button" @click="lang = lang === 'en' ? 'zh' : 'en'">{{ t.language }}</button>
        <button class="config-button" type="button" @click="configOpen = true">
          {{ configured ? t.configured : t.configure }}
        </button>
      </div>
    </section>

    <section v-if="configOpen" class="panel config-panel">
      <div>
        <p class="eyebrow">FIRST RUN SETUP</p>
        <h2>{{ t.setup }}</h2>
      </div>
      <div class="grid two">
        <label>{{ t.providerPreset }}
          <select v-model="config.preset" @change="applyProviderPreset">
            <option v-for="preset in providerPresets" :key="preset.key" :value="preset.key">{{ preset.label }}</option>
          </select>
        </label>
        <label :title="tip('provider')">{{ t.provider }}
          <select v-model="config.provider">
            <option value="local">Local deterministic demo</option>
            <option value="openai-compatible">OpenAI compatible</option>
          </select>
        </label>
        <label>{{ t.model }}<input v-model="config.model" placeholder="gpt-4.1 / local-researcher" /></label>
        <label>{{ t.baseUrl }}<input v-model="config.base_url" placeholder="https://api.openai.com/v1" /></label>
        <label>{{ t.apiKey }}
          <input v-model="config.api_key" type="password" :placeholder="config.has_api_key ? t.placeholders.apiSaved : t.placeholders.apiNew" />
        </label>
      </div>
      <div class="actions compact-actions">
        <label class="checkline config-check">
          <input v-model="config.http_trust_env" type="checkbox" />
          <span>{{ t.trustEnv }}</span>
        </label>
      </div>
      <p v-if="config.provider === 'local'" class="hint">{{ t.localWarning }}</p>
      <div class="actions">
        <button class="primary" type="button" @click="saveConfig">{{ t.save }}</button>
        <button class="ghost" type="button" @click="configOpen = false">{{ t.later }}</button>
      </div>
    </section>

    <section class="workspace">
      <form class="panel brief" @submit.prevent="startRun">
        <div class="section-title">
          <p class="eyebrow">RESEARCH BRIEF</p>
          <h2>{{ t.brief }}</h2>
        </div>
        <label>{{ t.seed }}
          <textarea v-model="form.seed" rows="7" :placeholder="t.placeholders.seed"></textarea>
        </label>
        <div class="grid two">
          <label>{{ t.venue }}<input v-model="form.target_venue" :placeholder="t.placeholders.venue" /></label>
          <label>{{ t.format }}
            <select v-model="form.paper_format">
              <option v-for="item in formats" :key="item.key" :value="item.key">{{ item.label }} - {{ item.note }}</option>
            </select>
          </label>
          <label :title="tip('loopMode')">{{ t.loopMode }}
            <select v-model="form.loop_mode" @change="applyPreset">
              <option value="fast">fast demo</option>
              <option value="standard">standard research</option>
              <option value="strict">strict review</option>
            </select>
          </label>
          <label>{{ t.ideas }}<input v-model.number="form.num_ideas" type="number" min="1" max="8" /></label>
          <label>{{ t.literature }}
            <select v-model="form.literature">
              <option value="local">local</option>
              <option value="semanticscholar">Semantic Scholar</option>
              <option value="openalex">OpenAlex</option>
            </select>
          </label>
          <label>{{ t.backend }}
            <select v-model="form.execution_backend">
              <option value="dry-run">dry-run</option>
              <option value="shell">shell</option>
            </select>
          </label>
          <label :title="tip('decisionRounds')">{{ t.decisionRounds }}<input v-model.number="form.decision_rounds" type="number" min="1" max="30" /></label>
          <label :title="tip('executionRounds')">{{ t.executionRounds }}<input v-model.number="form.execution_rounds" type="number" min="1" max="30" /></label>
          <label :title="tip('writingRounds')">{{ t.writingRounds }}<input v-model.number="form.writing_rounds" type="number" min="1" max="30" /></label>
          <label>{{ t.bigLoops }}<input v-model.number="form.max_big_loops" type="number" min="1" max="10" /></label>
        </div>
        <label class="checkline" :title="tip('compilePdf')">
          <input v-model="form.compile_pdf" type="checkbox" />
          <span>{{ t.compilePdf }}</span>
        </label>
        <label class="checkline">
          <input v-model="form.demo_mode" type="checkbox" />
          <span>{{ t.demoMode }}</span>
        </label>
        <label class="upload">{{ t.upload }}
          <input type="file" multiple accept=".pdf,.md,.txt,.bib" @change="onFiles" />
          <span>{{ selectedFiles.length ? `${selectedFiles.length} files selected` : t.uploadEmpty }}</span>
        </label>
        <button class="primary wide" :disabled="loading || !canRun">
          {{ loading ? t.starting : t.start }}
        </button>
        <p v-if="message" class="message">{{ message }}</p>
      </form>

      <aside class="panel observatory">
        <div class="section-title">
          <p class="eyebrow">LIVE OBSERVABILITY</p>
          <h2>{{ t.observability }}</h2>
        </div>
        <div class="progress-ring" :style="{ '--progress': progressText }">
          <span>{{ progressText }}</span>
          <small>{{ trStatus(runState?.status || 'idle') }}</small>
        </div>
        <div class="stage-map">
          <article v-for="stage in stageGroups" :key="stage.key" :class="['stage-card', stage.status]">
            <span>{{ stage.index }}</span>
            <div>
              <strong>{{ trStage(stage) }}</strong>
              <small>{{ trStatus(stage.status) }}</small>
            </div>
          </article>
          <p v-if="!stageGroups.length" class="empty">{{ t.emptyStages }}</p>
        </div>
        <div v-if="runState" class="runtime-panel">
          <div>
            <span>{{ t.currentAction }}</span>
            <strong>{{ runState.current_action }}</strong>
          </div>
          <button class="ghost compact" type="button" @click="logOpen = !logOpen">
            {{ logOpen ? t.hideLog : t.liveLog }}
          </button>
          <div v-if="logOpen" class="runtime-log">
            <button
              v-for="event in runState.logs"
              :key="`${event.time}-${event.stage}-${event.message}`"
              :class="event.status"
              type="button"
              @click="event.path && openArtifact({ title: event.message, path: event.path })"
              :title="event.detail"
            >
              <small>{{ event.stage }} {{ event.round }}</small>
              <span>{{ event.message }}</span>
            </button>
          </div>
        </div>
        <div v-if="runState" class="download-panel">
          <strong>{{ t.downloads }}</strong>
          <div v-if="runState.downloads?.length" class="download-list">
            <a v-for="item in runState.downloads" :key="item.path" :href="downloadUrl(item)">
              {{ item.title }}
            </a>
          </div>
          <p v-else class="empty">{{ t.noDownloads }}</p>
        </div>
        <a class="github-card" href="https://github.com/damonwan1/AutoScholarLoop" target="_blank" rel="noreferrer">
          <span>GitHub</span>
          <strong>{{ t.githubTitle }}</strong>
          <small>{{ t.githubText }}</small>
          <em>{{ t.githubButton }} -></em>
        </a>
      </aside>
    </section>

    <section v-if="runState" class="panel results">
      <div class="section-title">
        <p class="eyebrow">CHECKPOINTS</p>
        <h2>{{ t.checkpoints }}</h2>
      </div>
      <div class="artifact-list">
        <button
          v-for="item in runState.previews"
          :key="item.path"
          :class="{ active: activeArtifact?.path === item.path }"
          @click="openArtifact(item)"
        >
          {{ item.title }}
        </button>
      </div>
      <pre v-if="artifactText" class="markdown-preview">{{ artifactText }}</pre>
      <div v-else class="empty result-empty">{{ t.selectCheckpoint }}</div>
    </section>
  </main>
</template>
