
const SVG_NS = "http://www.w3.org/2000/svg";

const ALGORITHMS = ["bfs", "dfs", "ids", "ucs", "greedy", "astar", "hill", "sa"];
const ALGO_LABELS = {
  hill: "Hill Climbing",
  bfs: "BFS",
  dfs: "DFS",
  ids: "IDS",
  ucs: "UCS",
  greedy: "Greedy",
  astar: "A*",
  sa: "Simulated Annealing"
};

const REQUIRED_PURPLE_NODES = ["DUN02", "HGL02", "FB04"];

let MAP_W = 1448;
let MAP_H = 1086;

let state = {
  graph: null,
  algo: "astar",
  last: null,
  viewBox: { x: 0, y: 0, w: MAP_W, h: MAP_H },
  dragging: false,
  dragStart: null,
  vbStart: null,
  moved: false,
  playerNode: "S",
  animatingPlayer: false,
  routeLocked: false,
  routeCompleted: false,
  goalCollected: false,
  footstepCount: 0,
  collectedPurple: new Set(),
  dungeon: {
    sessionId: null,
    observation: null,
    result: null,
    stepIndex: 0,
    animating: false,
    triggeredFromMain: false,
    pendingResume: null,
    pauseReason: null
  },
  dun02Dungeon: {
    sessionId: null,
    map: null,
    result: null,
    animating: false,
    triggeredFromMain: false
  },
  fb04Dungeon: {
    sessionId: null,
    map: null,
    customMap: null,
    selectedNodes: [],
    result: null,
    triggeredFromMain: false,
    pendingResume: null,
    pauseReason: null
  },
  andor: {
    triggeredFromMain: false,
    result: null
  }};

const $ = (id) => document.getElementById(id);

function svgEl(tag, attrs = {}, text = null) {
  const el = document.createElementNS(SVG_NS, tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (v !== null && v !== undefined) el.setAttribute(k, String(v));
  });
  if (text !== null) el.textContent = text;
  return el;
}

async function init() {
  buildAlgoButtons();
  await loadGraph();
  bindEvents();
  applyViewBox();
}

async function loadGraph() {
  const res = await fetch("/api/graph");
  state.graph = await res.json();

  MAP_W = state.graph.map.width;
  MAP_H = state.graph.map.height;
  state.viewBox = { x: 0, y: 0, w: MAP_W, h: MAP_H };

  drawGraph();
  drawMarkers();

  const nodeCount = Object.values(state.graph.nodes || {}).filter(hasXY).length;
  const edgeCount = (state.graph.edges || []).length;
  $("mapTitle").textContent = "Đã tải graph: " + nodeCount + " node / " + edgeCount + " cạnh";
  $("mapSubtitle").textContent = "Nếu không thấy node, hãy bấm Ctrl+F5 hoặc chạy đúng server ở http://127.0.0.1:8010";

  if (hasXY(node("S"))) {
    drawPlayer(node("S").x, node("S").y, "down", 0);
  }
}

function node(id) {
  return state.graph.nodes[id];
}

function hasXY(n) {
  return n && n.x !== null && n.y !== null && n.x !== undefined && n.y !== undefined;
}

function edgePoints(edge) {
  if (edge.shape_points && edge.shape_points.length) return edge.shape_points;
  return [node(edge.from), node(edge.to)];
}

function buildAlgoButtons() {
  const box = $("algorithmButtons");
  box.innerHTML = "";
  ALGORITHMS.forEach(algo => {
    const btn = document.createElement("button");
    btn.className = "algo-btn" + (algo === state.algo ? " active" : "");
    btn.textContent = ALGO_LABELS[algo];
    btn.dataset.algo = algo;
    btn.addEventListener("click", () => setAlgo(algo));
    box.appendChild(btn);
  });
}

function setAlgo(algo) {
  state.algo = algo;
  document.querySelectorAll(".algo-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.algo === algo);
  });
}

function drawGraph() {
  if (!state.graph) return;

  const svg = $("gameSvg");
  svg.classList.toggle("show-edges", $("showEdges")?.checked || false);
  svg.classList.toggle("show-labels", $("showLabels")?.checked || false);

  const edgeLayer = $("edgeLayer");
  const nodeLayer = $("nodeLayer");
  edgeLayer.innerHTML = "";
  nodeLayer.innerHTML = "";

  state.graph.edges.forEach(edge => {
    const pts = edgePoints(edge);
    const poly = pts.map(p => `${p.x},${p.y}`).join(" ");
    edgeLayer.appendChild(svgEl("polyline", {
      class: `graph-edge ${edge.violates_no_go ? "danger-edge" : ""}`,
      points: poly
    }));
  });

  Object.entries(state.graph.nodes).forEach(([id, n]) => {
    if (!hasXY(n)) return;
    const g = svgEl("g", { class: "node-item", "data-node": id });
    const r = n.kind === "start" || n.kind === "goal" ? 12 : 7;
    const nodeClasses = ["node-circle"];
    if (n.kind) nodeClasses.push(n.kind);
    if (requiredPurpleNodes().includes(id)) nodeClasses.push("dungeon");
    if (n.kind === "goal_gate" || ["GATE_MID", "B09", "G04"].includes(id)) nodeClasses.push("goal-gate");
    g.appendChild(svgEl("circle", {
      class: nodeClasses.join(" "),
      cx: n.x,
      cy: n.y,
      r
    }));
    g.appendChild(svgEl("text", {
      class: "node-label",
      x: n.x + 8,
      y: n.y - 8
    }, id));
    g.appendChild(svgEl("title", {}, `${id}: ${n.name}`));
    g.addEventListener("click", () => {
      if (id === "DUN02") {
        triggerDun02DungeonFromMainRoute().catch(err => alert(err.message));
      }
      if (id === "HGL02") {
        triggerDungeonFromMainRoute().catch(err => alert(err.message));
      }
      if (id === "FB04") {
        triggerFb04DungeonFromMainRoute().catch(err => alert(err.message));
      }

      // Test nhanh Boss cuối: click trực tiếp vào GOAL/kho báu để mở Boss.
      if (id === "GOAL" || id === "TREASURE") {
        state.bossFinalTriggered = true;
        triggerBossFinalFromTreasure().catch(err => alert(err.message));
      }
    });
    nodeLayer.appendChild(g);
  });
}

function buildTreasureChest(x, y) {
  const g = svgEl("g", { class: "treasure-chest", transform: `translate(${x - 18}, ${y - 22})` });
  const px = [];
  const add = (fill, x, y, w = 1, h = 1) => px.push([fill, x, y, w, h]);

  add("#3b2412", 4, 15, 28, 12);
  add("#7b4315", 6, 17, 24, 8);
  add("#c07a2e", 4, 12, 28, 6);
  add("#f6d36e", 6, 14, 24, 2);
  add("#f7e8a6", 15, 11, 6, 3);
  add("#5a2b09", 16, 18, 4, 9);
  add("#d9a73c", 13, 19, 10, 4);
  add("#f9f2c0", 15, 19, 6, 2);
  add("#2d1608", 4, 27, 28, 2);
  add("#ffd86a", 3, 9, 30, 2);
  px.forEach(([fill, pxX, pxY, w, h]) => g.appendChild(svgEl("rect", { fill, x: pxX, y: pxY, width: w, height: h })));
  return g;
}

function drawMarkers() {
  const layer = $("markerLayer");
  layer.innerHTML = "";
  if (!state.graph) return;

  const start = node("S");
  const goal = node("GOAL");

  if (!hasXY(start) || !hasXY(goal)) return;

  const sg = svgEl("g", { class: "start-marker", id: "startMarker" });
  sg.appendChild(svgEl("rect", {
    class: "start-banner",
    x: start.x - 38, y: start.y + 22, width: 76, height: 28, rx: 7
  }));
  sg.appendChild(svgEl("text", { x: start.x, y: start.y + 42 }, "START"));
  layer.appendChild(sg);

  const gg = svgEl("g", { class: "goal-marker", id: "goalMarker" });
  gg.appendChild(svgEl("circle", { class: "goal-aura", cx: goal.x, cy: goal.y - 8, r: 24 }));
  gg.appendChild(svgEl("circle", { class: "goal-aura soft", cx: goal.x, cy: goal.y - 8, r: 38 }));
  gg.appendChild(buildTreasureChest(goal.x, goal.y - 18));
  gg.appendChild(svgEl("rect", {
    class: "goal-banner",
    x: goal.x - 35, y: goal.y - 68, width: 70, height: 27, rx: 7
  }));
  gg.appendChild(svgEl("text", { id: "goalMarkerText", x: goal.x, y: goal.y - 48 }, state.goalCollected ? "FOUND" : "GOAL"));
  layer.appendChild(gg);
}

function buildPlayerSprite(direction = "down", frame = 0) {
  const g = svgEl("g", { id: "player", class: "pixel player-sprite" });
  g.appendChild(svgEl("ellipse", { class: "player-shadow", cx: 16, cy: 41, rx: 14, ry: 5 }));

  const pixels = [];
  const add = (fill, x, y, w = 1, h = 1) => pixels.push([fill, x, y, w, h]);

  // hood / hat
  add("#6a3e17", 8, 0, 16, 4);
  add("#8c5724", 6, 4, 20, 4);
  add("#e0b14f", 11, -2, 10, 3);
  add("#4b2b12", 5, 8, 22, 3);

  // face
  add("#f4c59a", 9, 11, 14, 10);
  add("#ffdfc1", 11, 13, 10, 4);
  if (direction === "left") {
    add("#20110b", 11, 14, 2, 2);
    add("#20110b", 10, 17, 2, 1);
  } else if (direction === "right") {
    add("#20110b", 19, 14, 2, 2);
    add("#20110b", 20, 17, 2, 1);
  } else if (direction === "up") {
    add("#8c5724", 10, 10, 12, 3);
  } else {
    add("#20110b", 12, 14, 2, 2);
    add("#20110b", 18, 14, 2, 2);
    add("#c17b66", 15, 18, 2, 1);
  }

  // body / cape / belt
  add("#2aa85e", 8, 22, 16, 12);
  add("#1b6e40", 8, 22, 3, 12);
  add("#1b6e40", 21, 22, 3, 12);
  add("#6f2740", 6, 23, 3, 12);
  add("#6f2740", 23, 23, 3, 12);
  add("#f0cb67", 12, 28, 8, 3);
  add("#80561d", 14, 28, 4, 4);

  // arms
  if (direction === "left") {
    add("#f4c59a", 4, 24, 5, 4); add("#f4c59a", 22, 25, 5, 4);
  } else if (direction === "right") {
    add("#f4c59a", 6, 25, 5, 4); add("#f4c59a", 24, 24, 5, 4);
  } else {
    add("#f4c59a", 5, 25, 4, 4); add("#f4c59a", 23, 25, 4, 4);
  }

  // legs / boots animation
  if (frame % 2 === 0) {
    add("#5c3920", 10, 34, 5, 9); add("#5c3920", 18, 35, 5, 8);
    add("#121212", 9, 42, 7, 3); add("#121212", 18, 42, 7, 3);
  } else {
    add("#5c3920", 11, 35, 5, 8); add("#5c3920", 18, 34, 5, 9);
    add("#121212", 10, 42, 7, 3); add("#121212", 18, 42, 7, 3);
  }

  pixels.forEach(([fill, x, y, w, h]) => g.appendChild(svgEl("rect", { fill, x, y, width: w, height: h })));
  return g;
}

function setPlayerPose(direction = "down", frame = 0) {
  const layer = $("playerLayer");
  const old = $("player");
  const currentTransform = old ? old.getAttribute("transform") : `translate(${node(state.playerNode).x - 16}, ${node(state.playerNode).y - 34})`;
  if (old) old.remove();
  const sprite = buildPlayerSprite(direction, frame);
  sprite.setAttribute("transform", currentTransform);
  layer.appendChild(sprite);
}

function drawPlayer(x, y, direction = "down", frame = 0) {
  const layer = $("playerLayer");
  layer.innerHTML = "";
  const sprite = buildPlayerSprite(direction, frame);
  sprite.setAttribute("transform", `translate(${x - 16}, ${y - 34})`);
  layer.appendChild(sprite);
}

function clearEffects() {
  $("effectLayer").innerHTML = "";
}

function dropFootstep(x, y, index = 0) {
  const layer = $("effectLayer");
  const g = svgEl("g", { class: "footstep", transform: `translate(${x}, ${y}) rotate(${index % 2 === 0 ? -18 : 18})` });
  g.appendChild(svgEl("ellipse", { cx: 0, cy: 0, rx: 3.1, ry: 5.4 }));
  g.appendChild(svgEl("circle", { cx: -2.7, cy: -4.6, r: 1.1 }));
  g.appendChild(svgEl("circle", { cx: -0.6, cy: -5.4, r: 1.0 }));
  g.appendChild(svgEl("circle", { cx: 1.6, cy: -5.0, r: 0.9 }));
  layer.appendChild(g);
  setTimeout(() => g.remove(), 1800);
}


function requiredPurpleNodes() {
  return state.graph?.purple_required_nodes || REQUIRED_PURPLE_NODES;
}

function routePurpleStatus(pathNodes = []) {
  const required = requiredPurpleNodes();
  const hit = required.filter(id => pathNodes.includes(id));
  const missing = required.filter(id => !pathNodes.includes(id));
  return { required, hit, missing, unlocked: missing.length === 0 };
}

function updatePurpleNodeVisuals() {
  document.querySelectorAll(".node-item").forEach(g => {
    const id = g.getAttribute("data-node");
    if (!id) return;
    g.classList.toggle("purple-collected", state.collectedPurple.has(id));
  });
}

function collectPurpleNode(id) {
  if (!requiredPurpleNodes().includes(id)) return;
  state.collectedPurple.add(id);
  updatePurpleNodeVisuals();
  const status = routePurpleStatus(Array.from(state.collectedPurple));
  $("mapSubtitle").textContent =
    `Đã kích hoạt node tím: ${Array.from(state.collectedPurple).join(", ")} • Còn thiếu: ${status.missing.join(", ") || "không còn"}`;
}

function lockGoalBecauseMissing(missing) {
  const txt = $("goalMarkerText");
  if (txt) txt.textContent = "LOCKED";

  const goalMarker = $("goalMarker");
  if (goalMarker) goalMarker.classList.add("locked");

  $("mapSubtitle").textContent =
    `Đã tới GOAL nhưng rương chưa mở. Còn thiếu node tím: ${missing.join(", ")}.`;

  const layer = $("effectLayer");
  const goal = node("GOAL");
  const g = svgEl("g", { class: "locked-burst" });
  g.appendChild(svgEl("circle", { cx: goal.x, cy: goal.y - 8, r: 28, class: "locked-ring" }));
  g.appendChild(svgEl("text", { x: goal.x, y: goal.y - 2, class: "locked-text" }, "LOCK"));
  layer.appendChild(g);
  setTimeout(() => g.remove(), 1800);
}


function celebrateGoal() {
  state.goalCollected = true;
  const goalMarker = $("goalMarker");
  const txt = $("goalMarkerText");
  if (goalMarker) goalMarker.classList.add("collected");
  if (txt) txt.textContent = "FOUND";

  const layer = $("effectLayer");
  const goal = node("GOAL");
  const g = svgEl("g", { class: "goal-burst" });
  const gx = goal.x, gy = goal.y - 8;
  for (let i = 0; i < 14; i++) {
    const angle = (Math.PI * 2 * i) / 14;
    const x2 = gx + Math.cos(angle) * 34;
    const y2 = gy + Math.sin(angle) * 34;
    g.appendChild(svgEl("line", { x1: gx, y1: gy, x2, y2, class: "burst-ray" }));
  }
  g.appendChild(svgEl("circle", { cx: gx, cy: gy, r: 20, class: "burst-ring" }));
  layer.appendChild(g);
  setTimeout(() => g.remove(), 1400);
}

function getSelectedPayload() {
  return {
    algorithm: state.algo,
    start: "S",
    goal: "GOAL",
    mode: $("costMode").value,
    beam_width: Number($("beamWidth").value || 2),
    depth_limit: Number($("depthLimit").value || 80)
  };
}


function setRouteUiLocked(locked) {
  state.routeLocked = locked;
  ["runBtn", "animateBtn", "compareBtn"].forEach((id) => {
    const btn = $(id);
    if (btn) btn.disabled = locked;
  });
  document.querySelectorAll(".algo-btn").forEach((btn) => {
    btn.disabled = locked;
  });
}

function canStartRouteAnimation() {
  if (state.routeLocked || state.animatingPlayer) {
    $("mapSubtitle").textContent = "Animation đang chạy, vui lòng chờ nhân vật hoàn tất lượt hiện tại.";
    return false;
  }
  return true;
}

async function runSearch() {
  if (!canStartRouteAnimation()) return;

  state.routeCompleted = false;
  setRouteUiLocked(true);

  try {
    state.collectedPurple = new Set();
    state.goalCollected = false;
    state.footstepCount = 0;

    if (state.dungeon) {
      state.dungeon.triggeredFromMain = false;
      state.dungeon.pendingResume = null;
      state.dungeon.pauseReason = null;
    }
    if (state.dun02Dungeon) {
      state.dun02Dungeon.triggeredFromMain = false;
    }
    if (state.fb04Dungeon) {
      state.fb04Dungeon.triggeredFromMain = false;
      state.fb04Dungeon.pendingResume = null;
      state.fb04Dungeon.pauseReason = null;
    }
    state.bossFinalTriggered = false;
    if (state.andor) state.andor.triggeredFromMain = false;

    drawMarkers();
    clearVisuals();
    $("resultStatus").textContent = "Python đang chạy...";

    const res = await fetch("/api/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(getSelectedPayload())
    });
    const result = await res.json();

    if (!result.success) {
      alert(result.error || "Có lỗi khi chạy thuật toán Python.");
      return;
    }

    state.last = result;
    renderResult(result);
    await animateVisitedThenRoute(result);
  } catch (err) {
    console.error(err);
    alert(err.message || "Có lỗi khi chạy thuật toán.");
  } finally {
    setRouteUiLocked(false);
  }
}
function renderResult(result) {
  const purple = routePurpleStatus(result.path_nodes || []);
  $("resultStatus").textContent = result.found
    ? (purple.unlocked ? "✅ Đã đi đủ node tím và mở được rương" : `🔒 Thiếu node tím: ${purple.missing.join(", ")}`)
    : "❌ Không tìm thấy route đủ node tím";
  $("statAlgo").textContent = ALGO_LABELS[result.algorithm] || result.algorithm;
  $("statExpanded").textContent = result.nodes_expanded;
  $("statCost").textContent = result.found ? (result.total_cost >= 9999 ? "phạt" : result.total_cost.toFixed(1)) : "--";
  $("statRuntime").textContent = `${result.runtime_ms} ms`;
  $("explainText").textContent = result.explanation;

  $("mapTitle").textContent = result.multi_goal
    ? `${ALGO_LABELS[result.algorithm] || result.algorithm}: KTX D → đủ node tím → Khối A.1`
    : `${ALGO_LABELS[result.algorithm] || result.algorithm}: KTX D → Khối A.1`;
  $("mapSubtitle").textContent = result.found
    ? `Route Python: ${result.path_names.join(" → ")} • Rule mở rương: phải qua DUN02, HGL02, FB04. ${purple.unlocked ? "✅ Đủ node tím." : "🔒 Thiếu: " + purple.missing.join(", ")}${result.bad_edges ? " ⚠ Có " + result.bad_edges + " cạnh bị phạt vật cản." : ""}`
    : "Python không tìm được đường trong graph hiện tại.";

  const list = $("pathList");
  list.innerHTML = "";
  if (!result.path_nodes.length) {
    list.innerHTML = "<li>Chưa có route.</li>";
    return;
  }
  result.path_nodes.forEach((id, i) => {
    const li = document.createElement("li");
    const checkpoint = requiredPurpleNodes().includes(id) ? " 🟣 CHECKPOINT" : "";
    li.innerHTML = `<b>${i + 1}. ${node(id).name}${checkpoint}</b><small>Node kỹ thuật: ${id}</small>`;
    list.appendChild(li);
  });
}

function clearVisuals() {
  $("visitedLayer").innerHTML = "";
  $("routeLayer").innerHTML = "";
  clearEffects();
  state.animatingPlayer = false;
}

function drawVisited(id) {
  if (!$("showVisited").checked) return;
  const n = node(id);
  if (!n) return;
  $("visitedLayer").appendChild(svgEl("circle", {
    class: "visited-node",
    cx: n.x,
    cy: n.y,
    r: 5
  }));
}

function routePoints(result) {
  if (!result.path_edges.length) return result.path_nodes.map(id => node(id));
  const pts = [];
  result.path_edges.forEach((edge, idx) => {
    const segment = edgePoints(edge);
    if (idx === 0) pts.push(...segment);
    else pts.push(...segment.slice(1));
  });
  return pts;
}

function drawRoute(result) {
  const layer = $("routeLayer");
  if (!result.found) return;
  const pts = routePoints(result);
  const poly = pts.map(p => `${p.x},${p.y}`).join(" ");

  layer.appendChild(svgEl("polyline", { class: "route-line-under", points: poly }));
  layer.appendChild(svgEl("polyline", { class: "route-line", points: poly }));

  result.path_nodes.forEach((id) => {
    const n = node(id);
    const g = svgEl("g");
    g.appendChild(svgEl("circle", { class: "route-node", cx: n.x, cy: n.y, r: 4 }));
    layer.appendChild(g);
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function animateVisitedThenRoute(result) {
  if (!result) return;

  const visited = result.visited || [];
  const alg = String(result.algorithm || "").toLowerCase();

  let shownVisited = visited;
  let delay = 12;

  // IDS/IDDFS sinh rất nhiều node visited.
  // Nếu vẽ nhiều node trước khi chạy route thì người chơi tưởng nhân vật bị đứng im.
  // Vì vậy IDS chỉ preview cực ngắn rồi cho nhân vật đi ngay.
  if (alg === "ids" || visited.length > 2000) {
    const MAX_IDS_PREVIEW = 80;
    const step = Math.max(1, Math.ceil(visited.length / MAX_IDS_PREVIEW));
    shownVisited = visited.filter((_, idx) => idx % step === 0).slice(0, MAX_IDS_PREVIEW);
    delay = 0;

    $("mapSubtitle").textContent =
      `${(result.algorithm || "IDS").toUpperCase()} đã tìm được route. Thuật toán duyệt ${visited.length.toLocaleString()} trạng thái, nên chỉ preview nhanh ${shownVisited.length} node rồi cho nhân vật đi ngay.`;
  }

  for (const id of shownVisited) {
    drawVisited(id);
    if (delay > 0) await sleep(delay);
  }

  drawRoute(result);
  await sleep(120);
  await animatePlayerAlongResult(result);
}

async function animatePlayer() {
  if (!state.last || !state.last.found) return;

  if (state.animatingPlayer || state.routeLocked) {
    $("mapSubtitle").textContent = "Animation đang chạy, không chạy chồng thêm lượt mới.";
    return;
  }

  if (state.routeCompleted && state.playerNode === "GOAL") {
    $("mapSubtitle").textContent = "Nhân vật đã tới GOAL. Bấm Đặt lại hoặc Tìm đường bằng thuật toán khác để chạy lại.";
    return;
  }

  setRouteUiLocked(true);
  try {
    await animatePlayerAlongResult(state.last);
  } catch (err) {
    console.error(err);
    alert(err.message || "Có lỗi khi cho nhân vật di chuyển.");
  } finally {
    setRouteUiLocked(false);
  }
}

async function triggerAndorDungeonFromMainRoute() {
  // Fix lỗi undefined: route chính đang gọi màn AND-OR ở node M26.
  // Trong project hiện tại, hầm AND-OR được mở bằng triggerDungeonFromMainRoute().
  if (typeof triggerDungeonFromMainRoute === "function") {
    return triggerDungeonFromMainRoute();
  }

  // Fallback nếu tên hàm thay đổi.
  if (typeof enterDungeon === "function") {
    return enterDungeon();
  }

  alert("Không tìm thấy hàm mở hầm AND-OR / HGL02.");
}

async function animatePlayerAlongResult(result) {
  if (!result || !result.found || state.animatingPlayer) return;

  state.animatingPlayer = true;

  try {
    const pathNodes = result.path_nodes;
    const speed = Number($("speedRange").value || 260);

    state.playerNode = pathNodes[0];
    drawPlayer(node(pathNodes[0]).x, node(pathNodes[0]).y, "down", 0);
    await sleep(120);

    for (let i = 1; i < pathNodes.length; i++) {
      const nextId = pathNodes[i];
      const edge = result.path_edges[i - 1];
      const segmentPts = edgePoints(edge);

      await movePlayerSmooth(segmentPts, speed, nextId);

      state.playerNode = nextId;
      collectPurpleNode(nextId);

      if (nextId === "DUN02") {
        await triggerDun02DungeonFromMainRoute();
      }

      if (nextId === "HGL02") {
        await triggerDungeonFromMainRoute();
      }

      if (nextId === "FB04") {
        await triggerFb04DungeonFromMainRoute();
      }

      if ((nextId === "GOAL" || nextId === "TREASURE") && !state.bossFinalTriggered) {
        state.bossFinalTriggered = true;
        $("mapSubtitle").textContent = "Đã tới kho báu, nhưng Rồng trùm cuối đang canh giữ. Mở màn Boss Minimax.";
        await triggerBossFinalFromTreasure();
      }
    }

    const status = routePurpleStatus(Array.from(state.collectedPurple));
    if (status.unlocked) {
      celebrateGoal();
    } else {
      lockGoalBecauseMissing(status.missing);
    }

    if (state.playerNode === "GOAL" || state.playerNode === "TREASURE") {
      state.routeCompleted = true;
    }
  } finally {
    state.animatingPlayer = false;
  }
}

async function movePlayerSmooth(points, duration, nextId) {
  let player = $("player");
  if (!player) return;

  let totalLen = 0;
  const segLens = [];
  for (let i = 1; i < points.length; i++) {
    const len = Math.hypot(points[i].x - points[i-1].x, points[i].y - points[i-1].y);
    segLens.push(len);
    totalLen += len;
  }

  const direction = (() => {
    const dx = points[points.length - 1].x - points[0].x;
    const dy = points[points.length - 1].y - points[0].y;
    if (Math.abs(dy) > Math.abs(dx)) return dy < 0 ? "up" : "down";
    return dx >= 0 ? "right" : "left";
  })();

  let frameIndex = 0;
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1];
    const b = points[i];
    const segDuration = Math.max(120, duration * (segLens[i - 1] / Math.max(totalLen, 1)));
    const frames = Math.max(10, Math.round(segDuration / 18));

    for (let t = 1; t <= frames; t++) {
      const r = t / frames;
      const bob = Math.sin(r * Math.PI) * 1.6;
      const x = a.x + (b.x - a.x) * r;
      const y = a.y + (b.y - a.y) * r - bob;

      if (t % 5 === 0) {
        frameIndex++;
        setPlayerPose(direction, frameIndex % 2);
        player = $("player") || player;
      }

      if (t % 8 === 0) {
        state.footstepCount += 1;
        dropFootstep(x - 1, y + 9, state.footstepCount);
      }

      player.setAttribute("transform", `translate(${x - 16}, ${y - 34})`);
      await sleep(16);
    }
  }

  setPlayerPose(direction, 0);
  player = $("player") || player;
  player.setAttribute("transform", `translate(${node(nextId).x - 16}, ${node(nextId).y - 34})`);
}

async function compareAll() {
  const tbody = $("compareTable").querySelector("tbody");
  tbody.innerHTML = "";

  const res = await fetch("/api/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(getSelectedPayload())
  });

  const data = await res.json();
  if (!data.success) {
    alert("Không so sánh được thuật toán.");
    return;
  }

  data.results.forEach(r => {
    const tr = document.createElement("tr");
    const costText = r.found ? (r.total_cost >= 9999 ? "phạt" : r.total_cost.toFixed(1)) : "--";
    tr.innerHTML = `<td>${ALGO_LABELS[r.algorithm]}</td><td>${r.found ? "✅" : "❌"}</td><td>${r.nodes_expanded}</td><td>${costText}</td>`;
    tbody.appendChild(tr);
  });
}

function resetGame() {
  state.routeCompleted = false;
  state.animatingPlayer = false;
  setRouteUiLocked(false);
  state.last = null;
  state.playerNode = "S";
  state.animatingPlayer = false;
  state.goalCollected = false;
  state.footstepCount = 0;
  state.collectedPurple = new Set();
  state.dungeon.triggeredFromMain = false;
  if (state.dun02Dungeon) state.dun02Dungeon.triggeredFromMain = false;
  if (state.fb04Dungeon) state.fb04Dungeon.triggeredFromMain = false;
  state.bossFinalTriggered = false;
  state.andor.triggeredFromMain = false;
  clearVisuals();
  drawMarkers();
  if (hasXY(node("S"))) {
    drawPlayer(node("S").x, node("S").y, "down", 0);
  }
  $("resultStatus").textContent = "Chưa chạy";
  $("statAlgo").textContent = "--";
  $("statExpanded").textContent = "--";
  $("statCost").textContent = "--";
  $("statRuntime").textContent = "--";
  $("pathList").innerHTML = "";
  $("explainText").textContent = "Chạy thuật toán để xem mô tả.";
  $("mapTitle").textContent = "Sẵn sàng tìm kho báu";
  $("mapSubtitle").textContent = "Chọn thuật toán rồi bấm “Tìm đường”. Backend Python sẽ xử lý route.";
}

function getSvgPoint(evt) {
  const svg = $("gameSvg");
  const pt = svg.createSVGPoint();
  pt.x = evt.clientX;
  pt.y = evt.clientY;
  return pt.matrixTransform(svg.getScreenCTM().inverse());
}

function applyViewBox() {
  const vb = state.viewBox;
  $("gameSvg").setAttribute("viewBox", `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
}

function clampViewBox(vb) {
  const minW = MAP_W * 0.32;
  const minH = MAP_H * 0.32;
  vb.w = Math.max(minW, Math.min(MAP_W, vb.w));
  vb.h = Math.max(minH, Math.min(MAP_H, vb.h));
  vb.x = Math.max(0, Math.min(MAP_W - vb.w, vb.x));
  vb.y = Math.max(0, Math.min(MAP_H - vb.h, vb.y));
  return vb;
}

function zoomAt(factor, cx = null, cy = null) {
  const vb = { ...state.viewBox };
  cx ??= vb.x + vb.w / 2;
  cy ??= vb.y + vb.h / 2;
  const newW = vb.w / factor;
  const newH = vb.h / factor;
  const rx = (cx - vb.x) / vb.w;
  const ry = (cy - vb.y) / vb.h;
  state.viewBox = clampViewBox({
    x: cx - newW * rx,
    y: cy - newH * ry,
    w: newW,
    h: newH
  });
  applyViewBox();
}

function resetView() {
  state.viewBox = { x: 0, y: 0, w: MAP_W, h: MAP_H };
  applyViewBox();
}







function setDungeonOverlayMode(mode = "HGL02") {
  state.currentDungeonMode = mode;

  const overlay = $("dungeonOverlay");
  overlay?.classList.toggle("dun02-mode", mode === "DUN02");
  overlay?.classList.toggle("hgl02-mode", mode === "HGL02");
  overlay?.classList.toggle("fb04-mode", mode === "FB04");
  overlay?.classList.remove("dun02-editing");

  state.dun02EditMode = false;

  if ($("dungeonEyebrow")) {
    $("dungeonEyebrow").textContent =
      mode === "DUN02" ? "DUN02 • BACKTRACKING + FORWARD CHECKING" :
      mode === "FB04" ? "FB04 • BELIEF STATE + BFS" :
      "HGL02 • AND-OR SEARCH";
  }

  if ($("dungeonTitle")) {
    $("dungeonTitle").textContent =
      mode === "DUN02" ? "Hầm ngục Backtracking + Forward Checking DUN02" :
      mode === "FB04" ? "Hầm ngục Belief State + BFS FB04" :
      "Hầm ngục AND-OR HGL02";
  }

  if ($("dungeonRuleText")) {
    $("dungeonRuleText").textContent =
      mode === "DUN02" ? "DUN02: Start → KEY → EXIT. Forward Checking sẽ cắt bẫy và EXIT khi chưa có KEY." :
      mode === "FB04" ? "FB04: mỗi lần chạy sẽ chọn ngẫu nhiên 1 Start thật trong 3 Start, nhưng AI chỉ biết tập belief và dùng BFS để hội tụ về B55." :
      "Map HGL02 cố định: Start = H01, Goal = EXIT.";
  }

  if ($("dun02EditPanel")) $("dun02EditPanel").classList.add("hidden");
  if ($("fb04EditPanel")) {
    $("fb04EditPanel").classList.add("hidden");
    $("fb04EditPanel").style.display = "none";
  }

  if ($("hgl02RunControls")) {
    $("hgl02RunControls").style.display = "block";
  }
  if ($("hgl02SolveFixedBtn")) {
    $("hgl02SolveFixedBtn").style.display = "inline-flex";
    $("hgl02SolveFixedBtn").textContent = "▶ Chạy thuật toán hầm ngục";
  }
  if ($("hgl02ResetViewBtn")) {
    $("hgl02ResetViewBtn").style.display = mode === "FB04" ? "none" : "inline-flex";
  }
}

function dungeonStartId(mapData) {
  return mapData?.start || "H01";
}

function dungeonGoalId(mapData) {
  return mapData?.exit || (mapData?.nodes?.H58 ? "H58" : Object.keys(mapData?.nodes || {}).slice(-1)[0]);
}

function openDungeonOverlay() {
  $("dungeonOverlay")?.classList.remove("hidden");
}

function closeDungeonOverlay() {
  $("dungeonOverlay")?.classList.add("hidden");

  // Nếu hầm được mở từ route chính thì khi đóng overlay,
  // route mới được phép tiếp tục di chuyển sang node tiếp theo.
  if (state.currentDungeonMode === "HGL02") {
    resumeHgl02MainRouteAfterDungeon();
  }
  if (state.currentDungeonMode === "FB04") {
    resumeFb04MainRouteAfterDungeon();
  }
}

function resumeHgl02MainRouteAfterDungeon() {
  const resume = state.dungeon?.pendingResume;
  if (typeof resume === "function") {
    state.dungeon.pendingResume = null;
    state.dungeon.pauseReason = null;
    state.dungeon.triggeredFromMain = false;
    resume();
  }
}

function waitForHgl02DungeonCloseIfNeeded() {
  if (!state.animatingPlayer) return Promise.resolve();
  return new Promise((resolve) => {
    state.dungeon.pendingResume = resolve;
    state.dungeon.pauseReason = "route-main";
  });
}

function resumeFb04MainRouteAfterDungeon() {
  const resume = state.fb04Dungeon?.pendingResume;
  if (typeof resume === "function") {
    state.fb04Dungeon.pendingResume = null;
    state.fb04Dungeon.pauseReason = null;
    state.fb04Dungeon.triggeredFromMain = false;
    resume();
  }
}

function waitForFb04DungeonCloseIfNeeded() {
  if (!state.animatingPlayer) return Promise.resolve();
  return new Promise((resolve) => {
    state.fb04Dungeon.pendingResume = resolve;
    state.fb04Dungeon.pauseReason = "route-main";
  });
}

function updateDungeonStats(sessionId = "--", beliefCount = 0, action = "--") {
  if ($("dungeonSession")) $("dungeonSession").textContent = sessionId || "--";
  if ($("dungeonSeen")) $("dungeonSeen").textContent = String(beliefCount);
  if ($("dungeonHidden")) $("dungeonHidden").textContent = String(action || "--");
}

function cloneHgl02Map(mapData) {
  return JSON.parse(JSON.stringify(mapData));
}

function activeHgl02Map() {
  return state.dungeon.customMap || state.dungeon.map;
}

function ensureHgl02CustomMap(clear = false) {
  if (!state.dungeon.map) return null;
  if (!state.dungeon.customMap || clear) {
    state.dungeon.customMap = {
      image: state.dungeon.map.image,
      width: state.dungeon.map.width,
      height: state.dungeon.map.height,
      start: clear ? null : state.dungeon.map.start,
      exit: clear ? null : state.dungeon.map.exit,
      nodes: clear ? {} : cloneHgl02Map(state.dungeon.map.nodes || {}),
      edges: clear ? [] : cloneHgl02Map(state.dungeon.map.edges || []),
      decorations: clear ? { blocked: [] } : cloneHgl02Map(state.dungeon.map.decorations || { blocked: [] }),
      custom: true
    };
  }
  return state.dungeon.customMap;
}

function nextHgl02NodeId(kind) {
  const m = ensureHgl02CustomMap(false);
  if (kind === "start") {
    let idx = 1;
    let id = "HS";
    while (m.nodes[id]) {
      id = "HS" + idx;
      idx++;
    }
    return id;
  }
  if (kind === "exit") return "HE";
  let id = "";
  state.dungeon.customCounter ??= 1;
  do {
    id = "H" + String(state.dungeon.customCounter).padStart(2, "0");
    state.dungeon.customCounter += 1;
  } while (m.nodes[id]);
  return id;
}

function setHgl02EditMode(enabled) {
  state.dungeon.editMode = enabled;
  $("dungeonOverlay")?.classList.toggle("hgl02-editing", enabled);
  if ($("hgl02EditBtn")) $("hgl02EditBtn").textContent = enabled ? "✓ Đang đánh node" : "✎ Bật đánh node";
  if (enabled) ensureHgl02CustomMap(false);
}

function hgl02SvgPoint(evt) {
  const svg = $("hgl02Svg");
  const pt = svg.createSVGPoint();
  pt.x = evt.clientX;
  pt.y = evt.clientY;
  return pt.matrixTransform(svg.getScreenCTM().inverse());
}

function hgl02SelectNode(id) {
  return;
  const arr = state.dungeon.selectedNodes || [];
  if (arr.includes(id)) {
    state.dungeon.selectedNodes = arr.filter(x => x !== id);
  } else {
    state.dungeon.selectedNodes = [...arr, id].slice(-2);
  }
  drawHgl02Map(activeHgl02Map(), { selected: state.dungeon.selectedNodes });
}

function addHgl02CustomNode(evt) {
  if (!state.dungeon.editMode) return;
  if (evt.target && evt.target.closest && evt.target.closest(".dun02-node")) return;

  const m = ensureHgl02CustomMap(false);
  const p = hgl02SvgPoint(evt);
  const kind = $("hgl02NodeKind")?.value || "normal";
  const id = nextHgl02NodeId(kind);

  m.nodes[id] = {
    label: kind === "start" ? "Start / Possible" : kind === "exit" ? "Exit" : kind === "blocked" ? "Vật cản" : id,
    x: Number(p.x.toFixed(1)),
    y: Number(p.y.toFixed(1)),
    kind
  };

  if (kind === "start" && !m.start) m.start = id;
  if (kind === "exit") m.exit = id;

  if (kind === "blocked") {
    m.decorations ||= { blocked: [] };
    m.decorations.blocked ||= [];
    m.decorations.blocked.push({
      x: Number(p.x.toFixed(1)),
      y: Number(p.y.toFixed(1)),
      label: "Vật cản",
      width: 80,
      height: 40
    });
  }

  drawHgl02Map(m, { selected: state.dungeon.selectedNodes || [] });
  $("dungeonStatus").textContent = `Đã thêm node ${id} tại x=${p.x.toFixed(1)}, y=${p.y.toFixed(1)}. Chọn 2 node rồi bấm “Nối 2 node đã chọn”.`;
}

function connectHgl02SelectedNodes() {
  const m = ensureHgl02CustomMap(false);
  const [a, b] = state.dungeon.selectedNodes || [];
  if (!a || !b || a === b) {
    alert("Hãy chọn đúng 2 node trên map HGL02 để nối cạnh.");
    return;
  }
  m.edges ||= [];
  const exists = m.edges.some(e => (e[0] === a && e[1] === b) || (e[0] === b && e[1] === a));
  if (!exists) m.edges.push([a, b]);
  state.dungeon.selectedNodes = [];
  drawDun02Map(m);
  $("dungeonStatus").textContent = `Đã nối cạnh ${a} ↔ ${b}. Belief State sẽ tự suy ra hướng N/E/S/W theo tọa độ.`;
}

function clearHgl02CustomNodes() {
  if (!state.dungeon.map) return;
  state.dungeon.customMap = {
    image: state.dungeon.map.image,
    width: state.dungeon.map.width,
    height: state.dungeon.map.height,
    start: null,
    exit: null,
    nodes: {},
    edges: [],
    decorations: { blocked: [] },
    custom: true
  };
  state.dungeon.selectedNodes = [];
  state.dungeon.customCounter = 1;
  setHgl02EditMode(true);
  drawHgl02Map(state.dungeon.customMap);
  $("dungeonStatus").textContent = "Đã xóa node mẫu. Hãy đặt Start, Exit, node thường, vật cản rồi nối cạnh.";
}

function undoHgl02CustomNode() {
  const m = ensureHgl02CustomMap(false);
  const ids = Object.keys(m.nodes || {});
  if (!ids.length) return;
  const last = ids[ids.length - 1];
  delete m.nodes[last];
  m.edges = (m.edges || []).filter(e => e[0] !== last && e[1] !== last);
  if (m.start === last) m.start = null;
  if (m.exit === last) m.exit = null;
  state.dungeon.selectedNodes = (state.dungeon.selectedNodes || []).filter(id => id !== last);
  drawHgl02Map(m, { selected: state.dungeon.selectedNodes });
  $("dungeonStatus").textContent = `Đã undo node ${last}.`;
}

function exportHgl02CustomCode() {
  const m = ensureHgl02CustomMap(false);
  const code = [
    "# HGL02 Belief State custom nodes/edges",
    "nodes = " + JSON.stringify(m.nodes, null, 2),
    "",
    "edges = " + JSON.stringify(m.edges, null, 2),
    "",
    `start = ${JSON.stringify(m.start)}`,
    `exit = ${JSON.stringify(m.exit)}`,
    "",
    "# Lưu ý: Belief ban đầu gồm tất cả node kind='start'.",
    "# Action N/E/S/W được backend suy ra từ hướng tọa độ giữa các node đã nối."
  ].join("\n");
  if ($("hgl02ExportBox")) $("hgl02ExportBox").value = code;
}

function drawHgl02Map(mapData, options = {}) {
  if (!mapData) return;

  const currentBelief = new Set(options.belief || []);
  const selected = new Set(options.selected || []);
  const route = options.route || [];
  const pruned = new Set(options.pruned || []);

  $("hgl02Svg").setAttribute("viewBox", `0 0 ${mapData.width} ${mapData.height}`);
  $("hgl02Bg").setAttribute("href", mapData.image);

  const edgeLayer = $("hgl02EdgeLayer");
  const decoLayer = $("hgl02DecoLayer");
  const routeLayer = $("hgl02RouteLayer");
  const nodeLayer = $("hgl02NodeLayer");

  edgeLayer.innerHTML = "";
  decoLayer.innerHTML = "";
  routeLayer.innerHTML = "";
  nodeLayer.innerHTML = "";

  const nodes = mapData.nodes || {};

  (mapData.edges || []).forEach(([a, b]) => {
    const na = nodes[a], nb = nodes[b];
    if (!na || !nb) return;
    edgeLayer.appendChild(svgEl("line", {
      class: "hgl02-edge",
      x1: na.x, y1: na.y,
      x2: nb.x, y2: nb.y
    }));
  });

  if (route.length > 1) {
    for (let i = 1; i < route.length; i++) {
      const a = nodes[route[i - 1]], b = nodes[route[i]];
      if (!a || !b) continue;
      routeLayer.appendChild(svgEl("line", {
        class: "hgl02-edge route",
        x1: a.x, y1: a.y,
        x2: b.x, y2: b.y
      }));
    }
  }

  (mapData.decorations?.blocked || []).forEach(item => {
    const g = svgEl("g", { class: "hgl02-blocked" });
    g.appendChild(svgEl("rect", {
      x: item.x - item.width / 2,
      y: item.y - item.height / 2,
      width: item.width,
      height: item.height,
      rx: 10
    }));
    g.appendChild(svgEl("line", {
      class: "hgl02-cross",
      x1: item.x - item.width / 2 + 8,
      y1: item.y - item.height / 2 + 8,
      x2: item.x + item.width / 2 - 8,
      y2: item.y + item.height / 2 - 8
    }));
    g.appendChild(svgEl("line", {
      class: "hgl02-cross",
      x1: item.x - item.width / 2 + 8,
      y1: item.y + item.height / 2 - 8,
      x2: item.x + item.width / 2 - 8,
      y2: item.y - item.height / 2 + 8
    }));
    g.appendChild(svgEl("text", { x: item.x, y: item.y + 5 }, item.label || "Vật cản"));
    decoLayer.appendChild(g);
  });

  Object.entries(nodes).forEach(([id, n]) => {
    const cls = ["hgl02-node", n.kind || "normal"];
    if (selected.has(id)) cls.push("selected");
    if (currentBelief.has(id)) cls.push("belief");
    if (pruned.has(id)) cls.push("pruned");

    const g = svgEl("g", { class: cls.join(" "), "data-hgl02-node": id });
    g.addEventListener("click", (evt) => {
      evt.stopPropagation();
      hgl02SelectNode(id);
    });

    g.appendChild(svgEl("circle", { cx: n.x, cy: n.y, r: id === mapData.exit ? 20 : 16 }));
    g.appendChild(svgEl("text", { x: n.x, y: n.y - 24 }, id));
    nodeLayer.appendChild(g);
  });
}


function drawHgl02PlayerAt(nodeId, mapData) {
  const layer = $("hgl02PlayerLayer");
  if (!layer || !mapData || !mapData.nodes || !mapData.nodes[nodeId]) return;
  layer.innerHTML = "";

  const n = mapData.nodes[nodeId];
  const g = svgEl("g", { class: "hgl02-player", id: "hgl02Player", transform: `translate(${n.x}, ${n.y})` });
  g.appendChild(svgEl("ellipse", { class: "hgl02-player-shadow", cx: 0, cy: 18, rx: 18, ry: 7 }));
  g.appendChild(svgEl("circle", { class: "hgl02-player-body", cx: 0, cy: 0, r: 16 }));
  g.appendChild(svgEl("path", { class: "hgl02-player-hood", d: "M -12 -8 L 0 -28 L 12 -8 Z" }));
  g.appendChild(svgEl("text", { class: "hgl02-player-label", x: 0, y: -34 }, nodeId));
  layer.appendChild(g);
}

async function moveHgl02PlayerPath(pathNodes, mapData) {
  if (!pathNodes || !pathNodes.length || !mapData) return;
  drawHgl02PlayerAt(pathNodes[0], mapData);

  let player = $("hgl02Player");
  if (!player) return;

  for (let i = 1; i < pathNodes.length; i++) {
    const from = mapData.nodes[pathNodes[i - 1]];
    const to = mapData.nodes[pathNodes[i]];
    if (!from || !to) continue;

    const frames = 24;
    for (let f = 1; f <= frames; f++) {
      const t = f / frames;
      const x = from.x + (to.x - from.x) * t;
      const y = from.y + (to.y - from.y) * t - Math.sin(t * Math.PI) * 5;
      player.setAttribute("transform", `translate(${x}, ${y})`);
      await sleep(22);
    }
    player.setAttribute("transform", `translate(${to.x}, ${to.y})`);
    const label = player.querySelector("text");
    if (label) label.textContent = pathNodes[i];
    updateDungeonStats(state.dungeon.sessionId || "--", 1, pathNodes[i]);
    $("dungeonStatus").textContent = pathNodes[i] === "H58"
      ? "✅ Nhân vật đã tới EXIT, thoát hầm ngục HGL02."
      : `Nhân vật đang di chuyển tới ${pathNodes[i]}.`;
    await sleep(120);
  }
}

async function solveHgl02AndorDungeon() {
  if (!state.dungeon.sessionId || !state.dungeon.map) {
    await enterDungeon();
  }

  const res = await fetch(`/api/hgl02/andor_solve?session_id=${encodeURIComponent(state.dungeon.sessionId || "")}`);
  const data = await res.json();

  if (!data.success) {
    alert(data.error || "Không chạy được AND-OR Search HGL02.");
    return;
  }

  state.dungeon.result = data;
  openDungeonOverlay();

  const log = $("dungeonLog");
  log.innerHTML = "";
  log.innerHTML += `<li><b>AND-OR Search</b><small>Start = H01, Goal = H58. OR_SEARCH chọn action; AND_SEARCH kiểm tra result_states. Node và đường kỹ thuật đang được ẩn.</small></li>`;

  (data.trace || []).slice(0, 80).forEach((step, idx) => {
    const li = document.createElement("li");
    li.innerHTML = `<b>${idx + 1}. ${step.type}</b><small>${step.message || ""}</small>`;
    log.appendChild(li);
  });

  updateDungeonStats(data.session_id, 1, "H01");
  $("dungeonStatus").textContent = data.found
    ? `✅ AND-OR tìm được plan tới H58. Số bước: ${data.path_nodes.length - 1}.`
    : "❌ AND-OR không tìm được plan tới H58.";

  drawHgl02Map(data.map);
  await moveHgl02PlayerPath(data.path_nodes, data.map);

  if (data.found) {
    await sleep(1000);
    closeDungeonOverlay();
  }

  // Nếu HGL02 được mở từ route chính, đóng overlay rồi mới cho nhân vật tiếp tục.
  if (state.dungeon?.triggeredFromMain) {
    $("mapSubtitle").textContent = "HGL02 đã hoàn tất. Nhân vật thoát khỏi hầm ngục và quay lại bản đồ chính để đi tiếp.";
    await sleep(720);
    closeDungeonOverlay();
  }

}
async function enterDungeon() {
  setDungeonOverlayMode("HGL02");
  openDungeonOverlay();

  const res = await fetch("/api/hgl02/new");
  const data = await res.json();

  if (!data.success) {
    alert(data.error || "Không tạo được HGL02.");
    return;
  }

  state.dungeon.sessionId = data.session_id;
  state.dungeon.map = data.map;
  state.dungeon.customMap = null;
  state.dungeon.result = null;
  state.dungeon.stepIndex = 0;
  state.dungeon.animating = false;
  state.dungeon.editMode = false;
  state.dungeon.selectedNodes = [];

  drawHgl02Map(data.map);
  drawHgl02PlayerAt("H01", data.map);
  updateDungeonStats(data.session_id, 1, "H01");
  $("dungeonStatus").textContent =
    "HGL02 đã nạp sẵn tọa độ: H01 là điểm bắt đầu, H58 là đích. Node và đường kỹ thuật đã được ẩn.";
  $("dungeonLog").innerHTML =
    `<li><b>Map HGL02 cố định</b><small>Đã nạp ${Object.keys(data.map.nodes || {}).length} node và ${(data.map.edges || []).length} cạnh. Start = H01, Goal = H58. Node/đường đi được ẩn, chỉ hiện nhân vật di chuyển.</small></li>`;
}

async function solveDungeon() {
  await solveHgl02AndorDungeon();
}

async function solveHgl02CustomDungeon() {
  await solveHgl02AndorDungeon();
}

async function animateDungeonSteps(result) {
  if (!result.steps || !result.steps.length) return;

  openDungeonOverlay();
  state.dungeon.animating = true;

  const log = $("dungeonLog");
  log.innerHTML = "";

  for (let i = 0; i < result.steps.length; i++) {
    const step = result.steps[i];
    const route = result.steps.slice(0, i + 1)
      .flatMap(s => s.belief || [])
      .filter((value, index, arr) => arr.indexOf(value) === index);

    drawHgl02Map(result.map, {
      belief: step.belief || [],
      route
    });

    updateDungeonStats(result.session_id, step.possible_count, step.action || "START");

    const li = document.createElement("li");
    li.innerHTML = `<b>${i + 1}. ${step.action ? "Action " + step.action : "Khởi tạo belief"}</b><small>${step.message}</small>`;
    log.appendChild(li);
    log.scrollTop = log.scrollHeight;

    $("dungeonStatus").textContent = step.message;
    await sleep(430);
  }

  $("dungeonStatus").textContent = result.found
    ? `✅ Belief đã hội tụ về EXIT. Chuỗi action: ${result.actions.join(" → ")}`
    : "❌ Belief chưa hội tụ được về EXIT. Hãy chỉnh node/cạnh hoặc đặt Start/Exit rõ hơn.";

  state.dungeon.animating = false;

  if (result.found) {
    await sleep(1200);
    closeDungeonOverlay();
  }
}

async function triggerDungeonFromMainRoute() {
  state.dungeon ??= {};
  if (state.dungeon.triggeredFromMain) return;
  state.dungeon.triggeredFromMain = true;

  $("mapSubtitle").textContent =
    "Nhân vật đi ngang qua HGL02 → mở hầm ngục AND-OR. Start = H01, Goal = H58.";

  await enterDungeon();

  $("mapSubtitle").textContent =
    "HGL02 đã nạp tọa độ cố định. Bấm Chạy AND-OR Search HGL02 để nhân vật di chuyển.";

  // Khi đang đi trên route lớn, phải dừng lại ở cửa HGL02.
  // Chỉ sau khi chạy xong / đóng overlay mới tiếp tục đi tiếp.
  await waitForHgl02DungeonCloseIfNeeded();
}

function drawDun02Map(mapData, options = {}) {
  if (!mapData || !$("dun02Svg")) return;

  const svg = $("dun02Svg");
  const bg = $("dun02Bg");
  const edgeLayer = $("dun02EdgeLayer");
  const decoLayer = $("dun02DecoLayer");
  const routeLayer = $("dun02RouteLayer");
  const nodeLayer = $("dun02NodeLayer");

  svg.setAttribute("viewBox", `0 0 ${mapData.width} ${mapData.height}`);
  if (bg) {
    bg.setAttribute("href", mapData.image);
    bg.setAttribute("width", mapData.width);
    bg.setAttribute("height", mapData.height);
  }

  edgeLayer.innerHTML = "";
  decoLayer.innerHTML = "";
  routeLayer.innerHTML = "";
  nodeLayer.innerHTML = "";

  const nodes = mapData.nodes || {};
  const selectedSet = new Set(options.selected || []);
  const route = options.route || [];
  const routePairs = new Set();

  for (let i = 0; i < route.length - 1; i++) {
    routePairs.add(`${route[i]}-${route[i + 1]}`);
    routePairs.add(`${route[i + 1]}-${route[i]}`);
  }

  (mapData.edges || []).forEach(edge => {
    const [a, b] = edge;
    if (!nodes[a] || !nodes[b]) return;

    edgeLayer.appendChild(svgEl("line", {
      x1: nodes[a].x,
      y1: nodes[a].y,
      x2: nodes[b].x,
      y2: nodes[b].y,
      class: routePairs.has(`${a}-${b}`) ? "dun02-edge route" : "dun02-edge"
    }));
  });

  if (route.length > 1) {
    for (let i = 0; i < route.length - 1; i++) {
      const a = nodes[route[i]];
      const b = nodes[route[i + 1]];
      if (!a || !b) continue;
      routeLayer.appendChild(svgEl("line", {
        x1: a.x,
        y1: a.y,
        x2: b.x,
        y2: b.y,
        class: "dun02-edge route"
      }));
    }
  }

  Object.entries(nodes).forEach(([id, n]) => {
    const cls = ["dun02-node", n.kind || "normal"];
    if (selectedSet.has(id)) cls.push("selected");
    if (options.currentNode === id) cls.push("current");

    const g = svgEl("g", {
      class: cls.join(" "),
      transform: `translate(${n.x}, ${n.y})`,
      "data-dun02-node": id
    });

    g.appendChild(svgEl("circle", { r: 12 }));
    g.appendChild(svgEl("text", { x: 0, y: -18 }, id));

    g.addEventListener("click", (evt) => {
      evt.stopPropagation();
    });

    nodeLayer.appendChild(g);
  });
}

function drawDun02PlayerAt(nodeId, mapData) {
  const layer = $("dun02PlayerLayer");
  if (!layer || !mapData?.nodes?.[nodeId]) return;
  layer.innerHTML = "";

  const n = mapData.nodes[nodeId];
  const g = svgEl("g", { class: "dun02-player", id: "dun02Player", transform: `translate(${n.x}, ${n.y})` });
  g.appendChild(svgEl("ellipse", { class: "dun02-player-shadow", cx: 0, cy: 18, rx: 18, ry: 7 }));
  g.appendChild(svgEl("circle", { class: "dun02-player-body", cx: 0, cy: 0, r: 16 }));
  g.appendChild(svgEl("path", { class: "dun02-player-hood", d: "M -12 -8 L 0 -28 L 12 -8 Z" }));
  g.appendChild(svgEl("text", { class: "dun02-player-label", x: 0, y: -34 }, nodeId));
  layer.appendChild(g);
}

async function moveDun02PlayerPath(pathNodes, mapData) {
  if (!pathNodes?.length || !mapData) return;

  drawDun02PlayerAt(pathNodes[0], mapData);
  let player = $("dun02Player");
  if (!player) return;

  for (let i = 1; i < pathNodes.length; i++) {
    const from = mapData.nodes[pathNodes[i - 1]];
    const to = mapData.nodes[pathNodes[i]];
    if (!from || !to) continue;

    const frames = 22;
    for (let f = 1; f <= frames; f++) {
      const t = f / frames;
      const bob = Math.sin(t * Math.PI) * 5;
      const x = from.x + (to.x - from.x) * t;
      const y = from.y + (to.y - from.y) * t - bob;
      player.setAttribute("transform", `translate(${x}, ${y})`);
      await sleep(18);
    }

    drawDun02PlayerAt(pathNodes[i], mapData);
    player = $("dun02Player");
    updateDungeonStats(state.dun02Dungeon?.sessionId || "--", i + 1, pathNodes[i]);
  }
}


function cloneDun02CurrentMap(mapData) {
  return JSON.parse(JSON.stringify(mapData));
}

function activeDun02DungeonMap() {
  return state.dun02Dungeon?.customMap || state.dun02Dungeon?.map;
}

function ensureDun02CustomMap(clear = false) {
  state.dun02Dungeon ??= {};
  if (!state.dun02Dungeon.map) return null;

  if (!state.dun02Dungeon.customMap || clear) {
    state.dun02Dungeon.customCounter = 1;
    state.dun02Dungeon.customMap = {
      image: state.dun02Dungeon.map.image,
      width: state.dun02Dungeon.map.width,
      height: state.dun02Dungeon.map.height,
      start: clear ? null : state.dun02Dungeon.map.start,
      key: clear ? null : state.dun02Dungeon.map.key,
      exit: clear ? null : state.dun02Dungeon.map.exit,
      nodes: clear ? {} : cloneDun02CurrentMap(state.dun02Dungeon.map.nodes || {}),
      edges: clear ? [] : cloneDun02CurrentMap(state.dun02Dungeon.map.edges || []),
      decorations: clear ? { blocked: [] } : cloneDun02CurrentMap(state.dun02Dungeon.map.decorations || {}),
    };
  }
  return state.dun02Dungeon.customMap;
}

function setDun02EditMode(enabled) {
  state.dun02EditMode = enabled;
  $("dungeonOverlay")?.classList.toggle("dun02-editing", enabled);
  if ($("dun02EditModeBtn")) $("dun02EditModeBtn").textContent = enabled ? "✓ Đang chỉnh node DUN02" : "✎ Bật chỉnh node DUN02";
  if (enabled) {
    ensureDun02CustomMap(false);
    $("dungeonStatus").textContent = "Đang bật chỉnh node DUN02. Click lên map để thêm node, hoặc click node có sẵn để chọn nối cạnh.";
  }
}

function dun02SvgPoint(evt) {
  const svg = $("dun02Svg");
  const pt = svg.createSVGPoint();
  pt.x = evt.clientX;
  pt.y = evt.clientY;
  return pt.matrixTransform(svg.getScreenCTM().inverse());
}

function nextDun02CustomNodeId(kind) {
  const m = ensureDun02CustomMap(false);
  if (kind === "start") return "DS";
  if (kind === "key") return "KEY";
  if (kind === "exit") return "EXIT";

  state.dun02Dungeon.customCounter ??= 1;
  let id = "";
  do {
    id = "U" + String(state.dun02Dungeon.customCounter).padStart(2, "0");
    state.dun02Dungeon.customCounter += 1;
  } while (m.nodes[id]);
  return id;
}

function dun02SelectCustomNode(id) {
  if (!state.dun02EditMode) return;
  const arr = state.dun02Dungeon.selectedNodes || [];
  if (arr.includes(id)) {
    state.dun02Dungeon.selectedNodes = arr.filter(x => x !== id);
  } else {
    state.dun02Dungeon.selectedNodes = [...arr, id].slice(-2);
  }
  drawDun02Map(activeDun02DungeonMap(), { selected: state.dun02Dungeon.selectedNodes });
}

function addDun02CustomNode(evt) {
  if (state.currentDungeonMode !== "DUN02" || !state.dun02EditMode) return;
  if (evt.target && evt.target.closest && evt.target.closest(".dun02-node")) return;
  evt.preventDefault?.();

  const m = ensureDun02CustomMap(false);
  if (!m) return;

  const p = dun02SvgPoint(evt);
  const kind = $("dun02NodeKind")?.value || "corridor";

  if (kind === "start" && m.start && m.nodes[m.start]) delete m.nodes[m.start];
  if (kind === "key" && m.key && m.nodes[m.key]) delete m.nodes[m.key];
  if (kind === "exit" && m.exit && m.nodes[m.exit]) delete m.nodes[m.exit];

  const id = nextDun02CustomNodeId(kind);
  const labelMap = {
    start: "Start",
    key: "KEY",
    exit: "EXIT",
    blocked: "Vật cản",
    trap: "Bẫy",
    dead_end: "Ngõ cụt",
    junction: "Ngã ba",
    corridor: "Hành lang",
  };

  m.nodes[id] = {
    label: labelMap[kind] || id,
    x: Math.round(p.x * 10) / 10,
    y: Math.round(p.y * 10) / 10,
    kind,
  };

  if (kind === "start") m.start = id;
  if (kind === "key") m.key = id;
  if (kind === "exit") m.exit = id;

  state.dun02Dungeon.selectedNodes = [id];
  drawDun02Map(m, { selected: state.dun02Dungeon.selectedNodes });
  $("dungeonStatus").textContent = `Đã thêm node ${id} tại x=${m.nodes[id].x}, y=${m.nodes[id].y}.`;
}

function connectDun02CustomNodes() {
  const m = ensureDun02CustomMap(false);
  const [a, b] = state.dun02Dungeon.selectedNodes || [];
  if (!a || !b || a === b) {
    alert("Hãy chọn đúng 2 node DUN02 để nối cạnh.");
    return;
  }

  m.edges ??= [];
  const exists = m.edges.some(e => (e[0] === a && e[1] === b) || (e[0] === b && e[1] === a));
  if (!exists) m.edges.push([a, b]);

  state.dun02Dungeon.selectedNodes = [];
  drawDun02Map(m);
  $("dungeonStatus").textContent = `Đã nối cạnh ${a} ↔ ${b}.`;
}

function clearDun02CustomNodes() {
  if (!state.dun02Dungeon?.map) return;
  ensureDun02CustomMap(true);
  state.dun02Dungeon.selectedNodes = [];
  setDun02EditMode(true);
  drawDun02Map(state.dun02Dungeon.customMap);
  $("dungeonStatus").textContent = "Đã xóa node mẫu DUN02. Hãy đặt Start, Key, Exit rồi nối cạnh.";
}

function undoDun02CustomNode() {
  const m = ensureDun02CustomMap(false);
  if (!m) return;

  const ids = Object.keys(m.nodes || {});
  const last = ids[ids.length - 1];
  if (!last) return;

  delete m.nodes[last];
  m.edges = (m.edges || []).filter(e => e[0] !== last && e[1] !== last);
  if (m.start === last) m.start = null;
  if (m.key === last) m.key = null;
  if (m.exit === last) m.exit = null;

  state.dun02Dungeon.selectedNodes = (state.dun02Dungeon.selectedNodes || []).filter(id => id !== last);
  drawDun02Map(m, { selected: state.dun02Dungeon.selectedNodes });
  $("dungeonStatus").textContent = `Đã undo node ${last}.`;
}

function exportDun02CustomCode() {
  const m = ensureDun02CustomMap(false);
  if (!m) return;

  const code = [
    "# DUN02 custom map",
    "nodes = " + JSON.stringify(m.nodes, null, 2),
    "edges = " + JSON.stringify(m.edges, null, 2),
    `start = ${JSON.stringify(m.start)}`,
    `key = ${JSON.stringify(m.key)}`,
    `exit = ${JSON.stringify(m.exit)}`,
  ].join("\n\n");

  if ($("dun02ExportBox")) $("dun02ExportBox").value = code;
  navigator.clipboard?.writeText(code).catch(() => {});
  $("dungeonStatus").textContent = "Đã xuất code DUN02. Có thể copy gửi lại để mình cố định vào app.py.";
}

async function runDun02CustomMap() {
  const m = activeDun02DungeonMap();
  if (!m) {
    alert("Chưa có map DUN02.");
    return;
  }

  const res = await fetch("/api/dun02/solve_custom", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      session_id: state.dun02Dungeon?.sessionId || "dun02-custom",
      map: m
    })
  });

  const data = await res.json();
  if (!data.success) {
    alert(data.error || "Không chạy được DUN02 custom.");
    return;
  }

  state.dun02Dungeon.result = data;
  await animateDun02BacktrackingTrace(data);
}


async function enterDun02Dungeon() {
  setDungeonOverlayMode("DUN02");
  openDungeonOverlay();

  const res = await fetch("/api/dun02/new");
  const data = await res.json();
  if (!data.success) {
    alert(data.error || "Không tạo được DUN02.");
    return;
  }

  state.dun02Dungeon ??= {};
  state.dun02Dungeon.sessionId = data.session_id;
  state.dun02Dungeon.map = data.map;
  state.dun02Dungeon.result = null;
  state.dun02Dungeon.animating = false;

  const startId = data.map.start || "DS";

  drawDun02Map(data.map);
  drawDun02PlayerAt(startId, data.map);
  updateDungeonStats(data.session_id, 1, startId);
  $("dungeonStatus").textContent =
    "DUN02 đã mở hầm ngục Backtracking + Forward Checking. Luật: đi từ Start, lấy KEY, rồi mới tới EXIT.";
  $("dungeonLog").innerHTML =
    `<li><b>Map DUN02 mới</b><small>Đã nạp ảnh hầm ngục mới, ${Object.keys(data.map.nodes || {}).length} node và ${(data.map.edges || []).length} cạnh. Thuật toán sẽ thử nhánh, cắt nhánh và quay lui.</small></li>`;
}


async function animateDun02BacktrackingTrace(data) {
  setDungeonOverlayMode("DUN02");
  openDungeonOverlay();

  const log = $("dungeonLog");
  log.innerHTML = "";

  const visited = [];
  const pruned = [];
  const backtracked = [];

  for (let i = 0; i < data.trace.length; i++) {
    const step = data.trace[i];

    if (step.type === "visit" && step.node && !visited.includes(step.node)) visited.push(step.node);
    if (step.type === "prune" && step.candidate && !pruned.includes(step.candidate)) pruned.push(step.candidate);
    if ((step.type === "backtrack" || step.type === "return") && step.node && !backtracked.includes(step.node)) backtracked.push(step.node);

    drawDun02Map(data.map, {
      currentNode: step.node || step.candidate,
      route: step.type === "success" ? data.path_nodes : []
    });

    updateDungeonStats(data.session_id, visited.length, step.type);
    $("dungeonStatus").textContent = step.message || step.reason || data.explanation;

    const titleMap = {
      visit: "Xét node",
      choose: "Thử nhánh",
      prune: "Forward Checking cắt nhánh",
      pickup_key: "Nhặt KEY",
      return: "Quay lui",
      backtrack: "Backtracking",
      success: "Thoát hầm ngục"
    };

    const li = document.createElement("li");
    li.innerHTML = `<b>${i + 1}. ${titleMap[step.type] || step.type}</b><small>${step.message || step.reason || ""}</small>`;
    log.appendChild(li);
    log.scrollTop = log.scrollHeight;

    await sleep(step.type === "success" ? 800 : 360);
  }

  drawDun02Map(data.map, { route: data.path_nodes, currentNode: data.exit });
  updateDungeonStats(data.session_id, data.nodes_expanded || visited.length, data.found ? "DONE" : "FAIL");
  $("dungeonStatus").textContent = data.found
    ? `✅ DUN02 hoàn tất. Route: ${data.path_nodes.join(" → ")}`
    : "❌ DUN02 chưa tìm ra lời giải.";

  if (data.found && data.path_nodes?.length) {
    await moveDun02PlayerPath(data.path_nodes, data.map);
  }
}


async function solveDun02BacktrackingDungeon() {
  if (!state.dun02Dungeon?.sessionId || !state.dun02Dungeon?.map) {
    await enterDun02Dungeon();
  }

  const res = await fetch("/api/dun02/solve", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ session_id: state.dun02Dungeon.sessionId })
  });
  const data = await res.json();

  if (!data.success) {
    alert(data.error || "Không chạy được Backtracking + Forward Checking DUN02.");
    return;
  }

  state.dun02Dungeon.result = data;
  await animateDun02BacktrackingTrace(data);

  if (data.found) {
    await sleep(900);
    closeDungeonOverlay();
  }
}

async function triggerDun02DungeonFromMainRoute() {
  state.dun02Dungeon ??= {};
  if (state.dun02Dungeon.triggeredFromMain) return;
  state.dun02Dungeon.triggeredFromMain = true;

  $("mapSubtitle").textContent =
    "Nhân vật đi ngang qua DUN02 → mở hầm ngục Backtracking + Forward Checking.";

  await enterDun02Dungeon();
  await solveDun02BacktrackingDungeon();

  $("mapSubtitle").textContent =
    "AI đã thoát khỏi hầm ngục DUN02, tiếp tục route chính.";
}




function cloneFb04Map(mapData) {
  return JSON.parse(JSON.stringify(mapData));
}

function ensureFb04CustomMap(clear = false) {
  state.fb04Dungeon ??= {};
  if (!state.fb04Dungeon.map) return null;
  if (!state.fb04Dungeon.customMap || clear) {
    state.fb04Dungeon.customCounter = 1;
    state.fb04Dungeon.selectedNodes = [];
    state.fb04Dungeon.customMap = {
      image: state.fb04Dungeon.map.image,
      width: state.fb04Dungeon.map.width,
      height: state.fb04Dungeon.map.height,
      start: null,
      exit: null,
      nodes: {},
      edges: [],
      decorations: { blocked: [] },
      custom: true
    };
  }
  return state.fb04Dungeon.customMap;
}

function activeFb04Map() {
  return state.fb04Dungeon?.customMap || state.fb04Dungeon?.map;
}

function setFb04EditMode(enabled) {
  state.fb04EditMode = enabled;
  $("dungeonOverlay")?.classList.toggle("fb04-editing", enabled);
  if ($("fb04EditModeBtn")) $("fb04EditModeBtn").textContent = enabled ? "✓ Đang chỉnh node FB04" : "✎ Bật chỉnh node FB04";
  if (enabled) ensureFb04CustomMap(false);
}

function fb04SvgPoint(evt) {
  const svg = $("fb04Svg");
  const m = activeFb04Map();
  if (!svg || !m) return { x: 0, y: 0 };
  try {
    const pt = svg.createSVGPoint();
    pt.x = evt.clientX;
    pt.y = evt.clientY;
    const converted = pt.matrixTransform(svg.getScreenCTM().inverse());
    return {
      x: Math.max(0, Math.min(m.width, converted.x)),
      y: Math.max(0, Math.min(m.height, converted.y)),
    };
  } catch (err) {
    const rect = svg.getBoundingClientRect();
    return {
      x: ((evt.clientX - rect.left) / rect.width) * m.width,
      y: ((evt.clientY - rect.top) / rect.height) * m.height,
    };
  }
}

function nextFb04NodeId(kind) {
  const m = ensureFb04CustomMap(false);
  if (kind === "exit") return "B_EXIT";
  if (kind === "start") {
    let idx = 1;
    let id = "BS" + String(idx).padStart(2, "0");
    while (m.nodes[id]) {
      idx++;
      id = "BS" + String(idx).padStart(2, "0");
    }
    return id;
  }
  state.fb04Dungeon.customCounter ??= 1;
  let id = "";
  do {
    id = "B" + String(state.fb04Dungeon.customCounter).padStart(2, "0");
    state.fb04Dungeon.customCounter += 1;
  } while (m.nodes[id]);
  return id;
}


function fb04PrimarySelectedNode() {
  const arr = state.fb04Dungeon?.selectedNodes || [];
  return arr.length ? arr[arr.length - 1] : null;
}

function updateFb04SelectedInfo() {
  const box = $("fb04SelectedInfo");
  if (!box) return;

  const id = fb04PrimarySelectedNode();
  const m = activeFb04Map();

  if (!id || !m?.nodes?.[id]) {
    box.textContent = "chưa chọn";
    return;
  }

  const n = m.nodes[id];
  box.textContent = `${id} | kind=${n.kind || "corridor"} | x=${n.x}, y=${n.y}`;
}

function setFb04SelectedKind(kind) {
  const m = ensureFb04CustomMap(false);
  const id = fb04PrimarySelectedNode();

  if (!m || !id || !m.nodes[id]) {
    alert("Hãy click chọn 1 node FB04 trước.");
    return;
  }

  // Nếu chuyển sang Exit thì chỉ giữ 1 Exit.
  if (kind === "exit") {
    if (m.exit && m.exit !== id && m.nodes[m.exit]) {
      m.nodes[m.exit].kind = "corridor";
      m.nodes[m.exit].label = m.nodes[m.exit].label || m.exit;
    }
    m.exit = id;
    m.nodes[id].label = "Exit";
  }

  // Có thể có nhiều Start để tạo belief ban đầu.
  if (kind === "start") {
    if (!m.start) m.start = id;
    m.nodes[id].label = "Start / Belief";
  }

  if (kind === "corridor") {
    if (m.start === id) {
      const otherStart = Object.entries(m.nodes).find(([nid, n]) => nid !== id && n.kind === "start");
      m.start = otherStart ? otherStart[0] : null;
    }
    if (m.exit === id) m.exit = null;
    m.nodes[id].label = "Hành lang";
  }

  m.nodes[id].kind = kind;

  drawFb04Map(m, { selected: state.fb04Dungeon.selectedNodes });
  updateFb04SelectedInfo();
  exportFb04Code();
  $("dungeonStatus").textContent = `Đã đổi ${id} thành ${kind === "start" ? "Start / Belief" : kind === "exit" ? "Exit" : "Hành lang"}.`;
}


function fb04SelectNode(id) {
  state.fb04Dungeon ??= {};
  const arr = state.fb04Dungeon.selectedNodes || [];

  if (arr.includes(id)) {
    state.fb04Dungeon.selectedNodes = arr.filter(x => x !== id);
  } else {
    state.fb04Dungeon.selectedNodes = [...arr, id].slice(-2);
  }

  drawFb04Map(activeFb04Map(), { selected: state.fb04Dungeon.selectedNodes });
  updateFb04SelectedInfo();
  exportFb04Code();
}

function addFb04CustomNode(evt) {
  if ((state.currentDungeonMode || "HGL02") !== "FB04") return;
  if (!state.fb04EditMode) setFb04EditMode(true);
  if (evt.target && evt.target.closest && evt.target.closest(".fb04-node")) return;
  evt.preventDefault?.();
  evt.stopPropagation?.();

  const m = ensureFb04CustomMap(false);
  const p = fb04SvgPoint(evt);
  const kind = $("fb04NodeKind")?.value || "corridor";
  if (kind === "exit" && m.exit && m.nodes[m.exit]) delete m.nodes[m.exit];

  const id = nextFb04NodeId(kind);
  const labelMap = {
    start: "Start / Belief",
    exit: "Exit",
    blocked: "Vật cản",
    dead_end: "Ngõ cụt",
    junction: "Ngã ba",
    corridor: "Hành lang",
  };

  m.nodes[id] = {
    label: labelMap[kind] || id,
    x: Math.round(p.x * 10) / 10,
    y: Math.round(p.y * 10) / 10,
    kind,
  };

  if (kind === "start" && !m.start) m.start = id;
  if (kind === "exit") m.exit = id;

  state.fb04Dungeon.selectedNodes = [id];
  drawFb04Map(m, { selected: state.fb04Dungeon.selectedNodes });
  updateFb04SelectedInfo();
  updateDungeonStats(state.fb04Dungeon?.sessionId || "--", Object.keys(m.nodes).length, id);
  exportFb04Code();
  $("dungeonStatus").textContent = `Đã thêm node ${id}: x=${m.nodes[id].x}, y=${m.nodes[id].y}.`;
}

function connectFb04SelectedNodes() {
  const m = ensureFb04CustomMap(false);
  const [a, b] = state.fb04Dungeon.selectedNodes || [];
  if (!a || !b || a === b) {
    alert("Hãy chọn đúng 2 node FB04 để nối cạnh.");
    return;
  }
  m.edges ??= [];
  const exists = m.edges.some(e => (e[0] === a && e[1] === b) || (e[0] === b && e[1] === a));
  if (!exists) m.edges.push([a, b]);
  state.fb04Dungeon.selectedNodes = [];
  drawFb04Map(m);
  exportFb04Code();
  $("dungeonStatus").textContent = `Đã nối cạnh ${a} ↔ ${b}.`;
}

function clearFb04Nodes() {
  ensureFb04CustomMap(true);
  drawFb04Map(state.fb04Dungeon.customMap);
  updateFb04SelectedInfo();
  updateDungeonStats(state.fb04Dungeon?.sessionId || "--", 0, "EDIT");
  if ($("fb04ExportBox")) $("fb04ExportBox").value = "";
  $("dungeonStatus").textContent = "Đã xóa tất cả node FB04. Hãy tự đặt Start/Exit và nối cạnh.";
}

function undoFb04Node() {
  const m = ensureFb04CustomMap(false);
  const ids = Object.keys(m.nodes || {});
  const last = ids[ids.length - 1];
  if (!last) return;
  delete m.nodes[last];
  m.edges = (m.edges || []).filter(e => e[0] !== last && e[1] !== last);
  if (m.start === last) m.start = null;
  if (m.exit === last) m.exit = null;
  state.fb04Dungeon.selectedNodes = (state.fb04Dungeon.selectedNodes || []).filter(id => id !== last);
  drawFb04Map(m, { selected: state.fb04Dungeon.selectedNodes });
  updateFb04SelectedInfo();
  exportFb04Code();
  $("dungeonStatus").textContent = `Đã undo node ${last}.`;
}

function exportFb04Code() {
  const m = ensureFb04CustomMap(false);
  if (!m) return;

  const nodes = m.nodes || {};
  const ids = Object.keys(nodes);

  const coordLines = ids.map((id, idx) => {
    const n = nodes[id];
    const xp = m.width ? (n.x / m.width * 100).toFixed(2) : "0.00";
    const yp = m.height ? (n.y / m.height * 100).toFixed(2) : "0.00";
    return `${idx + 1}. ${id} | ${n.kind || "corridor"} | x=${n.x}, y=${n.y} | x%=${xp}, y%=${yp}`;
  });

  const nodeLines = ids.map((id) => {
    const n = nodes[id];
    const xp = m.width ? (n.x / m.width * 100).toFixed(2) : "0.00";
    const yp = m.height ? (n.y / m.height * 100).toFixed(2) : "0.00";
    return `"${id}": {"label": "${n.label || id}", "x": ${n.x}, "y": ${n.y}, "x_percent": ${xp}, "y_percent": ${yp}, "kind": "${n.kind || "corridor"}"}`;
  });

  const code = [
    "===== DANH SÁCH TỌA ĐỘ ĐÃ ĐẶT =====",
    `Tổng node: ${ids.length}`,
    `Start chính: ${m.start || "chưa đặt"} | Các Start belief: ${ids.filter(id => nodes[id].kind === "start").join(", ") || "chưa có"}`,
    `Exit: ${m.exit || "chưa đặt"}`,
    "",
    coordLines.join("\\n") || "Chưa có node nào.",
    "",
    "===== CODE NODES/EDGES =====",
    "# FB04 BELIEF BFS NODE COORDINATES",
    `# Image size: ${m.width} x ${m.height}`,
    "",
    "nodes = {",
    nodeLines.map(line => "    " + line + ",").join("\\n"),
    "}",
    "",
    "edges = " + JSON.stringify(m.edges || [], null, 2),
    "",
    `start = ${JSON.stringify(m.start)}`,
    `exit = ${JSON.stringify(m.exit)}`
  ].join("\\n");

  if ($("fb04ExportBox")) $("fb04ExportBox").value = code;
}

function drawFb04Map(mapData, options = {}) {
  if (!mapData || !$("fb04Svg")) return;
  const svg = $("fb04Svg");
  const bg = $("fb04Bg");
  const edgeLayer = $("fb04EdgeLayer");
  const routeLayer = $("fb04RouteLayer");
  const nodeLayer = $("fb04NodeLayer");

  svg.setAttribute("viewBox", `0 0 ${mapData.width} ${mapData.height}`);
  bg.setAttribute("href", mapData.image);
  bg.setAttribute("width", mapData.width);
  bg.setAttribute("height", mapData.height);

  edgeLayer.innerHTML = "";
  routeLayer.innerHTML = "";
  nodeLayer.innerHTML = "";

  const nodes = mapData.nodes || {};
  const belief = new Set(options.belief || []);
  const selected = new Set(options.selected || []);
  const actualRoute = options.actualRoute || [];
  const beliefSegments = options.beliefSegments || [];
  const fog = !!options.fog;

  (mapData.edges || []).forEach(([a, b]) => {
    if (!nodes[a] || !nodes[b]) return;
    edgeLayer.appendChild(svgEl("line", {
      x1: nodes[a].x, y1: nodes[a].y,
      x2: nodes[b].x, y2: nodes[b].y,
      class: fog ? "fb04-edge fb04-fog-edge" : "fb04-edge"
    }));
  });

  // Route của belief: nét tím đứt để thấy tập niềm tin dịch chuyển thế nào.
  beliefSegments.forEach((seg) => {
    const a = nodes[seg.from], b = nodes[seg.to];
    if (!a || !b) return;
    routeLayer.appendChild(svgEl("line", {
      x1: a.x, y1: a.y,
      x2: b.x, y2: b.y,
      class: "fb04-edge fb04-belief-route"
    }));
  });

  // Route của nhân vật thật: nét xanh rõ, vẽ chồng lên trên belief.
  if (actualRoute.length > 1) {
    for (let i = 1; i < actualRoute.length; i++) {
      const a = nodes[actualRoute[i - 1]], b = nodes[actualRoute[i]];
      if (!a || !b) continue;
      routeLayer.appendChild(svgEl("line", {
        x1: a.x, y1: a.y,
        x2: b.x, y2: b.y,
        class: "fb04-edge fb04-route"
      }));
    }
  }

  Object.entries(nodes).forEach(([id, n]) => {
    // Khi chạy thật: chỉ hiện dấu ? cho các node thuộc belief hiện tại.
    if (options.hideNonBeliefNodes && fog && !belief.has(id)) return;

    const cls = ["fb04-node", n.kind || "normal"];
    if (belief.has(id)) cls.push("belief");
    if (selected.has(id)) cls.push("selected");
    if (options.currentNode === id) cls.push("current");
    if (fog) cls.push("fog");

    const g = svgEl("g", { class: cls.join(" "), transform: `translate(${n.x}, ${n.y})` });

    if (fog) {
      const isBelief = belief.has(id);
      const isExit = id === mapData.exit && isBelief;
      g.appendChild(svgEl("circle", { r: isBelief ? 12 : 8 }));
      g.appendChild(svgEl("text", { x: 0, y: 5 }, isExit ? "✓" : "?"));
    } else {
      g.appendChild(svgEl("circle", { r: id === mapData.exit ? 17 : 12 }));
      g.appendChild(svgEl("text", { x: 0, y: -18 }, id));
    }

    g.addEventListener("click", (evt) => {
      evt.stopPropagation();
      fb04SelectNode(id);
    });
    nodeLayer.appendChild(g);
  });
}

function buildFb04BeliefSegments(prevBelief, curBelief) {
  const fromList = [...(prevBelief || [])].sort();
  const toList = [...(curBelief || [])].sort();
  const segs = [];
  const count = Math.max(fromList.length, toList.length);
  for (let i = 0; i < count; i++) {
    const from = fromList[Math.min(i, fromList.length - 1)];
    const to = toList[Math.min(i, toList.length - 1)];
    if (!from || !to) continue;
    segs.push({ from, to });
  }
  return segs;
}

function drawFb04PlayerAt(nodeId, mapData) {
  const layer = $("fb04PlayerLayer");
  if (!layer) return;

  layer.innerHTML = "";

  if (!nodeId || !mapData?.nodes?.[nodeId]) return;

  const n = mapData.nodes[nodeId];
  const g = svgEl("g", {
    class: "fb04-player",
    transform: `translate(${n.x}, ${n.y})`
  });

  g.appendChild(svgEl("ellipse", {
    class: "fb04-player-shadow",
    cx: 0,
    cy: 16,
    rx: 16,
    ry: 6
  }));

  g.appendChild(svgEl("circle", {
    class: "fb04-player-body",
    cx: 0,
    cy: 0,
    r: 12
  }));

  g.appendChild(svgEl("path", {
    class: "fb04-player-hood",
    d: "M -9 -6 L 0 -20 L 9 -6 Z"
  }));

  layer.appendChild(g);
}

async function enterFb04Dungeon() {
  setDungeonOverlayMode("FB04");
  openDungeonOverlay();

  const res = await fetch("/api/fb04/new");
  const data = await res.json();

  if (!data.success) {
    alert(data.error || "Không tạo được FB04.");
    return;
  }

  state.fb04Dungeon.sessionId = data.session_id;
  state.fb04Dungeon.map = data.map;
  state.fb04Dungeon.customMap = data.map;
  state.fb04Dungeon.selectedNodes = [];
  state.fb04Dungeon.result = null;
  state.fb04Dungeon.actualStart = data.actual_start || null;

  // Chạy thật: chưa vẽ đường sẵn trên map; chỉ hiện nhân vật thật và các dấu ? belief ban đầu.
  drawFb04Map(data.map, { fog: true, hideNonBeliefNodes: true, belief: data.belief || [], actualRoute: [], beliefSegments: [] });
  drawFb04PlayerAt(state.fb04Dungeon.actualStart, data.map);

  updateDungeonStats(data.session_id, (data.belief || []).length, "INIT");
  $("dungeonStatus").textContent = "FB04 sẵn sàng. Khi chạy, đường xanh sẽ là đường nhân vật thật và đường tím sẽ là quá trình belief dịch chuyển.";
  $("dungeonLog").innerHTML =
    `<li><b>FB04 Belief</b><small>Belief ban đầu = {(data.belief || []).join(", ")}. Start thật lần này được chọn ngẫu nhiên. Bấm nút chạy để xem BFS hội tụ về B55 qua B51 → B52 → B53 → B54.</small></li>`;
}


function fb04ActualMoveLabel(prevNode, currentNode) {
  if (!prevNode || !currentNode) return "MOVE";
  if (prevNode === currentNode) return `Đứng yên tại ${currentNode}`;
  return `Di chuyển ${prevNode} → ${currentNode}`;
}

async function solveFb04BeliefBfsDungeon() {
  if (!state.fb04Dungeon?.sessionId || !state.fb04Dungeon?.map) {
    await enterFb04Dungeon();
  }

  const m = activeFb04Map();
  const res = await fetch("/api/fb04/solve", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ session_id: state.fb04Dungeon.sessionId, map: m, actual_start: state.fb04Dungeon.actualStart })
  });
  const data = await res.json();

  if (!data.success) {
    alert(data.error || "Không chạy được Belief State + BFS FB04.");
    return;
  }

  state.fb04Dungeon.result = data;
  setDungeonOverlayMode("FB04");
  openDungeonOverlay();

  const log = $("dungeonLog");
  log.innerHTML = "";
  log.innerHTML += `<li><b>Belief State + BFS</b><small>Đường xanh = đường nhân vật thật. Đường tím = sự dịch chuyển của tập belief. Nếu belief hội tụ về EXIT thì thoát hầm ngục.</small></li>`;

  const cumulativeBeliefSegments = [];
  for (const step of data.steps || []) {
    const actualPath = data.actual_path || [];
    const actualNode = actualPath[step.step] || data.actual_start || data.exit;
    const prevActualNode = step.step > 0 ? (actualPath[step.step - 1] || data.actual_start) : null;
    const moveLabel = step.step === 0 ? `Bắt đầu tại ${actualNode}` : fb04ActualMoveLabel(prevActualNode, actualNode);
    const prevBelief = step.step > 0 && data.steps?.[step.step - 1] ? data.steps[step.step - 1].belief || [] : [];
    const curBelief = step.belief || [];

    if (step.step > 0) {
      cumulativeBeliefSegments.push(...buildFb04BeliefSegments(prevBelief, curBelief));
    }
    const currentActualRoute = actualPath.slice(0, step.step + 1);

    // Chỉ vẽ đường thực tế và đường belief động theo từng bước, không dùng route vẽ sẵn trong map nữa.
    drawFb04Map(data.map, {
      fog: true,
      hideNonBeliefNodes: true,
      belief: curBelief,
      actualRoute: currentActualRoute,
      beliefSegments: cumulativeBeliefSegments,
      currentNode: actualNode
    });
    drawFb04PlayerAt(actualNode, data.map);

    updateDungeonStats(data.session_id, step.possible_count, moveLabel);
    $("dungeonStatus").textContent =
      `${moveLabel} | Belief còn ${step.possible_count} khả năng | Start thật: ${data.actual_start}`;

    const li = document.createElement("li");
    const beliefText = step.step === 0
      ? `Belief khởi tạo: {${curBelief.join(", ")}}`
      : `Belief: {${prevBelief.join(", ")}} → {${curBelief.join(", ")}}`;
    li.innerHTML = `<b>${step.step}. ${moveLabel}</b><small>${beliefText}</small>`;
    log.appendChild(li);
    log.scrollTop = log.scrollHeight;
    await sleep(520);
  }

  $("dungeonStatus").textContent = data.found
    ? `✅ FB04 hoàn tất. Actual đã tới B55 và belief hội tụ về {B55}. Đoạn cuối đi qua B51 → B52 → B53 → B54 → B55.`
    : "❌ FB04 chưa tìm được chuỗi action làm belief hội tụ về EXIT.";

  // Nếu FB04 được mở từ route chính, đóng overlay rồi mới cho nhân vật tiếp tục.
  if (state.fb04Dungeon?.triggeredFromMain) {
    $("mapSubtitle").textContent = data.found
      ? "FB04 đã hoàn tất. Nhân vật thoát khỏi hầm ngục và quay lại bản đồ chính để đi tiếp."
      : "FB04 kết thúc. Nhân vật quay lại bản đồ chính.";
    await sleep(720);
    closeDungeonOverlay();
  }
}

async function triggerFb04DungeonFromMainRoute() {
  state.fb04Dungeon ??= {};
  state.fb04Dungeon.triggeredFromMain = true;

  $("mapSubtitle").textContent =
    "Nhân vật đi ngang qua FB04 sân bóng → mở hầm ngục Belief State + BFS.";

  await enterFb04Dungeon();

  $("mapSubtitle").textContent =
    "FB04 đã sẵn sàng. Bấm nút Chạy thuật toán hầm ngục để bắt đầu Belief State + BFS.";

  // Khi đang đi trên route lớn, phải dừng lại ở cửa FB04.
  // Chỉ sau khi chạy xong / đóng overlay mới tiếp tục đi tiếp,
  // tránh tình trạng vừa xong sân bóng là nhảy thẳng sang hầm khác.
  await waitForFb04DungeonCloseIfNeeded();
}



async function bossFetchJson(url) {
  const res = await fetch(url);
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch (err) {
    throw new Error(`Boss API không trả JSON. Hãy tắt server cũ và chạy lại python app.py. URL: ${url}`);
  }
}

// =========================
// Final Boss - Dragon Minimax
// =========================
const bossState = {
  sessionId: null,
  data: null,
  autoRunning: false
};

function openBossOverlay() {
  $("bossOverlay")?.classList.remove("hidden");
}

function closeBossOverlay() {
  $("bossOverlay")?.classList.add("hidden");
}

function bossCellCenter(cellId) {
  const cell = document.querySelector(`.boss-cell[data-cell="${cellId}"]`);
  const wrap = $("bossBoardWrap") || document.querySelector(".boss-board-wrap");
  const base = wrap?.getBoundingClientRect();
  if (!cell || !base) return { x: 0, y: 0 };
  const r = cell.getBoundingClientRect();
  return {
    x: r.left - base.left + r.width / 2,
    y: r.top - base.top + r.height / 2
  };
}

function bossDragonCenter() {
  // Ảnh nền đã có rồng. Lấy điểm xuất phát fireball gần miệng rồng trong ảnh.
  const wrap = $("bossBoardWrap") || document.querySelector(".boss-board-wrap");
  const base = wrap?.getBoundingClientRect();
  if (!base) return { x: 0, y: 0 };
  return {
    x: base.width * 0.505,
    y: base.height * 0.205
  };
}

function drawBossBoard(data) {
  const board = $("bossBoard");
  if (!board || !data) return;

  const burned = new Set(data.burned || []);
  const valid = new Set(data.valid_moves || []);
  board.innerHTML = "";
  board.style.gridTemplateColumns = `repeat(${data.size}, 1fr)`;
  board.style.gridTemplateRows = `repeat(${data.size}, 1fr)`;

  for (let r = 0; r < data.size; r++) {
    for (let c = 0; c < data.size; c++) {
      const id = `${r}-${c}`;
      const cell = document.createElement("button");
      cell.className = "boss-cell";
      cell.type = "button";
      cell.dataset.cell = id;
      cell.dataset.coord = `${String.fromCharCode(65 + r)}${c + 1}`;

      if (burned.has(id)) cell.classList.add("burned");
      if (valid.has(id) && data.status === "playing") cell.classList.add("valid");
      if (id === data.dragon) cell.classList.add("goal");

      cell.innerHTML = `<span class="cell-id">${cell.dataset.coord}</span>`;

      if (burned.has(id)) {
        const burnMark = document.createElement("span");
        burnMark.className = "boss-burn-mark";
        cell.appendChild(burnMark);

        const burnFire = document.createElement("span");
        burnFire.className = "boss-burn-fire";
        burnFire.setAttribute("aria-hidden", "true");
        cell.appendChild(burnFire);
      }

      if (id === data.knight) {
        const k = document.createElement("span");
        k.className = "boss-token knight";
        k.textContent = "🛡️";
        cell.appendChild(k);
      }

      if (id === data.dragon) {
        const crown = document.createElement("span");
        crown.className = "boss-goal-mark";
        crown.textContent = "👑";
        cell.appendChild(crown);
      }

      cell.addEventListener("click", () => {
        if (!valid.has(id) || data.status !== "playing") return;
        bossStep(id).catch(err => alert(err.message));
      });

      board.appendChild(cell);
    }
  }

  $("bossSession").textContent = data.session_id || "--";
  $("bossTurn").textContent = String(data.turn ?? 0);
  $("bossStatus").textContent =
    data.status === "finished"
      ? (data.winner === "knight" ? "Knight thắng" : "Dragon thắng")
      : "Đang chiến đấu";

  const log = $("bossLog");
  if (log) {
    log.innerHTML = "";
    (data.log || []).slice(-12).forEach((line, idx) => {
      const li = document.createElement("li");
      li.innerHTML = `<b>${idx + 1}.</b><small>${line}</small>`;
      log.appendChild(li);
    });
    log.scrollTop = log.scrollHeight;
  }
}

async function animateBossFire(targetCellId) {
  const fire = $("bossFireball");
  if (!fire || !targetCellId) return;

  const start = bossDragonCenter();
  const end = bossCellCenter(targetCellId);
  const fireW = fire.offsetWidth || 40;
  const fireH = fire.offsetHeight || 52;

  fire.classList.remove("hidden");
  fire.style.opacity = "1";
  fire.style.transform = `translate(${start.x - fireW / 2}px, ${start.y - fireH / 2}px) scale(.72)`;

  await sleep(30);

  fire.style.transform = `translate(${end.x - fireW / 2}px, ${end.y - fireH / 2}px) scale(1.08)`;
  await sleep(650);

  const target = document.querySelector(`.boss-cell[data-cell="${targetCellId}"]`);
  target?.classList.add("impact");
  await sleep(180);
  target?.classList.remove("impact");

  fire.style.opacity = "0";
  await sleep(220);
  fire.classList.add("hidden");
  fire.style.opacity = "1";
}

async function newBossGame() {
  const data = await bossFetchJson("/api/boss/new");
  if (!data.success) {
    alert(data.error || "Không tạo được boss.");
    return;
  }
  bossState.sessionId = data.session_id;
  bossState.data = data;
  openBossOverlay();
  drawBossBoard(data);
}

async function bossStep(moveId = null) {
  if (!bossState.sessionId) await newBossGame();

  const prev = bossState.data;
  const qs = new URLSearchParams({ session_id: bossState.sessionId });
  if (moveId) qs.set("move", moveId);

  const data = await bossFetchJson(`/api/boss/step?${qs.toString()}`);
  if (!data.success) {
    alert(data.error || "Boss step lỗi.");
    return;
  }

  // Pha 1: Knight di chuyển trước.
  if (prev && data.last_knight_to) {
    const phase1 = { ...prev, knight: data.last_knight_to, turn: data.turn, log: [...(prev.log || []), `Knight tiến tới ${data.last_knight_to}.`] };
    drawBossBoard(phase1);
    await sleep(280);
  }

  // Pha 2: Dragon phun lửa từ tổ rồng tới ô mục tiêu.
  if (data.last_fire) {
    await animateBossFire(data.last_fire);
  }

  bossState.data = data;
  drawBossBoard(data);
}

async function autoRunBoss() {
  if (!bossState.sessionId) await newBossGame();
  bossState.autoRunning = true;

  while (bossState.autoRunning && bossState.data?.status === "playing") {
    await bossStep(null);
    await sleep(1050);
  }
}

async function triggerBossFinalFromTreasure() {
  openBossOverlay();
  await newBossGame();
}


function enableBossQuickTestClick() {
  // Cho phép test boss nhanh bằng cách click kho báu/GOAL trên map chính.
  const goalNode = document.querySelector('[data-node-id="GOAL"], [data-id="GOAL"]');
  goalNode?.addEventListener("click", () => {
    state.bossFinalTriggered = true;
    triggerBossFinalFromTreasure().catch(err => alert(err.message));
  });
}

function bindEvents() {
  setTimeout(enableBossQuickTestClick, 500);
  $("bossNewBtn")?.addEventListener("click", () => newBossGame().catch(err => alert(err.message)));
  $("bossAutoBtn")?.addEventListener("click", () => autoRunBoss().catch(err => alert(err.message)));
  $("closeBossBtn")?.addEventListener("click", closeBossOverlay);

  $("fb04SetStartBtn")?.addEventListener("click", () => setFb04SelectedKind("start"));
  $("fb04SetExitBtn")?.addEventListener("click", () => setFb04SelectedKind("exit"));
  $("fb04SetCorridorBtn")?.addEventListener("click", () => setFb04SelectedKind("corridor"));

  $("runBtn").addEventListener("click", () => runSearch().catch(err => alert(err.message)));
  $("animateBtn").addEventListener("click", animatePlayer);
  $("compareBtn").addEventListener("click", () => compareAll().catch(err => alert(err.message)));
  $("resetBtn").addEventListener("click", resetGame);

  $("closeDungeonBtn")?.addEventListener("click", closeDungeonOverlay);
  $("hgl02SolveFixedBtn")?.addEventListener("click", () => {
    const mode = state.currentDungeonMode || "HGL02";
    const runner =
      mode === "DUN02" ? solveDun02BacktrackingDungeon :
      mode === "FB04" ? solveFb04BeliefBfsDungeon :
      solveHgl02AndorDungeon;
    runner().catch(err => alert(err.message));
  });
  $("hgl02ResetViewBtn")?.addEventListener("click", () => {
    const mode = state.currentDungeonMode || "HGL02";
    if (mode === "DUN02") {
      const m = activeDun02DungeonMap();
      if (m) {
        drawDun02Map(m);
        drawDun02PlayerAt(m.start || "DS", m);
        updateDungeonStats(state.dun02Dungeon?.sessionId || "--", 1, m.start || "DS");
        $("dungeonStatus").textContent = "Đã làm mới hiển thị DUN02. Node và cạnh đang hiện để chỉnh đường đi.";
      }
      return;
    }

    if (state.dungeon.map) {
      drawHgl02Map(state.dungeon.map);
      drawHgl02PlayerAt(dungeonStartId(state.dungeon.map), state.dungeon.map);
      updateDungeonStats(state.dungeon.sessionId || "--", 1, dungeonStartId(state.dungeon.map));
      $("dungeonStatus").textContent = "Đã làm mới hiển thị HGL02.";
    }
  });
  $("closeAndorBtn")?.addEventListener("click", closeAndorOverlay);

  $("showEdges").addEventListener("change", drawGraph);
  $("showLabels").addEventListener("change", drawGraph);

  $("zoomIn").addEventListener("click", () => zoomAt(1.22));
  $("zoomOut").addEventListener("click", () => zoomAt(0.82));
  $("resetView").addEventListener("click", resetView);

  const svg = $("gameSvg");
  svg.addEventListener("wheel", (evt) => {
    evt.preventDefault();
    const p = getSvgPoint(evt);
    zoomAt(evt.deltaY < 0 ? 1.15 : 0.87, p.x, p.y);
  }, { passive: false });

  svg.addEventListener("mousedown", (evt) => {
    state.dragging = true;
    state.moved = false;
    state.dragStart = { x: evt.clientX, y: evt.clientY };
    state.vbStart = { ...state.viewBox };
    svg.classList.add("dragging");
  });

  window.addEventListener("mousemove", (evt) => {
    if (!state.dragging) return;
    const rect = svg.getBoundingClientRect();
    const dx = evt.clientX - state.dragStart.x;
    const dy = evt.clientY - state.dragStart.y;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) state.moved = true;
    state.viewBox = clampViewBox({
      x: state.vbStart.x - dx * state.vbStart.w / rect.width,
      y: state.vbStart.y - dy * state.vbStart.h / rect.height,
      w: state.vbStart.w,
      h: state.vbStart.h
    });
    applyViewBox();
  });

  window.addEventListener("mouseup", () => {
    if (!state.dragging) return;
    state.dragging = false;
    svg.classList.remove("dragging");
  });
}

init().catch(err => {
  console.error(err);
  alert("Không tải được graph từ Python backend. Hãy chạy: python app.py");
});