(function () {
  const PARTICLE_PRESET_LABELS = Object.freeze({
    snow: "雪花",
    rain: "雨丝",
    petals: "樱花",
    dust: "光尘",
    embers: "火星",
    sparkles: "闪光",
    bubbles: "气泡",
    confetti: "纸片",
    smoke: "烟雾",
    flame: "火焰",
    stardust: "星尘",
    glyphs: "法阵符纹",
  });

  const PARTICLE_INTENSITY_LABELS = Object.freeze({
    light: "轻一点",
    medium: "中等",
    heavy: "浓一点",
  });

  const PARTICLE_SPEED_LABELS = Object.freeze({
    slow: "慢一点",
    medium: "正常",
    fast: "快一点",
  });

  const PARTICLE_WIND_LABELS = Object.freeze({
    left: "向左吹",
    still: "几乎无风",
    right: "向右吹",
  });

  const PARTICLE_AREA_LABELS = Object.freeze({
    full: "铺满全屏",
    left: "左半边",
    center: "中间区域",
    right: "右半边",
  });

  const PARTICLE_BLEND_LABELS = Object.freeze({
    screen: "滤色发光",
    add: "线性发光",
    normal: "正常叠加",
  });

  const PARTICLE_EMISSION_MODE_LABELS = Object.freeze({
    continuous: "持续发射",
    burst: "爆发式发射",
  });

  const PARTICLE_EMITTER_SHAPE_LABELS = Object.freeze({
    line: "线形发射器",
    point: "点发射器",
    box: "盒形发射器",
    circle: "圆形发射器",
  });

  const PARTICLE_FOLLOW_LABELS = Object.freeze({
    none: "固定在画面上",
    character: "跟随当前说话角色",
    camera: "跟随镜头中心",
  });

  const PARTICLE_FOLLOW_ANCHOR_LABELS = Object.freeze({
    head: "头部附近",
    torso: "身体中段",
    feet: "脚边 / 地面",
  });

  const PARTICLE_SIZE_CURVE_LABELS = Object.freeze({
    steady: "尺寸保持稳定",
    bloom: "先小后大",
    shrink: "慢慢缩小",
    pulse: "中段放大",
  });

  const PARTICLE_OPACITY_CURVE_LABELS = Object.freeze({
    fade: "正常淡出",
    linger: "停留更久",
    blink: "中段更亮",
    pop: "先亮后淡",
  });

  const PARTICLE_COLOR_CURVE_LABELS = Object.freeze({
    steady: "颜色保持稳定",
    cool_shift: "慢慢偏冷",
    warm_shift: "越烧越暖",
    spectral: "光谱漂移",
    pulse_glow: "中段爆亮",
  });

  const PARTICLE_FORCE_FIELD_LABELS = Object.freeze({
    none: "无中心力场",
    attract: "吸附中心",
    repel: "排斥中心",
    orbit: "环绕中心",
  });

  const PARTICLE_SIZE_CURVE_PROFILES = Object.freeze({
    steady: Object.freeze({ start: 1, mid: 1.02, end: 1.04 }),
    bloom: Object.freeze({ start: 0.48, mid: 0.92, end: 1.18 }),
    shrink: Object.freeze({ start: 1.16, mid: 0.94, end: 0.66 }),
    pulse: Object.freeze({ start: 0.68, mid: 1.28, end: 0.82 }),
  });

  const PARTICLE_OPACITY_CURVE_PROFILES = Object.freeze({
    fade: Object.freeze({ start: 1, mid: 0.74, end: 0.12 }),
    linger: Object.freeze({ start: 0.82, mid: 0.86, end: 0.26 }),
    blink: Object.freeze({ start: 0.44, mid: 1, end: 0.14 }),
    pop: Object.freeze({ start: 1, mid: 0.54, end: 0.08 }),
  });

  const PARTICLE_FORCE_FIELD_PROFILES = Object.freeze({
    none: Object.freeze({ x: 0, y: 0, orbit: 0 }),
    attract: Object.freeze({ x: 0.62, y: 0.62, orbit: 0.08 }),
    repel: Object.freeze({ x: -0.68, y: -0.68, orbit: 0.06 }),
    orbit: Object.freeze({ x: 0.22, y: 0.22, orbit: 0.78 }),
  });

  const PARTICLE_COLOR_CURVE_PROFILES = Object.freeze({
    steady: Object.freeze({
      hue: Object.freeze({ start: 0, mid: 0, end: 0 }),
      saturation: Object.freeze({ start: 1, mid: 1, end: 1 }),
      brightness: Object.freeze({ start: 1, mid: 1, end: 1 }),
    }),
    cool_shift: Object.freeze({
      hue: Object.freeze({ start: 0, mid: 10, end: 22 }),
      saturation: Object.freeze({ start: 0.98, mid: 1.08, end: 1.14 }),
      brightness: Object.freeze({ start: 0.98, mid: 1.04, end: 0.94 }),
    }),
    warm_shift: Object.freeze({
      hue: Object.freeze({ start: 0, mid: -10, end: -24 }),
      saturation: Object.freeze({ start: 1, mid: 1.12, end: 1.18 }),
      brightness: Object.freeze({ start: 0.96, mid: 1.08, end: 0.9 }),
    }),
    spectral: Object.freeze({
      hue: Object.freeze({ start: -10, mid: 18, end: 54 }),
      saturation: Object.freeze({ start: 1.04, mid: 1.22, end: 1.12 }),
      brightness: Object.freeze({ start: 0.94, mid: 1.12, end: 0.96 }),
    }),
    pulse_glow: Object.freeze({
      hue: Object.freeze({ start: 0, mid: 4, end: 0 }),
      saturation: Object.freeze({ start: 1, mid: 1.28, end: 1.04 }),
      brightness: Object.freeze({ start: 0.94, mid: 1.26, end: 0.9 }),
    }),
  });

  const PARTICLE_COMBO_PRESET_LABELS = Object.freeze({
    none: "单层粒子",
    blizzard_stack: "暴风雪叠层",
    inferno_stack: "火焰仪式叠层",
    arcane_stack: "魔法阵叠层",
    celestial_stack: "星海梦境叠层",
    celebration_stack: "礼花舞台叠层",
  });

  const PARTICLE_SCENE_PRESET_LABELS = Object.freeze({
    blizzard: "暴雪",
    thunderstorm: "暴雨",
    magic_burst: "魔法火花",
    ember_field: "火焰余烬",
    underwater: "水底气泡",
    festival: "舞台礼花",
    smoke_veil: "烟雾幕帘",
    flame_aura: "火焰环流",
    stardust_field: "星尘漂流",
    magic_circle: "魔法阵环",
  });

  const PARTICLE_CUSTOM_COMBO_LAYER_LIMIT = 6;
  const PARTICLE_CUSTOM_PRESET_LIMIT = 24;
  const PARTICLE_IMAGE_ASSET_TYPES = Object.freeze(["background", "sprite", "cg", "ui"]);

const PARTICLE_PRESET_DEFAULTS = {
  snow: {
    density: 40,
    sizeMin: 6,
    sizeMax: 18,
    lifeMin: 6,
    lifeMax: 11,
    gravityX: 0,
    gravityY: 70,
    gravityZ: 16,
    spreadX: 100,
    spreadY: 22,
    spreadZ: 36,
    opacityMin: 0.38,
    opacityMax: 0.95,
    rotationMin: 0,
    rotationMax: 180,
    spin: 55,
    turbulence: 22,
    color: "#ffffff",
    colorAccent: "#dff4ff",
    blend: "screen",
  },
  rain: {
    density: 56,
    sizeMin: 2,
    sizeMax: 4,
    lifeMin: 1.2,
    lifeMax: 2.5,
    gravityX: 18,
    gravityY: 190,
    gravityZ: -8,
    spreadX: 100,
    spreadY: 14,
    spreadZ: 20,
    opacityMin: 0.26,
    opacityMax: 0.82,
    rotationMin: 8,
    rotationMax: 14,
    spin: 0,
    turbulence: 10,
    color: "#b7dcff",
    colorAccent: "#f0fbff",
    blend: "screen",
  },
  petals: {
    density: 28,
    sizeMin: 12,
    sizeMax: 22,
    lifeMin: 4.5,
    lifeMax: 8.2,
    gravityX: 0,
    gravityY: 58,
    gravityZ: 6,
    spreadX: 100,
    spreadY: 24,
    spreadZ: 42,
    opacityMin: 0.48,
    opacityMax: 0.96,
    rotationMin: -20,
    rotationMax: 40,
    spin: 120,
    turbulence: 36,
    color: "#ffd6ea",
    colorAccent: "#fff3f8",
    blend: "screen",
  },
  dust: {
    density: 26,
    sizeMin: 4,
    sizeMax: 12,
    lifeMin: 5.5,
    lifeMax: 11,
    gravityX: 0,
    gravityY: 24,
    gravityZ: 24,
    spreadX: 100,
    spreadY: 40,
    spreadZ: 70,
    opacityMin: 0.18,
    opacityMax: 0.72,
    rotationMin: 0,
    rotationMax: 360,
    spin: 40,
    turbulence: 24,
    color: "#c4f6ff",
    colorAccent: "#f8fdff",
    blend: "screen",
  },
  embers: {
    density: 24,
    sizeMin: 3,
    sizeMax: 9,
    lifeMin: 2.6,
    lifeMax: 6.4,
    gravityX: 6,
    gravityY: -46,
    gravityZ: 30,
    spreadX: 100,
    spreadY: 36,
    spreadZ: 54,
    opacityMin: 0.3,
    opacityMax: 0.92,
    rotationMin: 0,
    rotationMax: 180,
    spin: 80,
    turbulence: 34,
    color: "#ffb36b",
    colorAccent: "#fff1b5",
    blend: "add",
  },
  sparkles: {
    density: 18,
    sizeMin: 5,
    sizeMax: 12,
    lifeMin: 1.8,
    lifeMax: 4.2,
    gravityX: 0,
    gravityY: 16,
    gravityZ: 36,
    spreadX: 100,
    spreadY: 50,
    spreadZ: 58,
    opacityMin: 0.28,
    opacityMax: 1,
    rotationMin: 0,
    rotationMax: 180,
    spin: 180,
    turbulence: 26,
    color: "#dff8ff",
    colorAccent: "#8fe8ff",
    blend: "add",
  },
  bubbles: {
    density: 20,
    sizeMin: 10,
    sizeMax: 26,
    lifeMin: 3.8,
    lifeMax: 8.6,
    gravityX: 0,
    gravityY: -72,
    gravityZ: 28,
    spreadX: 100,
    spreadY: 44,
    spreadZ: 64,
    opacityMin: 0.18,
    opacityMax: 0.62,
    rotationMin: -16,
    rotationMax: 16,
    spin: 36,
    turbulence: 18,
    color: "#b6f3ff",
    colorAccent: "#effcff",
    blend: "normal",
  },
  confetti: {
    density: 34,
    sizeMin: 6,
    sizeMax: 14,
    lifeMin: 3.2,
    lifeMax: 6.4,
    gravityX: 0,
    gravityY: 120,
    gravityZ: 18,
    spreadX: 100,
    spreadY: 26,
    spreadZ: 48,
    opacityMin: 0.52,
    opacityMax: 0.98,
    rotationMin: 0,
    rotationMax: 360,
    spin: 240,
    turbulence: 42,
    color: "#7fe7ff",
    colorAccent: "#ff8ee3",
    blend: "normal",
  },
  smoke: {
    density: 22,
    sizeMin: 24,
    sizeMax: 64,
    lifeMin: 4.6,
    lifeMax: 10.8,
    gravityX: 0,
    gravityY: -24,
    gravityZ: 42,
    spreadX: 72,
    spreadY: 44,
    spreadZ: 80,
    opacityMin: 0.14,
    opacityMax: 0.46,
    rotationMin: -26,
    rotationMax: 26,
    spin: 18,
    turbulence: 32,
    color: "#aebed4",
    colorAccent: "#f1f7ff",
    blend: "normal",
  },
  flame: {
    density: 26,
    sizeMin: 14,
    sizeMax: 34,
    lifeMin: 1.4,
    lifeMax: 3.8,
    gravityX: 0,
    gravityY: -82,
    gravityZ: 24,
    spreadX: 40,
    spreadY: 36,
    spreadZ: 44,
    opacityMin: 0.34,
    opacityMax: 0.92,
    rotationMin: -18,
    rotationMax: 18,
    spin: 58,
    turbulence: 44,
    color: "#ff8b3d",
    colorAccent: "#fff4a6",
    blend: "add",
  },
  stardust: {
    density: 30,
    sizeMin: 3,
    sizeMax: 10,
    lifeMin: 5.4,
    lifeMax: 12.6,
    gravityX: 0,
    gravityY: 8,
    gravityZ: 54,
    spreadX: 100,
    spreadY: 60,
    spreadZ: 90,
    opacityMin: 0.18,
    opacityMax: 0.86,
    rotationMin: 0,
    rotationMax: 240,
    spin: 140,
    turbulence: 28,
    color: "#8edbff",
    colorAccent: "#fff1ff",
    blend: "screen",
  },
  glyphs: {
    density: 14,
    sizeMin: 18,
    sizeMax: 36,
    lifeMin: 2.6,
    lifeMax: 5.8,
    gravityX: 0,
    gravityY: 0,
    gravityZ: 18,
    spreadX: 34,
    spreadY: 18,
    spreadZ: 26,
    opacityMin: 0.34,
    opacityMax: 0.92,
    rotationMin: -12,
    rotationMax: 12,
    spin: 120,
    turbulence: 14,
    color: "#85d4ff",
    colorAccent: "#f7dcff",
    blend: "add",
  },
};

const PARTICLE_PRESET_ADVANCED_DEFAULTS = {
  snow: {
    emissionMode: "continuous",
    emitterShape: "line",
    emitterX: 50,
    emitterY: -6,
    emitterZ: 0,
    attractionX: 0,
    attractionY: 0,
    vortex: 12,
    follow: "none",
    sizeCurve: "steady",
    opacityCurve: "linger",
    forceField: "none",
    fieldX: 50,
    fieldY: 52,
  },
  rain: {
    emissionMode: "continuous",
    emitterShape: "line",
    emitterX: 50,
    emitterY: -8,
    emitterZ: -8,
    attractionX: 10,
    attractionY: 0,
    vortex: 6,
    follow: "none",
    sizeCurve: "steady",
    opacityCurve: "fade",
    forceField: "none",
    fieldX: 50,
    fieldY: 58,
  },
  petals: {
    emissionMode: "continuous",
    emitterShape: "line",
    emitterX: 50,
    emitterY: -4,
    emitterZ: 10,
    attractionX: 0,
    attractionY: 4,
    vortex: 48,
    follow: "none",
    sizeCurve: "pulse",
    opacityCurve: "linger",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 56,
  },
  dust: {
    emissionMode: "continuous",
    emitterShape: "box",
    emitterX: 50,
    emitterY: 52,
    emitterZ: 20,
    attractionX: 0,
    attractionY: -4,
    vortex: 18,
    follow: "none",
    sizeCurve: "bloom",
    opacityCurve: "linger",
    forceField: "attract",
    fieldX: 50,
    fieldY: 54,
  },
  embers: {
    emissionMode: "continuous",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 104,
    emitterZ: 24,
    attractionX: 0,
    attractionY: -14,
    vortex: 65,
    follow: "none",
    sizeCurve: "shrink",
    opacityCurve: "pop",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 84,
  },
  sparkles: {
    emissionMode: "burst",
    emitterShape: "point",
    emitterX: 50,
    emitterY: 48,
    emitterZ: 0,
    attractionX: 0,
    attractionY: 0,
    vortex: 95,
    follow: "none",
    sizeCurve: "pulse",
    opacityCurve: "blink",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 50,
  },
  bubbles: {
    emissionMode: "continuous",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 106,
    emitterZ: 26,
    attractionX: 0,
    attractionY: -18,
    vortex: 24,
    follow: "none",
    sizeCurve: "bloom",
    opacityCurve: "linger",
    forceField: "attract",
    fieldX: 50,
    fieldY: 42,
  },
  confetti: {
    emissionMode: "burst",
    emitterShape: "line",
    emitterX: 50,
    emitterY: -6,
    emitterZ: 6,
    attractionX: 0,
    attractionY: 16,
    vortex: 110,
    follow: "none",
    sizeCurve: "pulse",
    opacityCurve: "pop",
    forceField: "repel",
    fieldX: 50,
    fieldY: 40,
  },
  smoke: {
    emissionMode: "continuous",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 94,
    emitterZ: 22,
    attractionX: 0,
    attractionY: -10,
    vortex: 36,
    follow: "none",
    sizeCurve: "bloom",
    opacityCurve: "linger",
    forceField: "attract",
    fieldX: 50,
    fieldY: 58,
  },
  flame: {
    emissionMode: "continuous",
    emitterShape: "point",
    emitterX: 50,
    emitterY: 94,
    emitterZ: 12,
    attractionX: 0,
    attractionY: -22,
    vortex: 84,
    follow: "none",
    sizeCurve: "shrink",
    opacityCurve: "pop",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 76,
  },
  stardust: {
    emissionMode: "continuous",
    emitterShape: "box",
    emitterX: 50,
    emitterY: 48,
    emitterZ: 36,
    attractionX: 0,
    attractionY: 0,
    vortex: 72,
    follow: "camera",
    sizeCurve: "pulse",
    opacityCurve: "blink",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 50,
  },
  glyphs: {
    emissionMode: "burst",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 56,
    emitterZ: 10,
    attractionX: 0,
    attractionY: 0,
    vortex: 150,
    follow: "character",
    sizeCurve: "pulse",
    opacityCurve: "blink",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 56,
  },
};

const PARTICLE_SCENE_PRESET_CONFIGS = {
  blizzard: {
    preset: "snow",
    comboPreset: "blizzard_stack",
    intensity: "heavy",
    speed: "fast",
    wind: "left",
    area: "full",
    density: 96,
    sizeMin: 7,
    sizeMax: 22,
    lifeMin: 5.6,
    lifeMax: 10.2,
    gravityX: -38,
    gravityY: 102,
    gravityZ: 28,
    spreadX: 100,
    spreadY: 34,
    spreadZ: 60,
    turbulence: 46,
    emissionMode: "continuous",
    emitterShape: "line",
    sizeCurve: "steady",
    opacityCurve: "linger",
    forceField: "attract",
    fieldX: 42,
    fieldY: 60,
    color: "#f4fbff",
    colorAccent: "#d8f4ff",
    blend: "screen",
  },
  thunderstorm: {
    preset: "rain",
    intensity: "heavy",
    speed: "fast",
    wind: "right",
    area: "full",
    density: 110,
    sizeMin: 2,
    sizeMax: 5,
    lifeMin: 0.9,
    lifeMax: 1.8,
    gravityX: 46,
    gravityY: 230,
    gravityZ: -18,
    spreadX: 100,
    spreadY: 18,
    spreadZ: 30,
    turbulence: 18,
    emissionMode: "continuous",
    emitterShape: "line",
    sizeCurve: "steady",
    opacityCurve: "fade",
    forceField: "none",
    color: "#9bd4ff",
    colorAccent: "#f0fbff",
    blend: "screen",
  },
  magic_burst: {
    preset: "sparkles",
    comboPreset: "arcane_stack",
    intensity: "heavy",
    speed: "medium",
    wind: "still",
    area: "center",
    density: 42,
    sizeMin: 6,
    sizeMax: 18,
    lifeMin: 1.4,
    lifeMax: 3.4,
    gravityX: 0,
    gravityY: 16,
    gravityZ: 42,
    spreadX: 44,
    spreadY: 44,
    spreadZ: 72,
    turbulence: 52,
    emissionMode: "burst",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 54,
    vortex: 150,
    sizeCurve: "pulse",
    opacityCurve: "blink",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 52,
    color: "#9de4ff",
    colorAccent: "#fff0ff",
    blend: "add",
  },
  ember_field: {
    preset: "embers",
    comboPreset: "inferno_stack",
    intensity: "heavy",
    speed: "slow",
    wind: "left",
    area: "full",
    density: 54,
    sizeMin: 4,
    sizeMax: 12,
    lifeMin: 3.2,
    lifeMax: 7.2,
    gravityX: -12,
    gravityY: -52,
    gravityZ: 38,
    spreadX: 92,
    spreadY: 44,
    spreadZ: 68,
    turbulence: 58,
    emissionMode: "continuous",
    emitterShape: "box",
    emitterY: 94,
    vortex: 120,
    sizeCurve: "shrink",
    opacityCurve: "pop",
    forceField: "orbit",
    fieldX: 54,
    fieldY: 76,
    color: "#ff9a57",
    colorAccent: "#fff0b3",
    blend: "add",
  },
  underwater: {
    preset: "bubbles",
    intensity: "medium",
    speed: "slow",
    wind: "still",
    area: "center",
    density: 34,
    sizeMin: 10,
    sizeMax: 30,
    lifeMin: 4.5,
    lifeMax: 9.6,
    gravityX: 0,
    gravityY: -80,
    gravityZ: 38,
    spreadX: 54,
    spreadY: 58,
    spreadZ: 82,
    turbulence: 26,
    emissionMode: "continuous",
    emitterShape: "circle",
    emitterX: 50,
    emitterY: 106,
    sizeCurve: "bloom",
    opacityCurve: "linger",
    forceField: "attract",
    fieldX: 50,
    fieldY: 36,
    color: "#8de9ff",
    colorAccent: "#f2ffff",
    blend: "normal",
  },
  festival: {
    preset: "confetti",
    comboPreset: "celebration_stack",
    intensity: "heavy",
    speed: "medium",
    wind: "still",
    area: "full",
    density: 56,
    sizeMin: 7,
    sizeMax: 16,
    lifeMin: 2.4,
    lifeMax: 4.8,
    gravityX: 0,
    gravityY: 144,
    gravityZ: 24,
    spreadX: 100,
    spreadY: 32,
    spreadZ: 56,
    turbulence: 62,
    emissionMode: "burst",
    emitterShape: "line",
    emitterY: -6,
    vortex: 132,
    sizeCurve: "pulse",
    opacityCurve: "pop",
    forceField: "repel",
    fieldX: 50,
    fieldY: 46,
    color: "#8ce7ff",
    colorAccent: "#ff8ada",
    blend: "normal",
  },
  smoke_veil: {
    preset: "smoke",
    intensity: "medium",
    speed: "slow",
    wind: "left",
    area: "full",
    density: 30,
    sizeMin: 28,
    sizeMax: 72,
    lifeMin: 5.4,
    lifeMax: 12,
    gravityX: -8,
    gravityY: -18,
    gravityZ: 52,
    spreadX: 84,
    spreadY: 56,
    spreadZ: 90,
    turbulence: 44,
    emissionMode: "continuous",
    emitterShape: "box",
    emitterY: 86,
    sizeCurve: "bloom",
    opacityCurve: "linger",
    forceField: "attract",
    fieldX: 46,
    fieldY: 50,
    color: "#b1bfd3",
    colorAccent: "#eef4ff",
    blend: "normal",
  },
  flame_aura: {
    preset: "flame",
    comboPreset: "inferno_stack",
    intensity: "heavy",
    speed: "medium",
    wind: "still",
    area: "center",
    density: 34,
    sizeMin: 16,
    sizeMax: 34,
    lifeMin: 1.2,
    lifeMax: 3.2,
    gravityX: 0,
    gravityY: -96,
    gravityZ: 28,
    spreadX: 36,
    spreadY: 30,
    spreadZ: 38,
    turbulence: 56,
    emissionMode: "continuous",
    emitterShape: "circle",
    emitterY: 92,
    follow: "character",
    sizeCurve: "shrink",
    opacityCurve: "pop",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 74,
    color: "#ff8d42",
    colorAccent: "#fff0ab",
    blend: "add",
  },
  stardust_field: {
    preset: "stardust",
    comboPreset: "celestial_stack",
    intensity: "medium",
    speed: "slow",
    wind: "still",
    area: "full",
    density: 42,
    sizeMin: 3,
    sizeMax: 12,
    lifeMin: 6.8,
    lifeMax: 13.4,
    gravityX: 0,
    gravityY: 6,
    gravityZ: 66,
    spreadX: 100,
    spreadY: 62,
    spreadZ: 100,
    turbulence: 32,
    emissionMode: "continuous",
    emitterShape: "box",
    emitterY: 48,
    follow: "camera",
    sizeCurve: "pulse",
    opacityCurve: "blink",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 50,
    color: "#97ddff",
    colorAccent: "#ffe5ff",
    blend: "screen",
  },
  magic_circle: {
    preset: "glyphs",
    comboPreset: "arcane_stack",
    intensity: "heavy",
    speed: "slow",
    wind: "still",
    area: "center",
    density: 18,
    sizeMin: 20,
    sizeMax: 38,
    lifeMin: 2.8,
    lifeMax: 6.4,
    gravityX: 0,
    gravityY: 0,
    gravityZ: 14,
    spreadX: 28,
    spreadY: 12,
    spreadZ: 32,
    turbulence: 16,
    emissionMode: "burst",
    emitterShape: "circle",
    emitterY: 56,
    follow: "character",
    sizeCurve: "pulse",
    opacityCurve: "blink",
    forceField: "orbit",
    fieldX: 50,
    fieldY: 56,
    color: "#8fd8ff",
    colorAccent: "#f5d8ff",
    blend: "add",
  },
};

const PARTICLE_COMBO_PRESET_CONFIGS = {
  none: [],
  blizzard_stack: [
    {
      preset: "snow",
      densityMultiplier: 0.84,
      layerCount: 2,
      sizeScale: 1.08,
      lifeScale: 1.12,
      spreadYMultiplier: 1.18,
      spreadZAdd: 18,
      turbulenceAdd: 10,
      opacityScale: 0.92,
      follow: "camera",
      followAnchor: "torso",
      blend: "screen",
      colorMix: 0.28,
    },
    {
      preset: "dust",
      densityMultiplier: 0.42,
      sizeScale: 1.52,
      lifeScale: 1.34,
      spreadYMultiplier: 1.46,
      spreadZAdd: 24,
      gravityYAdd: -10,
      turbulenceAdd: 18,
      opacityScale: 0.46,
      follow: "camera",
      followAnchor: "torso",
      forceField: "attract",
      blend: "screen",
      color: "#d9efff",
      colorAccent: "#ffffff",
      colorEnd: "#b8d8ff",
    },
  ],
  inferno_stack: [
    {
      preset: "flame",
      densityMultiplier: 0.88,
      layerCount: 2,
      sizeScale: 1.04,
      opacityScale: 0.96,
      follow: "character",
      followAnchor: "feet",
      emitterYOffset: 10,
      blend: "add",
      colorMix: 0.36,
    },
    {
      preset: "smoke",
      densityMultiplier: 0.44,
      sizeScale: 1.62,
      lifeScale: 1.26,
      spreadYMultiplier: 1.38,
      spreadZAdd: 28,
      gravityYAdd: -14,
      turbulenceAdd: 14,
      opacityScale: 0.56,
      follow: "character",
      followAnchor: "torso",
      emitterYOffset: 4,
      blend: "normal",
      color: "#9e95a6",
      colorAccent: "#ddd8e8",
      colorEnd: "#706978",
    },
    {
      preset: "embers",
      densityMultiplier: 0.48,
      sizeScale: 0.92,
      lifeScale: 0.92,
      opacityScale: 0.78,
      follow: "character",
      followAnchor: "torso",
      emitterYOffset: 8,
      blend: "add",
      colorMix: 0.22,
    },
  ],
  arcane_stack: [
    {
      preset: "glyphs",
      densityMultiplier: 0.9,
      layerCount: 2,
      sizeScale: 1.06,
      opacityScale: 0.92,
      follow: "character",
      followAnchor: "feet",
      forceField: "orbit",
      blend: "add",
      colorMix: 0.48,
    },
    {
      preset: "stardust",
      densityMultiplier: 0.54,
      sizeScale: 0.92,
      lifeScale: 1.12,
      spreadZAdd: 34,
      turbulenceAdd: 18,
      opacityScale: 0.72,
      follow: "camera",
      followAnchor: "torso",
      area: "center",
      blend: "screen",
      colorMix: 0.52,
    },
    {
      preset: "sparkles",
      densityMultiplier: 0.34,
      sizeScale: 0.82,
      opacityScale: 0.78,
      emissionMode: "burst",
      follow: "character",
      followAnchor: "torso",
      emitterShape: "circle",
      blend: "add",
      colorMix: 0.48,
    },
  ],
  celestial_stack: [
    {
      preset: "stardust",
      densityMultiplier: 0.88,
      layerCount: 2,
      opacityScale: 0.92,
      follow: "camera",
      followAnchor: "torso",
      blend: "screen",
      colorMix: 0.46,
    },
    {
      preset: "dust",
      densityMultiplier: 0.4,
      sizeScale: 1.44,
      lifeScale: 1.28,
      spreadZAdd: 30,
      opacityScale: 0.42,
      turbulenceAdd: 18,
      follow: "camera",
      followAnchor: "torso",
      blend: "screen",
      colorMix: 0.44,
    },
    {
      preset: "bubbles",
      densityMultiplier: 0.24,
      sizeScale: 0.74,
      lifeScale: 1.12,
      gravityYAdd: -22,
      opacityScale: 0.36,
      follow: "camera",
      followAnchor: "torso",
      area: "center",
      blend: "normal",
      colorMix: 0.34,
    },
  ],
  celebration_stack: [
    {
      preset: "confetti",
      densityMultiplier: 0.78,
      layerCount: 2,
      emissionMode: "burst",
      opacityScale: 0.96,
      blend: "normal",
      colorMix: 0.3,
    },
    {
      preset: "sparkles",
      densityMultiplier: 0.4,
      sizeScale: 0.82,
      opacityScale: 0.82,
      emissionMode: "burst",
      blend: "add",
      colorMix: 0.44,
    },
    {
      preset: "stardust",
      densityMultiplier: 0.26,
      lifeScale: 0.92,
      opacityScale: 0.46,
      follow: "camera",
      followAnchor: "torso",
      blend: "screen",
      colorMix: 0.38,
    },
  ],
};


  function hasOwnKey(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getEscapeHtml(options = {}) {
    return typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  }

  function getSafeNumber(value, fallback) {
    const parsed = Number.parseFloat(value ?? "");
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function getSafeParticleAction(action) {
    return action === "stop" ? "stop" : "start";
  }

  function getParticleActionLabel(action) {
    return getSafeParticleAction(action) === "stop" ? "关闭当前粒子特效" : "开始粒子特效";
  }

  function getSafeParticlePreset(preset) {
    return hasOwnKey(PARTICLE_PRESET_LABELS, preset) ? preset : "snow";
  }

  function getParticlePresetLabel(preset) {
    return PARTICLE_PRESET_LABELS[getSafeParticlePreset(preset)];
  }

  function getParticlePresetDefaults(preset) {
    return PARTICLE_PRESET_DEFAULTS[getSafeParticlePreset(preset)] ?? PARTICLE_PRESET_DEFAULTS.snow;
  }

  function getParticleAdvancedDefaults(preset) {
    return (
      PARTICLE_PRESET_ADVANCED_DEFAULTS[getSafeParticlePreset(preset)] ?? PARTICLE_PRESET_ADVANCED_DEFAULTS.snow
    );
  }

  function getSafeParticleIntensity(intensity) {
    return hasOwnKey(PARTICLE_INTENSITY_LABELS, intensity) ? intensity : "medium";
  }

  function getParticleIntensityLabel(intensity) {
    return PARTICLE_INTENSITY_LABELS[getSafeParticleIntensity(intensity)];
  }

  function getSafeParticleSpeed(speed) {
    return hasOwnKey(PARTICLE_SPEED_LABELS, speed) ? speed : "medium";
  }

  function getParticleSpeedLabel(speed) {
    return PARTICLE_SPEED_LABELS[getSafeParticleSpeed(speed)];
  }

  function getSafeParticleWind(wind) {
    return hasOwnKey(PARTICLE_WIND_LABELS, wind) ? wind : "still";
  }

  function getParticleWindLabel(wind) {
    return PARTICLE_WIND_LABELS[getSafeParticleWind(wind)];
  }

  function getSafeParticleArea(area) {
    return hasOwnKey(PARTICLE_AREA_LABELS, area) ? area : "full";
  }

  function getParticleAreaLabel(area) {
    return PARTICLE_AREA_LABELS[getSafeParticleArea(area)];
  }

  function getSafeParticleBlendMode(blend) {
    return hasOwnKey(PARTICLE_BLEND_LABELS, blend) ? blend : "screen";
  }

  function getParticleBlendModeLabel(blend) {
    return PARTICLE_BLEND_LABELS[getSafeParticleBlendMode(blend)];
  }

  function getParticleBlendCssValue(blend) {
    const safeBlend = getSafeParticleBlendMode(blend);
    return safeBlend === "add" ? "plus-lighter" : safeBlend;
  }

  function getSafeParticleEmissionMode(mode) {
    return hasOwnKey(PARTICLE_EMISSION_MODE_LABELS, mode) ? mode : "continuous";
  }

  function getParticleEmissionModeLabel(mode) {
    return PARTICLE_EMISSION_MODE_LABELS[getSafeParticleEmissionMode(mode)];
  }

  function getSafeParticleEmitterShape(shape) {
    return hasOwnKey(PARTICLE_EMITTER_SHAPE_LABELS, shape) ? shape : "line";
  }

  function getParticleEmitterShapeLabel(shape) {
    return PARTICLE_EMITTER_SHAPE_LABELS[getSafeParticleEmitterShape(shape)];
  }

  function getSafeParticleFollowTarget(follow) {
    return hasOwnKey(PARTICLE_FOLLOW_LABELS, follow) ? follow : "none";
  }

  function getParticleFollowTargetLabel(follow) {
    return PARTICLE_FOLLOW_LABELS[getSafeParticleFollowTarget(follow)];
  }

  function getSafeParticleFollowAnchor(anchor) {
    return hasOwnKey(PARTICLE_FOLLOW_ANCHOR_LABELS, anchor) ? anchor : "torso";
  }

  function getParticleFollowAnchorLabel(anchor) {
    return PARTICLE_FOLLOW_ANCHOR_LABELS[getSafeParticleFollowAnchor(anchor)];
  }

  function getSafeParticleSizeCurve(curve) {
    return hasOwnKey(PARTICLE_SIZE_CURVE_LABELS, curve) ? curve : "steady";
  }

  function getParticleSizeCurveLabel(curve) {
    return PARTICLE_SIZE_CURVE_LABELS[getSafeParticleSizeCurve(curve)];
  }

  function getSafeParticleOpacityCurve(curve) {
    return hasOwnKey(PARTICLE_OPACITY_CURVE_LABELS, curve) ? curve : "fade";
  }

  function getParticleOpacityCurveLabel(curve) {
    return PARTICLE_OPACITY_CURVE_LABELS[getSafeParticleOpacityCurve(curve)];
  }

  function getSafeParticleColorCurve(curve) {
    return hasOwnKey(PARTICLE_COLOR_CURVE_LABELS, curve) ? curve : "steady";
  }

  function getParticleColorCurveLabel(curve) {
    return PARTICLE_COLOR_CURVE_LABELS[getSafeParticleColorCurve(curve)];
  }

  function getSafeParticleForceField(mode) {
    return hasOwnKey(PARTICLE_FORCE_FIELD_LABELS, mode) ? mode : "none";
  }

  function getParticleForceFieldLabel(mode) {
    return PARTICLE_FORCE_FIELD_LABELS[getSafeParticleForceField(mode)];
  }

  function getSafeParticleComboPreset(comboPreset) {
    return hasOwnKey(PARTICLE_COMBO_PRESET_LABELS, comboPreset) ? comboPreset : "none";
  }

  function getParticleComboPresetLabel(comboPreset) {
    return PARTICLE_COMBO_PRESET_LABELS[getSafeParticleComboPreset(comboPreset)];
  }

  function getParticleScenePresetConfig(presetId) {
    return PARTICLE_SCENE_PRESET_CONFIGS[presetId] ?? null;
  }

  function getParticleComboPresetConfig(comboPreset) {
    return PARTICLE_COMBO_PRESET_CONFIGS[getSafeParticleComboPreset(comboPreset)] ?? [];
  }

  function buildDefaultParticleCustomComboLayer(preset = "stardust") {
    const safePreset = getSafeParticlePreset(preset);
    const defaults = getParticlePresetDefaults(safePreset);
    const advancedDefaults = getParticleAdvancedDefaults(safePreset);
    return {
      enabled: false,
      preset: safePreset,
      emissionMode: advancedDefaults.emissionMode,
      follow: advancedDefaults.follow,
      followAnchor: "torso",
      densityMultiplier: 1,
      sizeScale: 1,
      lifeScale: 1,
      opacityScale: 1,
      colorMix: 0.42,
      blend: defaults.blend,
    };
  }

  function normalizeParticleCustomComboLayer(layer, fallbackPreset = "stardust") {
    const base = buildDefaultParticleCustomComboLayer(layer?.preset ?? fallbackPreset);
    return {
      enabled: Boolean(layer?.enabled),
      preset: getSafeParticlePreset(layer?.preset ?? base.preset),
      emissionMode: getSafeParticleEmissionMode(layer?.emissionMode ?? base.emissionMode),
      follow: getSafeParticleFollowTarget(layer?.follow ?? base.follow),
      followAnchor: getSafeParticleFollowAnchor(layer?.followAnchor ?? base.followAnchor),
      densityMultiplier: getSafeParticleClampedNumber(layer?.densityMultiplier, 1, 0.2, 4),
      sizeScale: getSafeParticleClampedNumber(layer?.sizeScale, 1, 0.2, 4),
      lifeScale: getSafeParticleClampedNumber(layer?.lifeScale, 1, 0.2, 4),
      opacityScale: getSafeParticleClampedNumber(layer?.opacityScale, 1, 0.1, 2),
      colorMix: getSafeParticleClampedNumber(layer?.colorMix, 0.42, 0, 1),
      blend: getSafeParticleBlendMode(layer?.blend ?? base.blend),
    };
  }

  function normalizeParticleCustomComboLayers(layers) {
    const source = Array.isArray(layers) ? layers.slice(0, PARTICLE_CUSTOM_COMBO_LAYER_LIMIT) : [];
    return source.map((layer, index) =>
      normalizeParticleCustomComboLayer(layer, index === 0 ? "stardust" : "smoke")
    );
  }

  function getEnabledParticleCustomComboLayers(layers) {
    return normalizeParticleCustomComboLayers(layers).filter((layer) => layer.enabled);
  }

  function getParticleCustomComboLayerSummary(layers) {
    const enabledLayers = getEnabledParticleCustomComboLayers(layers);
    if (!enabledLayers.length) {
      return "未额外叠层";
    }

    return enabledLayers
      .map(
        (layer, index) =>
          `L${index + 2}:${getParticlePresetLabel(layer.preset)} / ×${formatParticleNumber(
            layer.densityMultiplier,
            1
          )} / ${getParticleBlendModeLabel(layer.blend)}`
      )
      .join(" · ");
  }

  function getParticleDefaultColorCurve(preset) {
    return (
      {
        snow: "cool_shift",
        rain: "cool_shift",
        petals: "steady",
        dust: "steady",
        embers: "warm_shift",
        sparkles: "pulse_glow",
        bubbles: "cool_shift",
        confetti: "steady",
        smoke: "cool_shift",
        flame: "warm_shift",
        stardust: "spectral",
        glyphs: "spectral",
      }[getSafeParticlePreset(preset)] ?? "steady"
    );
  }

  function getSafeParticleLayerCount(layerCount) {
    return clamp(Math.round(getSafeNumber(layerCount, 1)), 1, 3);
  }

  function getSafeParticleClampedNumber(value, fallback, min, max) {
    return clamp(getSafeNumber(value, fallback), min, max);
  }

  function buildDefaultParticleEffectConfig(preset = "snow") {
    const safePreset = getSafeParticlePreset(preset);
    const defaults = getParticlePresetDefaults(safePreset);
    const advancedDefaults = getParticleAdvancedDefaults(safePreset);
    return {
      action: "start",
      preset: safePreset,
      assetId: "",
      intensity: "medium",
      speed: "medium",
      wind: "still",
      area: "full",
      emissionMode: advancedDefaults.emissionMode,
      emitterShape: advancedDefaults.emitterShape,
      emitterX: advancedDefaults.emitterX,
      emitterY: advancedDefaults.emitterY,
      emitterZ: advancedDefaults.emitterZ,
      attractionX: advancedDefaults.attractionX,
      attractionY: advancedDefaults.attractionY,
      vortex: advancedDefaults.vortex,
      follow: advancedDefaults.follow,
      followAnchor: "torso",
      comboPreset: "none",
      customComboLayers: [],
      layerCount: 1,
      sizeCurve: advancedDefaults.sizeCurve,
      opacityCurve: advancedDefaults.opacityCurve,
      colorCurve: getParticleDefaultColorCurve(safePreset),
      forceField: advancedDefaults.forceField,
      fieldX: advancedDefaults.fieldX,
      fieldY: advancedDefaults.fieldY,
      density: defaults.density,
      sizeMin: defaults.sizeMin,
      sizeMax: defaults.sizeMax,
      lifeMin: defaults.lifeMin,
      lifeMax: defaults.lifeMax,
      gravityX: defaults.gravityX,
      gravityY: defaults.gravityY,
      gravityZ: defaults.gravityZ,
      spreadX: defaults.spreadX,
      spreadY: defaults.spreadY,
      spreadZ: defaults.spreadZ,
      opacityMin: defaults.opacityMin,
      opacityMax: defaults.opacityMax,
      rotationMin: defaults.rotationMin,
      rotationMax: defaults.rotationMax,
      spin: defaults.spin,
      turbulence: defaults.turbulence,
      color: defaults.color,
      colorAccent: defaults.colorAccent,
      colorEnd: defaults.colorAccent,
      blend: defaults.blend,
    };
  }

  function getParticleSpeedMultiplier(speed) {
    return {
      slow: 1.28,
      medium: 1,
      fast: 0.78,
    }[getSafeParticleSpeed(speed)];
  }

  function getParticleWindBias(wind, preset) {
    const base = {
      left: -26,
      still: 0,
      right: 26,
    }[getSafeParticleWind(wind)];

    if (preset === "rain") {
      return base * 0.85;
    }

    if (preset === "dust" || preset === "bubbles") {
      return base * 0.5;
    }

    return base;
  }

  function getParticleAreaLayout(area, spreadX = 100) {
    const base = {
      full: { start: 0, width: 100 },
      left: { start: 0, width: 54 },
      center: { start: 23, width: 54 },
      right: { start: 46, width: 54 },
    }[getSafeParticleArea(area)];
    const normalizedWidth = Math.max(8, base.width * (clamp(spreadX, 4, 100) / 100));
    return {
      start: base.start + (base.width - normalizedWidth) * 0.5,
      width: normalizedWidth,
    };
  }

  function getParticlePresetDensityMultiplier(preset) {
    return {
      snow: 1,
      rain: 1.15,
      petals: 0.72,
      dust: 0.56,
      embers: 0.58,
      sparkles: 0.42,
      bubbles: 0.45,
      confetti: 0.8,
    }[getSafeParticlePreset(preset)];
  }

  function getParticleMotionProfile(preset) {
    return {
      snow: { startBase: -18, endBase: 126, aspect: "round" },
      rain: { startBase: -20, endBase: 136, aspect: "rain" },
      petals: { startBase: -14, endBase: 126, aspect: "petal" },
      dust: { startBase: -8, endBase: 112, aspect: "dust" },
      embers: { startBase: 108, endBase: -18, aspect: "ember" },
      sparkles: { startBase: -6, endBase: 118, aspect: "sparkle" },
      bubbles: { startBase: 112, endBase: -22, aspect: "bubble" },
      confetti: { startBase: -12, endBase: 126, aspect: "confetti" },
    }[getSafeParticlePreset(preset)];
  }

  function getParticleRandom(index, salt = 1) {
    const value = Math.sin((index + 1) * 12.9898 + salt * 78.233) * 43758.5453123;
    return value - Math.floor(value);
  }

  function formatParticleNumber(value, fractionDigits = 0) {
    return Number(value).toFixed(fractionDigits).replace(/\.0+$/, "").replace(/(\.\d*[1-9])0+$/, "$1");
  }

  function renderParticleLabelOptions(labelMap, selectedValue, options = {}) {
    const escape = getEscapeHtml(options);
    return Object.entries(labelMap ?? {})
      .map(
        ([value, label]) => `
                  <option value="${escape(value)}" ${value === selectedValue ? "selected" : ""}>
                    ${escape(label)}
                  </option>
                `
      )
      .join("");
  }

  function renderParticleCustomLayerEditor(index, layer, options = {}) {
    const escape = getEscapeHtml(options);
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const slotNumber = safeIndex + 1;
    const normalizedLayer = normalizeParticleCustomComboLayer(layer, safeIndex === 0 ? "stardust" : "smoke");

    return `
    <article class="editor-card particle-custom-layer-card" data-particle-custom-layer data-layer-index="${safeIndex}">
      <div class="particle-custom-layer-head">
        <h3>自定义叠层 ${slotNumber}</h3>
        <button class="toolbar-button toolbar-button-danger" type="button" data-action="remove-particle-custom-layer" data-layer-index="${safeIndex}">
          删除这层
        </button>
      </div>
      <p>这一层是你额外加的附加发射器。它适合叠烟雾、星尘、法阵、火焰这种辅助层，不用再单独新开一张粒子卡片。</p>
      <div class="particle-custom-layer-grid">
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}Enabled">是否启用</label>
          <select id="editorParticleCustomLayer${slotNumber}Enabled">
            <option value="false" ${normalizedLayer.enabled ? "" : "selected"}>先关闭这层</option>
            <option value="true" ${normalizedLayer.enabled ? "selected" : ""}>启用这层附加粒子</option>
          </select>
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}Preset">叠层粒子类型</label>
          <select id="editorParticleCustomLayer${slotNumber}Preset">
            ${renderParticleLabelOptions(PARTICLE_PRESET_LABELS, normalizedLayer.preset, options)}
          </select>
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}EmissionMode">发射模式</label>
          <select id="editorParticleCustomLayer${slotNumber}EmissionMode">
            ${renderParticleLabelOptions(PARTICLE_EMISSION_MODE_LABELS, normalizedLayer.emissionMode, options)}
          </select>
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}Follow">跟随目标</label>
          <select id="editorParticleCustomLayer${slotNumber}Follow">
            ${renderParticleLabelOptions(PARTICLE_FOLLOW_LABELS, normalizedLayer.follow, options)}
          </select>
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}FollowAnchor">跟随锚点</label>
          <select id="editorParticleCustomLayer${slotNumber}FollowAnchor">
            ${renderParticleLabelOptions(PARTICLE_FOLLOW_ANCHOR_LABELS, normalizedLayer.followAnchor, options)}
          </select>
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}DensityMultiplier">数量倍率</label>
          <input id="editorParticleCustomLayer${slotNumber}DensityMultiplier" type="number" min="0.2" max="4" step="0.1" value="${escape(
            formatParticleNumber(normalizedLayer.densityMultiplier, 1)
          )}" />
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}SizeScale">尺寸倍率</label>
          <input id="editorParticleCustomLayer${slotNumber}SizeScale" type="number" min="0.2" max="4" step="0.1" value="${escape(
            formatParticleNumber(normalizedLayer.sizeScale, 1)
          )}" />
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}LifeScale">寿命倍率</label>
          <input id="editorParticleCustomLayer${slotNumber}LifeScale" type="number" min="0.2" max="4" step="0.1" value="${escape(
            formatParticleNumber(normalizedLayer.lifeScale, 1)
          )}" />
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}OpacityScale">透明度倍率</label>
          <input id="editorParticleCustomLayer${slotNumber}OpacityScale" type="number" min="0.1" max="2" step="0.1" value="${escape(
            formatParticleNumber(normalizedLayer.opacityScale, 1)
          )}" />
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}ColorMix">颜色混合（0~1）</label>
          <input id="editorParticleCustomLayer${slotNumber}ColorMix" type="number" min="0" max="1" step="0.05" value="${escape(
            formatParticleNumber(normalizedLayer.colorMix, 2)
          )}" />
        </div>
        <div class="detail-row">
          <label for="editorParticleCustomLayer${slotNumber}Blend">混合模式</label>
          <select id="editorParticleCustomLayer${slotNumber}Blend">
            ${renderParticleLabelOptions(PARTICLE_BLEND_LABELS, normalizedLayer.blend, options)}
          </select>
        </div>
      </div>
    </article>
  `;
  }

  function getParticleAnchorPercent(position) {
    return {
      left: 24,
      center: 50,
      right: 76,
    }[position] ?? 50;
  }

  function getParticleCameraAnchorPercent(stageContext = null) {
    const focus =
      stageContext?.cameraPan?.target && stageContext.cameraPan.target !== "center"
        ? stageContext.cameraPan.target
        : stageContext?.cameraZoom?.focus ?? "center";
    return getParticleAnchorPercent(focus);
  }

  function getParticleEmitterAnchor(config = {}, stageContext = null) {
    const sourceConfig = config && typeof config === "object" ? config : {};
    const defaults = buildDefaultParticleEffectConfig(sourceConfig.preset);
    const baseConfig = {
      ...defaults,
      ...sourceConfig,
      area: getSafeParticleArea(sourceConfig.area),
      follow: getSafeParticleFollowTarget(sourceConfig.follow),
      followAnchor: getSafeParticleFollowAnchor(sourceConfig.followAnchor),
      emitterX: clamp(getSafeNumber(sourceConfig.emitterX, defaults.emitterX), 0, 100),
      emitterY: clamp(getSafeNumber(sourceConfig.emitterY, defaults.emitterY), -20, 120),
      emitterZ: clamp(getSafeNumber(sourceConfig.emitterZ, defaults.emitterZ), -100, 100),
    };
    const areaLayout = getParticleAreaLayout(baseConfig.area, 100);
    let anchorX = baseConfig.emitterX;
    let anchorY = baseConfig.emitterY;
    let anchorZ = baseConfig.emitterZ;

    if (baseConfig.follow === "character" && stageContext?.activeCharacterId) {
      const activeCharacter = (stageContext.visibleCharacters ?? []).find(
        (item) => item.characterId === stageContext.activeCharacterId
      );
      if (activeCharacter) {
        anchorX = getParticleAnchorPercent(activeCharacter.position);
        anchorY = baseConfig.followAnchor === "head" ? 34 : baseConfig.followAnchor === "feet" ? 82 : 56;
        anchorZ += 8;
      }
    } else if (baseConfig.follow === "camera") {
      anchorX = getParticleCameraAnchorPercent(stageContext);
      anchorY = baseConfig.followAnchor === "head" ? 30 : baseConfig.followAnchor === "feet" ? 72 : 48;
    }

    return {
      x: clamp(anchorX, areaLayout.start, areaLayout.start + areaLayout.width),
      y: clamp(anchorY, -20, 120),
      z: clamp(anchorZ, -100, 100),
    };
  }

  function getParticleCurveProfile(config = {}) {
    return {
      size: PARTICLE_SIZE_CURVE_PROFILES[getSafeParticleSizeCurve(config?.sizeCurve)],
      opacity: PARTICLE_OPACITY_CURVE_PROFILES[getSafeParticleOpacityCurve(config?.opacityCurve)],
      force: PARTICLE_FORCE_FIELD_PROFILES[getSafeParticleForceField(config?.forceField)],
    };
  }

  function getParticleColorCurveProfile(config = {}) {
    return PARTICLE_COLOR_CURVE_PROFILES[getSafeParticleColorCurve(config?.colorCurve)];
  }

  function buildParticleLayerVariants(config = {}) {
    const sourceConfig = config && typeof config === "object" ? config : {};
    const defaults = buildDefaultParticleEffectConfig(sourceConfig.preset);
    const color = getSafeParticleColor(sourceConfig.color, defaults.color);
    const colorAccent = getSafeParticleColor(sourceConfig.colorAccent, defaults.colorAccent);
    const baseConfig = {
      ...defaults,
      ...sourceConfig,
      layerCount: getSafeParticleLayerCount(sourceConfig.layerCount),
      density: clamp(Math.round(getSafeNumber(sourceConfig.density, defaults.density)), 1, 400),
      sizeMin: clamp(getSafeNumber(sourceConfig.sizeMin, defaults.sizeMin), 1, 160),
      sizeMax: clamp(getSafeNumber(sourceConfig.sizeMax, defaults.sizeMax), 1, 160),
      opacityMin: clamp(getSafeNumber(sourceConfig.opacityMin, defaults.opacityMin), 0.04, 1),
      opacityMax: clamp(getSafeNumber(sourceConfig.opacityMax, defaults.opacityMax), 0.04, 1),
      spreadZ: clamp(getSafeNumber(sourceConfig.spreadZ, defaults.spreadZ), 0, 100),
      gravityZ: clamp(getSafeNumber(sourceConfig.gravityZ, defaults.gravityZ), -120, 120),
      emitterZ: clamp(getSafeNumber(sourceConfig.emitterZ, defaults.emitterZ), -100, 100),
      color,
      colorAccent,
      colorEnd: getSafeParticleColor(sourceConfig.colorEnd, colorAccent),
    };
    const layerCount = baseConfig.layerCount;
    return Array.from({ length: layerCount }, (_, layerIndex) => {
      const depthFactor = layerCount === 1 ? 0 : layerIndex / (layerCount - 1);
      const sizeFactor = layerCount === 1 ? 1 : 0.78 + depthFactor * 0.46;
      const opacityFactor = layerCount === 1 ? 1 : 0.72 + depthFactor * 0.32;
      const densityFactor = layerCount === 1 ? 1 : 0.74 + (1 - Math.abs(depthFactor - 0.5) * 2) * 0.42;
      return {
        ...baseConfig,
        density: Math.max(6, Math.round((baseConfig.density / layerCount) * densityFactor)),
        sizeMin: clamp(baseConfig.sizeMin * sizeFactor, 1, 160),
        sizeMax: clamp(baseConfig.sizeMax * sizeFactor, 1, 160),
        opacityMin: clamp(baseConfig.opacityMin * opacityFactor, 0.04, 1),
        opacityMax: clamp(baseConfig.opacityMax * opacityFactor, 0.04, 1),
        spreadZ: clamp(baseConfig.spreadZ + layerIndex * 12, 0, 100),
        gravityZ: clamp(baseConfig.gravityZ + (depthFactor - 0.5) * 24, -120, 120),
        emitterZ: clamp(baseConfig.emitterZ + (depthFactor - 0.5) * 22, -100, 100),
        color: mixParticleColors(baseConfig.color, baseConfig.colorAccent, depthFactor * 0.35),
        colorAccent: mixParticleColors(baseConfig.colorAccent, baseConfig.colorEnd, depthFactor * 0.35),
        colorEnd: mixParticleColors(baseConfig.colorEnd, baseConfig.color, depthFactor * 0.18),
        __layerIndex: layerIndex,
      };
    });
  }

  function getParticleComboConfigNormalizer(options = {}) {
    if (typeof options === "function") {
      return options;
    }
    if (typeof options?.normalizeConfig === "function") {
      return options.normalizeConfig;
    }
    return (config = {}) => ({
      ...buildDefaultParticleEffectConfig(config?.preset),
      ...(config && typeof config === "object" ? config : {}),
    });
  }

  function buildParticleComboVariants(config = {}, options = {}) {
    const normalizeConfig = getParticleComboConfigNormalizer(options);
    const baseConfig = normalizeConfig(config);
    const comboPreset = getSafeParticleComboPreset(baseConfig.comboPreset);
    const presetOverlays = getParticleComboPresetConfig(comboPreset);
    const customOverlays = getEnabledParticleCustomComboLayers(baseConfig.customComboLayers).map((layer) => ({
      preset: layer.preset,
      emissionMode: layer.emissionMode,
      follow: layer.follow,
      followAnchor: layer.followAnchor,
      densityMultiplier: layer.densityMultiplier,
      sizeScale: layer.sizeScale,
      lifeScale: layer.lifeScale,
      opacityScale: layer.opacityScale,
      colorMix: layer.colorMix,
      blend: layer.blend,
    }));
    const overlays = [...presetOverlays, ...customOverlays];

    if (!overlays.length) {
      return [{ ...baseConfig, __comboIndex: 0 }];
    }

    return [
      { ...baseConfig, __comboIndex: 0 },
      ...overlays.map((overlay, comboIndex) => {
        const overlayDefaults = normalizeConfig(buildDefaultParticleEffectConfig(overlay.preset));
        const colorMix = clamp(getSafeNumber(overlay.colorMix, 0.42), 0, 1);
        const follow = overlay.follow ?? overlayDefaults.follow;
        const followAnchor =
          overlay.followAnchor ?? (follow === "none" ? overlayDefaults.followAnchor : baseConfig.followAnchor);

        return normalizeConfig({
          ...overlayDefaults,
          action: "start",
          intensity: overlay.intensity ?? baseConfig.intensity,
          speed: overlay.speed ?? baseConfig.speed,
          wind: overlay.wind ?? baseConfig.wind,
          area: overlay.area ?? baseConfig.area,
          emissionMode: overlay.emissionMode ?? overlayDefaults.emissionMode,
          emitterShape: overlay.emitterShape ?? overlayDefaults.emitterShape,
          emitterX: (overlay.emitterX ?? baseConfig.emitterX) + getSafeNumber(overlay.emitterXOffset, 0),
          emitterY: (overlay.emitterY ?? baseConfig.emitterY) + getSafeNumber(overlay.emitterYOffset, 0),
          emitterZ: (overlay.emitterZ ?? baseConfig.emitterZ) + getSafeNumber(overlay.emitterZOffset, 0),
          attractionX: overlay.attractionX ?? overlayDefaults.attractionX,
          attractionY: overlay.attractionY ?? overlayDefaults.attractionY,
          vortex: overlay.vortex ?? overlayDefaults.vortex,
          follow,
          followAnchor,
          comboPreset: "none",
          layerCount: overlay.layerCount ?? overlayDefaults.layerCount,
          sizeCurve: overlay.sizeCurve ?? overlayDefaults.sizeCurve,
          opacityCurve: overlay.opacityCurve ?? overlayDefaults.opacityCurve,
          forceField: overlay.forceField ?? overlayDefaults.forceField,
          fieldX: (overlay.fieldX ?? baseConfig.fieldX) + getSafeNumber(overlay.fieldXOffset, 0),
          fieldY: (overlay.fieldY ?? baseConfig.fieldY) + getSafeNumber(overlay.fieldYOffset, 0),
          density: Math.round(overlayDefaults.density * getSafeNumber(overlay.densityMultiplier, 1)),
          sizeMin: overlayDefaults.sizeMin * getSafeNumber(overlay.sizeScale, 1),
          sizeMax: overlayDefaults.sizeMax * getSafeNumber(overlay.sizeScale, 1),
          lifeMin: overlayDefaults.lifeMin * getSafeNumber(overlay.lifeScale, 1),
          lifeMax: overlayDefaults.lifeMax * getSafeNumber(overlay.lifeScale, 1),
          gravityX: overlayDefaults.gravityX + getSafeNumber(overlay.gravityXAdd, 0),
          gravityY: overlayDefaults.gravityY + getSafeNumber(overlay.gravityYAdd, 0),
          gravityZ: overlayDefaults.gravityZ + getSafeNumber(overlay.gravityZAdd, 0),
          spreadX: overlayDefaults.spreadX * getSafeNumber(overlay.spreadXMultiplier, 1),
          spreadY: overlayDefaults.spreadY * getSafeNumber(overlay.spreadYMultiplier, 1),
          spreadZ: overlayDefaults.spreadZ + getSafeNumber(overlay.spreadZAdd, 0),
          opacityMin: overlayDefaults.opacityMin * getSafeNumber(overlay.opacityScale, 1),
          opacityMax: overlayDefaults.opacityMax * getSafeNumber(overlay.opacityScale, 1),
          rotationMin: overlayDefaults.rotationMin,
          rotationMax: overlayDefaults.rotationMax,
          spin: overlayDefaults.spin + getSafeNumber(overlay.spinAdd, 0),
          turbulence: overlayDefaults.turbulence + getSafeNumber(overlay.turbulenceAdd, 0),
          color: overlay.color ?? mixParticleColors(overlayDefaults.color, baseConfig.color, colorMix),
          colorAccent:
            overlay.colorAccent ??
            mixParticleColors(overlayDefaults.colorAccent, baseConfig.colorAccent, Math.min(colorMix + 0.08, 1)),
          colorEnd:
            overlay.colorEnd ??
            mixParticleColors(overlayDefaults.colorAccent, baseConfig.colorEnd, Math.min(colorMix + 0.04, 1)),
          blend: overlay.blend ?? overlayDefaults.blend,
          assetId: "",
          __comboIndex: comboIndex + 1,
        });
      }),
    ];
  }

  function getParticleImageDisplayName(config, options = {}) {
    if (typeof options?.getImageName === "function") {
      return options.getImageName(config.assetId);
    }
    return config.assetId || "使用默认外观";
  }

  function describeParticleEffect(particleEffect, options = {}) {
    if (!particleEffect) {
      return "已关闭";
    }
    const normalizeConfig = getParticleComboConfigNormalizer(options);
    const config = normalizeConfig(particleEffect);
    return `${getParticlePresetLabel(config.preset)} · ${getParticleEmissionModeLabel(
      config.emissionMode
    )} · ${getParticleEmitterShapeLabel(config.emitterShape)} · ${getParticleComboPresetLabel(
      config.comboPreset
    )} · ${getParticleCustomComboLayerSummary(config.customComboLayers)} · ${getParticleSizeCurveLabel(
      config.sizeCurve
    )} · ${getParticleColorCurveLabel(config.colorCurve)} · ${config.layerCount} 层 · ${config.density} 颗 · ${formatParticleNumber(
      config.sizeMin
    )}-${formatParticleNumber(config.sizeMax)} px · G ${formatParticleNumber(config.gravityX)}/${formatParticleNumber(
      config.gravityY
    )}/${formatParticleNumber(config.gravityZ)} · ${getParticleBlendModeLabel(config.blend)}${
      config.assetId ? ` · ${getParticleImageDisplayName(config, options)}` : ""
    }`;
  }

  function buildParticleEffectDetailRows(particleEffect, options = {}) {
    const action = getSafeParticleAction(particleEffect?.action);
    const rows = [["执行动作", getParticleActionLabel(action)]];
    if (action !== "start") {
      return rows;
    }

    const normalizeConfig = getParticleComboConfigNormalizer(options);
    const particle = normalizeConfig(particleEffect);
    rows.push(["粒子类型", getParticlePresetLabel(particle.preset)]);
    rows.push(["自定义图片", getParticleImageDisplayName(particle, options)]);
    rows.push(["特效强度", getParticleIntensityLabel(particle.intensity)]);
    rows.push(["速度 / 风向", `${getParticleSpeedLabel(particle.speed)} / ${getParticleWindLabel(particle.wind)}`]);
    rows.push(["出现区域", getParticleAreaLabel(particle.area)]);
    rows.push(["发射模式", getParticleEmissionModeLabel(particle.emissionMode)]);
    rows.push(["组合方案", getParticleComboPresetLabel(particle.comboPreset)]);
    rows.push(["自定义叠层", getParticleCustomComboLayerSummary(particle.customComboLayers)]);
    rows.push([
      "发射器",
      `${getParticleEmitterShapeLabel(particle.emitterShape)} / ${getParticleFollowTargetLabel(
        particle.follow
      )} / ${getParticleFollowAnchorLabel(particle.followAnchor)}`,
    ]);
    rows.push(["叠加层数", `${particle.layerCount} 层`]);
    rows.push([
      "时间曲线",
      `${getParticleSizeCurveLabel(particle.sizeCurve)} / ${getParticleOpacityCurveLabel(
        particle.opacityCurve
      )} / ${getParticleColorCurveLabel(particle.colorCurve)}`,
    ]);
    rows.push([
      "中心力场",
      `${getParticleForceFieldLabel(particle.forceField)} / 中心 ${formatParticleNumber(
        particle.fieldX
      )} / ${formatParticleNumber(particle.fieldY)}`,
    ]);
    rows.push([
      "发射器 XYZ",
      `${formatParticleNumber(particle.emitterX)} / ${formatParticleNumber(particle.emitterY)} / ${formatParticleNumber(
        particle.emitterZ
      )}`,
    ]);
    rows.push([
      "吸引 / 旋涡",
      `X ${formatParticleNumber(particle.attractionX)} / Y ${formatParticleNumber(
        particle.attractionY
      )} / 涡流 ${formatParticleNumber(particle.vortex)}`,
    ]);
    rows.push(["粒子数量", `${particle.density} 颗`]);
    rows.push(["尺寸范围", `${formatParticleNumber(particle.sizeMin)} ~ ${formatParticleNumber(particle.sizeMax)} px`]);
    rows.push(["寿命范围", `${formatParticleNumber(particle.lifeMin, 1)} ~ ${formatParticleNumber(particle.lifeMax, 1)} 秒`]);
    rows.push([
      "重力 XYZ",
      `${formatParticleNumber(particle.gravityX)} / ${formatParticleNumber(particle.gravityY)} / ${formatParticleNumber(
        particle.gravityZ
      )}`,
    ]);
    rows.push([
      "疏散 XYZ",
      `${formatParticleNumber(particle.spreadX)} / ${formatParticleNumber(particle.spreadY)} / ${formatParticleNumber(
        particle.spreadZ
      )}`,
    ]);
    rows.push([
      "透明度范围",
      `${formatParticleNumber(particle.opacityMin, 2)} ~ ${formatParticleNumber(particle.opacityMax, 2)}`,
    ]);
    rows.push([
      "旋转 / 扰动",
      `${formatParticleNumber(particle.rotationMin)} ~ ${formatParticleNumber(
        particle.rotationMax
      )} deg / 自转 ${formatParticleNumber(particle.spin)} deg / 乱流 ${formatParticleNumber(particle.turbulence)}`,
    ]);
    rows.push(["颜色", `${particle.color} → ${particle.colorAccent} → ${particle.colorEnd}`]);
    rows.push(["混合模式", getParticleBlendModeLabel(particle.blend)]);
    return rows;
  }

  function isValidParticleColor(color) {
    return /^#[0-9a-fA-F]{6}$/.test(String(color ?? "").trim());
  }

  function getSafeParticleColor(color, fallback = "#ffffff") {
    if (isValidParticleColor(color)) {
      return String(color).trim().toLowerCase();
    }
    return String(fallback).trim().toLowerCase();
  }

  function hexToRgb(color) {
    const safeColor = getSafeParticleColor(color, "#ffffff");
    return {
      red: Number.parseInt(safeColor.slice(1, 3), 16),
      green: Number.parseInt(safeColor.slice(3, 5), 16),
      blue: Number.parseInt(safeColor.slice(5, 7), 16),
    };
  }

  function mixParticleColors(colorA, colorB, ratio) {
    const first = hexToRgb(colorA);
    const second = hexToRgb(colorB);
    const safeRatio = getSafeNumber(ratio, 0);
    const mixChannel = (channel) =>
      clamp(Math.round(first[channel] + (second[channel] - first[channel]) * safeRatio), 0, 255)
        .toString(16)
        .padStart(2, "0");

    return `#${mixChannel("red")}${mixChannel("green")}${mixChannel("blue")}`;
  }

  function makeParticleCustomPresetId(name, existingIds = []) {
    const base =
      String(name ?? "")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "_")
        .replace(/^_+|_+$/g, "") || "particle_preset";
    let candidate = base;
    let suffix = 2;
    const used = new Set(existingIds);
    while (used.has(candidate)) {
      candidate = `${base}_${String(suffix).padStart(2, "0")}`;
      suffix += 1;
    }
    return candidate;
  }

  function getParticleCustomPresetPrimaryPreset(config) {
    return getSafeParticlePreset(config?.preset ?? "snow");
  }

  function getParticleCustomPresetSearchTokens(preset) {
    const config = preset?.config && typeof preset.config === "object" ? preset.config : {};
    return [
      preset?.name ?? "",
      preset?.id ?? "",
      getParticlePresetLabel(config.preset),
      getParticleComboPresetLabel(config.comboPreset),
      getParticleCustomComboLayerSummary(config.customComboLayers),
    ]
      .join(" ")
      .toLowerCase();
  }

  function getFilteredParticleCustomPresets(presets = [], query = "") {
    const source = Array.isArray(presets) ? presets : [];
    const normalizedQuery = String(query ?? "")
      .trim()
      .toLowerCase();
    if (!normalizedQuery) {
      return source;
    }
    return source.filter((preset) => getParticleCustomPresetSearchTokens(preset).includes(normalizedQuery));
  }

  function groupParticleCustomPresets(presets = []) {
    const groups = new Map();
    (Array.isArray(presets) ? presets : []).forEach((preset) => {
      const key = getParticleCustomPresetPrimaryPreset(preset?.config);
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key).push(preset);
    });
    return Array.from(groups.entries());
  }

  function renderParticleEditorSelectRow(id, label, labelMap, selectedValue, options = {}) {
    const escape = getEscapeHtml(options);
    return `
      <div class="detail-row">
        <label for="${escape(id)}">${escape(label)}</label>
        <select id="${escape(id)}">
          ${renderParticleLabelOptions(labelMap, selectedValue, options)}
        </select>
      </div>
    `;
  }

  function renderParticleEditorNumberRow(id, label, value, inputOptions = {}, options = {}) {
    const escape = getEscapeHtml(options);
    const {
      min = 0,
      max = 100,
      step = 1,
      fractionDigits = 0,
    } = inputOptions;
    return `
      <div class="detail-row">
        <label for="${escape(id)}">${escape(label)}</label>
        <input id="${escape(id)}" type="number" min="${escape(min)}" max="${escape(max)}" step="${escape(step)}" value="${escape(
          formatParticleNumber(value, fractionDigits)
        )}" />
      </div>
    `;
  }

  function renderParticleEditorColorRow(id, label, value, options = {}) {
    const escape = getEscapeHtml(options);
    return `
      <div class="detail-row">
        <label for="${escape(id)}">${escape(label)}</label>
        <input id="${escape(id)}" type="color" value="${escape(value)}" />
      </div>
    `;
  }

  function renderParticleImageAssetOptions(assets, selectedAssetId, options = {}) {
    const escape = getEscapeHtml(options);
    const getAssetTypeLabel =
      typeof options.getAssetTypeLabel === "function" ? options.getAssetTypeLabel : (type) => type ?? "";

    return (Array.isArray(assets) ? assets : [])
      .map(
        (asset) => `
        <option value="${escape(asset?.id ?? "")}" ${asset?.id === selectedAssetId ? "selected" : ""}>
          ${escape(asset?.name ?? "")} · ${escape(getAssetTypeLabel(asset?.type))}
        </option>
      `
      )
      .join("");
  }

  function renderParticleCustomPresetQuickList(presets = [], options = {}) {
    const escape = getEscapeHtml(options);
    const selectedPresetId = String(options.selectedPresetId ?? "");
    const normalizeConfig =
      typeof options.normalizeParticleEffectConfig === "function"
        ? options.normalizeParticleEffectConfig
        : buildDefaultParticleEffectConfig;
    const filteredPresets = Array.isArray(presets) ? presets : [];

    if (!filteredPresets.length) {
      return `<div class="helper-text">当前筛选下还没有命中的粒子预设。可换一个关键词，或先保存一组新的项目预设。</div>`;
    }

    return groupParticleCustomPresets(filteredPresets)
      .map(
        ([presetType, presetItems]) => `
        <section class="particle-preset-group">
          <div class="particle-preset-group-title">${escape(getParticlePresetLabel(presetType))}</div>
          <div class="particle-preset-chip-list">
            ${presetItems
              .map((preset) => {
                const config = normalizeConfig(preset?.config);
                return `
                  <button
                    class="particle-preset-chip ${preset?.id === selectedPresetId ? "is-active" : ""}"
                    type="button"
                    data-action="select-particle-custom-preset"
                    data-preset-id="${escape(preset?.id ?? "")}"
                  >
                    <strong>${escape(preset?.name ?? "")}</strong>
                    <span>${escape(
                      `${getParticleComboPresetLabel(config.comboPreset)} / ${getParticleCustomComboLayerSummary(
                        config.customComboLayers
                      )}`
                    )}</span>
                  </button>
                `;
              })
              .join("")}
          </div>
        </section>
      `
      )
      .join("");
  }

  function renderParticleEffectEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const normalizeConfig =
      typeof options.normalizeParticleEffectConfig === "function"
        ? options.normalizeParticleEffectConfig
        : (config = {}) => ({
            ...buildDefaultParticleEffectConfig(config?.preset),
            ...(config && typeof config === "object" ? config : {}),
          });
    const renderImageOptions =
      typeof options.renderParticleImageAssetOptions === "function"
        ? options.renderParticleImageAssetOptions
        : (selectedAssetId) => renderParticleImageAssetOptions(options.particleImageAssets, selectedAssetId, options);
    const renderCustomLayer =
      typeof options.renderParticleCustomLayerEditor === "function"
        ? options.renderParticleCustomLayerEditor
        : renderParticleCustomLayerEditor;
    const particle = normalizeConfig(block);
    const action = getSafeParticleAction(particle.action);
    const preset = getSafeParticlePreset(particle.preset);
    const intensity = getSafeParticleIntensity(particle.intensity);
    const speed = getSafeParticleSpeed(particle.speed);
    const wind = getSafeParticleWind(particle.wind);
    const area = getSafeParticleArea(particle.area);
    const assetId = String(particle.assetId ?? "");
    const customComboLayers = normalizeParticleCustomComboLayers(particle.customComboLayers);
    const savedParticlePresets = Array.isArray(options.savedParticlePresets) ? options.savedParticlePresets : [];
    const particlePresetSearchQuery = String(options.particlePresetSearchQuery ?? "");
    const selectedParticleCustomPresetId = String(options.selectedParticleCustomPresetId ?? "");
    const filteredParticleCustomPresets = getFilteredParticleCustomPresets(
      savedParticlePresets,
      particlePresetSearchQuery
    );
    const filteredParticleCustomPresetCount = Number.isFinite(Number(options.filteredParticleCustomPresetCount))
      ? Number(options.filteredParticleCustomPresetCount)
      : filteredParticleCustomPresets.length;
    const customPresetLimit = Number(options.customPresetLimit ?? PARTICLE_CUSTOM_PRESET_LIMIT);
    const quickListMarkup =
      typeof options.renderParticleCustomPresetQuickList === "function"
        ? options.renderParticleCustomPresetQuickList()
        : renderParticleCustomPresetQuickList(filteredParticleCustomPresets, {
            ...options,
            selectedPresetId: selectedParticleCustomPresetId,
            normalizeParticleEffectConfig: normalizeConfig,
          });

    return `
    <article class="editor-card">
      <h3>编辑粒子特效</h3>
      <p>这里已经升级成高级粒子模块了。除了雪、雨、樱花和光尘，现在还能做火星、闪光、气泡、纸片，并且把数量、尺寸、寿命、重力、XYZ 疏散、旋转、颜色、混合方式都像 AE 一样细调。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorParticleAction">这张卡片要做什么</label>
        <select id="editorParticleAction">
          <option value="start" ${action === "start" ? "selected" : ""}>开始粒子特效</option>
          <option value="stop" ${action === "stop" ? "selected" : ""}>关闭当前粒子特效</option>
        </select>
      </div>
      ${renderParticleEditorSelectRow("editorParticlePreset", "粒子类型", PARTICLE_PRESET_LABELS, preset, options)}
      <div class="detail-row">
        <label>快速套用</label>
        <button class="toolbar-button" data-action="apply-particle-preset-defaults">套用这个预设的高级参数</button>
      </div>
      <div class="detail-row">
        <label for="editorParticleScenePreset">演出级预设库</label>
        <select id="editorParticleScenePreset">
          ${Object.entries(PARTICLE_SCENE_PRESET_LABELS)
            .map(([value, label]) => `<option value="${escape(value)}">${escape(label)}</option>`)
            .join("")}
        </select>
      </div>
      <div class="detail-row">
        <label>一键生成完整效果</label>
        <button class="toolbar-button" data-action="apply-particle-scene-preset">套用这组演出级预设</button>
      </div>
      <article class="editor-card particle-preset-library-card">
        <h3>项目粒子预设库</h3>
        <p>把你调好的暴雪、火焰仪式、魔法阵、梦境星海存成这个项目自己的粒子预设，下次直接复用。当前已保存 ${savedParticlePresets.length} / ${customPresetLimit} 组。</p>
      </article>
      <div class="detail-row">
        <label for="editorParticleCustomPresetSearch">搜索项目预设</label>
        <input
          id="editorParticleCustomPresetSearch"
          type="text"
          placeholder="搜预设名、粒子类型、组合方案"
          value="${escape(particlePresetSearchQuery)}"
        />
      </div>
      <div class="detail-row">
        <label for="editorParticleCustomPresetSelect">已保存的粒子预设</label>
        <select id="editorParticleCustomPresetSelect">
          <option value="">先选一个项目预设</option>
          ${savedParticlePresets
            .map(
              (presetItem) => `
                <option value="${escape(presetItem?.id ?? "")}" ${
                  presetItem?.id === selectedParticleCustomPresetId ? "selected" : ""
                }>${escape(presetItem?.name ?? "")}</option>
              `
            )
            .join("")}
        </select>
      </div>
      <div class="detail-row">
        <label>快速调用</label>
        <div class="detail-actions">
          <button class="toolbar-button" type="button" data-action="apply-particle-custom-preset">套用这个项目预设</button>
          <button class="toolbar-button toolbar-button-danger" type="button" data-action="delete-particle-custom-preset" ${
            savedParticlePresets.length === 0 ? "disabled" : ""
          }>删除这个项目预设</button>
        </div>
      </div>
      <div class="detail-row">
        <label for="editorParticleCustomPresetName">保存为项目预设</label>
        <input
          id="editorParticleCustomPresetName"
          type="text"
          maxlength="36"
          placeholder="比如：暴雪神殿 / 紫焰法阵 / 星海梦境"
          value=""
        />
      </div>
      <div class="detail-row">
        <label>写进当前项目</label>
        <div class="detail-actions">
          <button class="toolbar-button" type="button" data-action="save-particle-custom-preset">保存这组粒子为项目预设</button>
          <button class="toolbar-button" type="button" data-action="export-particle-custom-preset" ${
            savedParticlePresets.length === 0 ? "disabled" : ""
          }>导出当前预设</button>
          <button class="toolbar-button" type="button" data-action="export-particle-custom-preset-pack" ${
            savedParticlePresets.length === 0 ? "disabled" : ""
          }>导出整个预设包</button>
          <button class="toolbar-button" type="button" data-action="import-particle-custom-preset-pack">导入预设包</button>
        </div>
      </div>
      <article class="editor-card particle-preset-quick-library">
        <h3>快速挑选</h3>
        <p class="helper-text">搜索结果 ${filteredParticleCustomPresetCount} 组；每个项目最多保存 ${customPresetLimit} 组粒子预设。</p>
        <div id="particleCustomPresetQuickList">${quickListMarkup}</div>
      </article>
      ${renderParticleEditorSelectRow("editorParticleIntensity", "特效强度", PARTICLE_INTENSITY_LABELS, intensity, options)}
      ${renderParticleEditorNumberRow("editorParticleDensity", "粒子数量", particle.density, { min: 4, max: 240 }, options)}
      <div class="detail-row">
        <label for="editorParticleAssetId">自定义粒子图片</label>
        <select id="editorParticleAssetId">
          <option value="">使用当前预设的默认外观</option>
          ${renderImageOptions(assetId)}
        </select>
      </div>
      ${renderParticleEditorSelectRow("editorParticleSpeed", "下落速度", PARTICLE_SPEED_LABELS, speed, options)}
      ${renderParticleEditorSelectRow("editorParticleWind", "风向", PARTICLE_WIND_LABELS, wind, options)}
      ${renderParticleEditorSelectRow("editorParticleArea", "出现区域", PARTICLE_AREA_LABELS, area, options)}
      ${renderParticleEditorSelectRow("editorParticleBlend", "混合模式", PARTICLE_BLEND_LABELS, particle.blend, options)}
      ${renderParticleEditorSelectRow("editorParticleEmissionMode", "发射模式", PARTICLE_EMISSION_MODE_LABELS, particle.emissionMode, options)}
      ${renderParticleEditorSelectRow("editorParticleComboPreset", "组合方案", PARTICLE_COMBO_PRESET_LABELS, particle.comboPreset, options)}
      <article class="editor-card particle-custom-layer-toolbar">
        <h3>自定义多层组合</h3>
        <p>如果现成的组合方案还不够，这里支持继续叠加更多发射器，并按需要新增或删除附加层。</p>
        <div class="detail-actions">
          <button class="toolbar-button" type="button" data-action="add-particle-custom-layer" ${
            customComboLayers.length >= PARTICLE_CUSTOM_COMBO_LAYER_LIMIT ? "disabled" : ""
          }>
            新增一层附加粒子
          </button>
        </div>
      </article>
      ${
        customComboLayers.length > 0
          ? customComboLayers.map((layer, index) => renderCustomLayer(index, layer)).join("")
          : `<article class="editor-card particle-custom-layer-empty"><p>当前还没有额外叠层。可使用上面的按钮继续叠加烟雾、星尘、法阵、火焰等辅助层。</p></article>`
      }
      <article class="editor-card">
        <h3>发射器和外力</h3>
        <p>这一组更像 AE 里的发射器：可以决定它是持续下雪、一次性爆发纸片，还是从某个点、某条线、某个圆形区域喷出来；现在还可以一键套“组合方案”，把烟雾、法阵、星尘、火焰这些多层发射器叠在同一张卡里。</p>
      </article>
      ${renderParticleEditorSelectRow("editorParticleEmitterShape", "发射器形状", PARTICLE_EMITTER_SHAPE_LABELS, particle.emitterShape, options)}
      ${renderParticleEditorSelectRow("editorParticleFollow", "跟随目标", PARTICLE_FOLLOW_LABELS, particle.follow, options)}
      ${renderParticleEditorSelectRow("editorParticleFollowAnchor", "跟随锚点", PARTICLE_FOLLOW_ANCHOR_LABELS, particle.followAnchor, options)}
      ${renderParticleEditorNumberRow("editorParticleLayerCount", "叠加层数", particle.layerCount, { min: 1, max: 3 }, options)}
      ${renderParticleEditorNumberRow("editorParticleEmitterX", "发射器 X（%）", particle.emitterX, { min: 0, max: 100 }, options)}
      ${renderParticleEditorNumberRow("editorParticleEmitterY", "发射器 Y（%）", particle.emitterY, { min: -20, max: 120 }, options)}
      ${renderParticleEditorNumberRow("editorParticleEmitterZ", "发射器 Z", particle.emitterZ, { min: -100, max: 100 }, options)}
      ${renderParticleEditorNumberRow("editorParticleAttractionX", "吸引 / 推离 X", particle.attractionX, { min: -160, max: 160 }, options)}
      ${renderParticleEditorNumberRow("editorParticleAttractionY", "吸引 / 推离 Y", particle.attractionY, { min: -160, max: 160 }, options)}
      ${renderParticleEditorNumberRow("editorParticleVortex", "旋涡 / 绕圈", particle.vortex, { min: -240, max: 240 }, options)}
      ${renderParticleEditorSelectRow("editorParticleForceField", "中心力场", PARTICLE_FORCE_FIELD_LABELS, particle.forceField, options)}
      ${renderParticleEditorNumberRow("editorParticleFieldX", "力场中心 X（%）", particle.fieldX, { min: 0, max: 100 }, options)}
      ${renderParticleEditorNumberRow("editorParticleFieldY", "力场中心 Y（%）", particle.fieldY, { min: -20, max: 120 }, options)}
      <article class="editor-card">
        <h3>外观和寿命</h3>
        <p>这里决定粒子看起来有多大、活多久、透明度范围是多少。做大雪、细雨、轻尘和烟花碎片时会特别好用。</p>
      </article>
      ${renderParticleEditorNumberRow("editorParticleSizeMin", "最小尺寸（px）", particle.sizeMin, { min: 1, max: 160 }, options)}
      ${renderParticleEditorNumberRow("editorParticleSizeMax", "最大尺寸（px）", particle.sizeMax, { min: 1, max: 160 }, options)}
      ${renderParticleEditorNumberRow("editorParticleLifeMin", "最短寿命（秒）", particle.lifeMin, { min: 0.4, max: 20, step: 0.1, fractionDigits: 1 }, options)}
      ${renderParticleEditorNumberRow("editorParticleLifeMax", "最长寿命（秒）", particle.lifeMax, { min: 0.4, max: 20, step: 0.1, fractionDigits: 1 }, options)}
      ${renderParticleEditorNumberRow("editorParticleOpacityMin", "最小透明度（0~1）", particle.opacityMin, { min: 0.04, max: 1, step: 0.01, fractionDigits: 2 }, options)}
      ${renderParticleEditorNumberRow("editorParticleOpacityMax", "最大透明度（0~1）", particle.opacityMax, { min: 0.04, max: 1, step: 0.01, fractionDigits: 2 }, options)}
      ${renderParticleEditorSelectRow("editorParticleSizeCurve", "尺寸时间曲线", PARTICLE_SIZE_CURVE_LABELS, particle.sizeCurve, options)}
      ${renderParticleEditorSelectRow("editorParticleOpacityCurve", "透明度时间曲线", PARTICLE_OPACITY_CURVE_LABELS, particle.opacityCurve, options)}
      ${renderParticleEditorSelectRow("editorParticleColorCurve", "颜色时间曲线", PARTICLE_COLOR_CURVE_LABELS, particle.colorCurve, options)}
      <article class="editor-card">
        <h3>XYZ 运动和疏散</h3>
        <p>X / Y / Z 三个轴都可调。可将它理解为：X 是横向力，Y 是上下重力，Z 是远近层次；疏散越高，粒子越不整齐、越有空间感。</p>
      </article>
      ${renderParticleEditorNumberRow("editorParticleGravityX", "重力 X", particle.gravityX, { min: -180, max: 180 }, options)}
      ${renderParticleEditorNumberRow("editorParticleGravityY", "重力 Y", particle.gravityY, { min: -160, max: 280 }, options)}
      ${renderParticleEditorNumberRow("editorParticleGravityZ", "重力 Z", particle.gravityZ, { min: -120, max: 120 }, options)}
      ${renderParticleEditorNumberRow("editorParticleSpreadX", "疏散 X（%）", particle.spreadX, { min: 4, max: 100 }, options)}
      ${renderParticleEditorNumberRow("editorParticleSpreadY", "疏散 Y（%）", particle.spreadY, { min: 0, max: 100 }, options)}
      ${renderParticleEditorNumberRow("editorParticleSpreadZ", "疏散 Z（%）", particle.spreadZ, { min: 0, max: 100 }, options)}
      ${renderParticleEditorNumberRow("editorParticleTurbulence", "乱流 / 扰动", particle.turbulence, { min: 0, max: 120 }, options)}
      <article class="editor-card">
        <h3>旋转和颜色</h3>
        <p>这里可以把粒子调成慢慢转、快速打转、偏冷、偏暖或者高亮发光。如果上传的是自定义雪花图片，这里的颜色会直接当作着色涂层来用。</p>
      </article>
      ${renderParticleEditorNumberRow("editorParticleRotationMin", "初始旋转最小值（deg）", particle.rotationMin, { min: -360, max: 360 }, options)}
      ${renderParticleEditorNumberRow("editorParticleRotationMax", "初始旋转最大值（deg）", particle.rotationMax, { min: -360, max: 360 }, options)}
      ${renderParticleEditorNumberRow("editorParticleSpin", "自转速度 / 累积旋转（deg）", particle.spin, { min: -1080, max: 1080 }, options)}
      ${renderParticleEditorColorRow("editorParticleColor", "主颜色", particle.color, options)}
      ${renderParticleEditorColorRow("editorParticleColorAccent", "高光 / 辅助颜色", particle.colorAccent, options)}
      ${renderParticleEditorColorRow("editorParticleColorEnd", "结尾颜色", particle.colorEnd, options)}
      <div class="helper-text">如果选择“关闭当前粒子特效”，下面这些高级设置会被忽略；如果选择“开始”，它会一直持续到遇到下一张关闭卡片为止。现在这套参数已经足够做大雪、暴雨、漂浮火星、梦境闪光、冒泡、庆祝纸片这些高级演出了。</div>
    </div>
    <div class="detail-actions">
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function getParticleCustomPresetById(presets = [], presetId = "") {
    const safePresetId = String(presetId ?? "").trim();
    if (!safePresetId || !Array.isArray(presets)) {
      return null;
    }
    return presets.find((preset) => preset?.id === safePresetId) ?? null;
  }

  function buildParticleCustomPresetSavePlan({
    name = "",
    currentConfig = {},
    currentPresets = [],
    selectedPresetId = "",
    limit = PARTICLE_CUSTOM_PRESET_LIMIT,
  } = {}) {
    const presets = Array.isArray(currentPresets) ? currentPresets : [];
    const safeName = String(name ?? "").trim();
    if (!safeName) {
      return { ok: false, reason: "missing_name" };
    }

    const existingPreset = getParticleCustomPresetById(presets, selectedPresetId);
    if (!existingPreset && presets.length >= limit) {
      return { ok: false, reason: "limit_reached", limit };
    }

    const targetId =
      existingPreset?.id ??
      makeParticleCustomPresetId(
        safeName,
        presets.map((preset) => preset.id)
      );
    const nextPreset = { id: targetId, name: safeName, config: currentConfig };
    const nextPresets = existingPreset
      ? presets.map((preset) => (preset.id === existingPreset.id ? nextPreset : preset))
      : [...presets, nextPreset];

    return {
      ok: true,
      isUpdate: Boolean(existingPreset),
      targetId,
      name: safeName,
      preset: nextPreset,
      nextPresets,
    };
  }

  function buildParticleCustomPresetExportPayload(preset, exportedAt = new Date().toISOString()) {
    return {
      engine: "Canvasia Engine",
      kind: "particle_preset",
      exportedAt,
      preset,
    };
  }

  function buildParticleCustomPresetPackExportPayload(
    presets = [],
    projectTitle = "Canvasia Project",
    exportedAt = new Date().toISOString()
  ) {
    return {
      engine: "Canvasia Engine",
      kind: "particle_preset_pack",
      projectTitle,
      exportedAt,
      presets: Array.isArray(presets) ? presets : [],
    };
  }

  function extractParticleCustomPresetsFromImportPayload(parsed) {
    if (Array.isArray(parsed)) {
      return parsed;
    }
    if (Array.isArray(parsed?.presets)) {
      return parsed.presets;
    }
    if (parsed?.preset) {
      return [parsed.preset];
    }
    return [];
  }

  function buildParticleCustomPresetImportPlan(parsed, existingPresets = [], options = {}) {
    const rawPresets = extractParticleCustomPresetsFromImportPayload(parsed);
    if (!rawPresets.length) {
      throw new Error("这个文件里没有找到可导入的粒子预设。");
    }

    const limit = Number.isFinite(Number(options?.limit))
      ? Math.max(0, Math.round(Number(options.limit)))
      : PARTICLE_CUSTOM_PRESET_LIMIT;
    const presets = Array.isArray(existingPresets) ? existingPresets : [];
    const remainingSlots = Math.max(0, limit - presets.length);
    if (!remainingSlots) {
      throw new Error(`这个项目的粒子预设库已经达到上限 ${limit} 组，请先删掉一些旧预设再导入。`);
    }

    const normalizeConfig = getParticleComboConfigNormalizer(options);
    const importablePresets = rawPresets.slice(0, remainingSlots);
    const skippedCount = Math.max(0, rawPresets.length - importablePresets.length);
    const mergedPresets = [...presets];
    const usedIds = mergedPresets.map((preset) => preset.id);

    importablePresets.forEach((rawPreset, index) => {
      const fallbackName = `导入预设 ${index + 1}`;
      const name = String(rawPreset?.name ?? fallbackName).trim() || fallbackName;
      const config = normalizeConfig(rawPreset?.config ?? rawPreset);
      const nextId = makeParticleCustomPresetId(rawPreset?.id ?? name, usedIds);
      usedIds.push(nextId);
      mergedPresets.push({
        id: nextId,
        name,
        config,
      });
    });

    const importedCount = importablePresets.length;
    return {
      rawCount: rawPresets.length,
      importedCount,
      skippedCount,
      mergedPresets,
      selectedPresetId: mergedPresets[mergedPresets.length - 1]?.id ?? "",
      summary:
        skippedCount > 0
          ? `已导入粒子预设：新增 ${importedCount} 组，另有 ${skippedCount} 组因为项目上限被跳过`
          : `已导入粒子预设：新增 ${importedCount} 组`,
    };
  }

  window.CanvasiaEditorParticleEffects = Object.freeze({
    PARTICLE_PRESET_LABELS,
    PARTICLE_INTENSITY_LABELS,
    PARTICLE_SPEED_LABELS,
    PARTICLE_WIND_LABELS,
    PARTICLE_AREA_LABELS,
    PARTICLE_BLEND_LABELS,
    PARTICLE_EMISSION_MODE_LABELS,
    PARTICLE_EMITTER_SHAPE_LABELS,
    PARTICLE_FOLLOW_LABELS,
    PARTICLE_FOLLOW_ANCHOR_LABELS,
    PARTICLE_SIZE_CURVE_LABELS,
    PARTICLE_OPACITY_CURVE_LABELS,
    PARTICLE_COLOR_CURVE_LABELS,
    PARTICLE_FORCE_FIELD_LABELS,
    PARTICLE_COMBO_PRESET_LABELS,
    PARTICLE_SCENE_PRESET_LABELS,
    PARTICLE_PRESET_DEFAULTS,
    PARTICLE_PRESET_ADVANCED_DEFAULTS,
    PARTICLE_SCENE_PRESET_CONFIGS,
    PARTICLE_COMBO_PRESET_CONFIGS,
    PARTICLE_CUSTOM_COMBO_LAYER_LIMIT,
    PARTICLE_CUSTOM_PRESET_LIMIT,
    PARTICLE_IMAGE_ASSET_TYPES,
    getSafeParticleAction,
    getParticleActionLabel,
    getSafeParticlePreset,
    getParticlePresetLabel,
    getParticlePresetDefaults,
    getParticleAdvancedDefaults,
    getSafeParticleIntensity,
    getParticleIntensityLabel,
    getSafeParticleSpeed,
    getParticleSpeedLabel,
    getSafeParticleWind,
    getParticleWindLabel,
    getSafeParticleArea,
    getParticleAreaLabel,
    getSafeParticleBlendMode,
    getParticleBlendModeLabel,
    getParticleBlendCssValue,
    getSafeParticleEmissionMode,
    getParticleEmissionModeLabel,
    getSafeParticleEmitterShape,
    getParticleEmitterShapeLabel,
    getSafeParticleFollowTarget,
    getParticleFollowTargetLabel,
    getSafeParticleFollowAnchor,
    getParticleFollowAnchorLabel,
    getSafeParticleSizeCurve,
    getParticleSizeCurveLabel,
    getSafeParticleOpacityCurve,
    getParticleOpacityCurveLabel,
    getSafeParticleColorCurve,
    getParticleColorCurveLabel,
    getSafeParticleForceField,
    getParticleForceFieldLabel,
    getSafeParticleComboPreset,
    getParticleComboPresetLabel,
    getParticleScenePresetConfig,
    getParticleComboPresetConfig,
    buildDefaultParticleCustomComboLayer,
    normalizeParticleCustomComboLayer,
    normalizeParticleCustomComboLayers,
    getEnabledParticleCustomComboLayers,
    getParticleCustomComboLayerSummary,
    getParticleDefaultColorCurve,
    getSafeParticleLayerCount,
    getSafeParticleClampedNumber,
    buildDefaultParticleEffectConfig,
    getParticleSpeedMultiplier,
    getParticleWindBias,
    getParticleAreaLayout,
    getParticlePresetDensityMultiplier,
    getParticleMotionProfile,
    getParticleRandom,
    formatParticleNumber,
    renderParticleCustomLayerEditor,
    getParticleAnchorPercent,
    getParticleCameraAnchorPercent,
    getParticleEmitterAnchor,
    getParticleCurveProfile,
    getParticleColorCurveProfile,
    buildParticleLayerVariants,
    buildParticleComboVariants,
    describeParticleEffect,
    buildParticleEffectDetailRows,
    isValidParticleColor,
    getSafeParticleColor,
    mixParticleColors,
    makeParticleCustomPresetId,
    getParticleCustomPresetPrimaryPreset,
    getParticleCustomPresetSearchTokens,
    getFilteredParticleCustomPresets,
    groupParticleCustomPresets,
    renderParticleCustomPresetQuickList,
    renderParticleEffectEditor,
    renderParticleImageAssetOptions,
    getParticleCustomPresetById,
    buildParticleCustomPresetSavePlan,
    buildParticleCustomPresetExportPayload,
    buildParticleCustomPresetPackExportPayload,
    extractParticleCustomPresetsFromImportPayload,
    buildParticleCustomPresetImportPlan,
  });
})();
