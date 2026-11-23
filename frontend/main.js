import { API_URL } from "./config.js";

console.log(`API URL: ${API_URL}`);

// Wake up call
fetch(`${API_URL}/api/health`).catch(() => {});

const MAX_ROWS = 50;
const MAX_TICKED = 10;
const MAX_STOCK_BOXES = 20;
const MAX_STOCK_LENGTH = 20000;
const DEFAULT_KERF = 3;

const STORAGE_KEY = "timbercut.cutlist";
const RESULT_KEY = "timbercut.result";

const docsLink = document.getElementById("api-docs-link");
const cutList = document.getElementById("cut-list");
const rowTemplate = document.getElementById("piece-row-template");
const planButton = document.getElementById("plan-button");
const emptyState = document.getElementById("state-empty");
const stockLengthList = document.getElementById("stock-lengths");
const stockTemplate = document.getElementById("stock-chip-template");
const stockMessage = document.getElementById("stock-message");
const chipLength = document.getElementById("stock-add-input");
const addStockButton = document.querySelector('[data-action="add-stock"]');
const deleteStocks = document.getElementById("delete-all-stock");
const stateInvalid = document.getElementById("state-invalid");
const stateInvalidList = document.getElementById("invalid-messages");
const planForm = document.getElementById("plan-form");
const kerfValue = document.getElementById("kerf-value");
//result
const results = document.getElementById("results");
const planSections = document.getElementById("plan-sections");
const planSectionTemplate = document.getElementById("plan-section-template");
const stackTemplate = document.getElementById("stack-template");
const boardPieceTemplate = document.getElementById("board-piece-template");
const boardKerfTemplate = document.getElementById("board-kerf-template");
const boardOffcutTemplate = document.getElementById("board-offcut-template");
const stackUnderTemplate = document.getElementById("stack-under-template");
const plan = document.getElementById("plan");
const ruler = document.getElementById("ruler");
// summary
const totalBoards = document.getElementById("total-boards");
const totalBought = document.getElementById("total-bought");
const totalUsed = document.getElementById("total-used");
const totalWaste = document.getElementById("total-waste");
const planHeadline = document.getElementById("plan-headline");
const shoppingBody = document.getElementById("shopping-body");
const shoppingRowTemplate = document.getElementById("shopping-row-template");

const FIELDS = ["label", "length", "quantity", "section"];

const pieceExamples = [
  { label: "wall stud", length: 1950, quantity: 16, section: "47x100 C24" },
  { label: "nogging", length: 550, quantity: 12, section: "47x100 C24" },
  { label: "rafter", length: 2150, quantity: 7, section: "47x150 C24" },
];

const stockExamples = [
  { length: 2400, checked: true },
  { length: 3600, checked: true },
  { length: 4800, checked: true },
  { length: 6000, checked: true },
];

const EXAMPLE_SOLVER = "greedy";
const SOLVERS = ["greedy", "cp_sat"];

const actions = {
  "add-piece": () => addRow(),
  "remove-piece": (button) => removeRow(button.closest("[data-piece-row]")),
  "load-example": () => loadExample(),
  "add-stock": () => addChip(),
};

kerfValue.textContent = DEFAULT_KERF;
// A switch for the output on the right to not show an empty-state alert
let showOutput = false;

docsLink.href = `${API_URL}/api/docs/`;

// Counters ***********
function rowCount() {
  return cutList.querySelectorAll("[data-piece-row]").length;
}

function stockCount() {
  return stockLengthList.querySelectorAll('input[name="stock_length"]').length;
}

function tickedCount() {
  return stockLengthList.querySelectorAll('input[name="stock_length"]:checked')
    .length;
}

function syncRowControls() {
  const count = rowCount();

  document.querySelectorAll('[data-action="add-piece"]').forEach((button) => {
    button.disabled = count >= MAX_ROWS;
  });
  syncPlanButton();
}

// Helpers *****************
function cloneTemplate(template) {
  return template.content.firstElementChild.cloneNode(true);
}

// Pieces **************************************************
function addRow(focus = true) {
  if (rowCount() >= MAX_ROWS) return;

  const row = cloneTemplate(rowTemplate);
  cutList.append(row);
  syncRowControls();
  saveCutList();

  if (focus) {
    row.querySelector('input[name="label"]').focus();
  }
  return row;
}

function removeRow(row) {
  row.remove();
  syncRowControls();
  saveCutList();
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;

  actions[button.dataset.action]?.(button);
});

// Local storage **********************************
function readRows() {
  return [...cutList.querySelectorAll("[data-piece-row]")].map((row) => {
    const piece = {};
    for (const field of FIELDS) {
      piece[field] = row.querySelector(`input[name="${field}"]`).value;
    }
    return piece;
  });
}

function readStocks() {
  return [
    ...stockLengthList.querySelectorAll('input[name="stock_length"]'),
  ].map((box) => {
    const stock = {};
    stock["length"] = Number(box.value);
    stock["checked"] = box.checked;
    return stock;
  });
}

function fillRow(row, piece) {
  for (const field of FIELDS) {
    row.querySelector(`input[name="${field}"]`).value = piece[field] ?? "";
  }
}

function fillStock(chip, values) {
  const input = chip.querySelector('input[name="stock_length"]');
  input.value = values["length"];
  chip.querySelector("[data-chip-length]").textContent = values["length"];
  input.checked = values["checked"];
}

function loadExample() {
  cutList.replaceChildren();
  stockLengthList.replaceChildren();
  planForm.elements.solver.value = EXAMPLE_SOLVER;
  localStorage.removeItem(RESULT_KEY);
  planSections.replaceChildren();

  for (const piece of pieceExamples) {
    fillRow(addRow(false), piece);
  }
  for (const stock of stockExamples) {
    fillStock(newChip(), stock);
  }
  syncStockControls();
}

function saveCutList() {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        pieces: readRows(),
        stocks: readStocks(),
        solver: planForm.elements.solver.value,
      }),
    );
  } catch {
    // Storage blocked or full: the page keeps working, it just won't store.
  }
}

function loadCutList() {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return {
      pieces: validateList(data?.pieces, MAX_ROWS),
      stocks: validateList(data?.stocks, MAX_STOCK_BOXES),
      solver: SOLVERS.includes(data?.solver) ? data.solver : null,
    };
  } catch {
    return { pieces: [], stocks: [], solver: null };
  }
}

function validateList(arr, max) {
  if (!Array.isArray(arr)) return [];
  return arr.filter((item) => item && typeof item === "object").slice(0, max);
}

function saveResult(result) {
  try {
    localStorage.setItem(RESULT_KEY, JSON.stringify(result));
  } catch {}
}

function loadResult() {
  try {
    const result = JSON.parse(localStorage.getItem(RESULT_KEY));
    if (!result || typeof result !== "object") return null;
    if (!Array.isArray(result.boards)) return null;
    const boardsValid = result.boards.every(
      (board) =>
        board &&
        typeof board === "object" &&
        Array.isArray(board.cuts) &&
        typeof board.stock_length === "number",
    );
    if (!boardsValid) return null;
    if (!result.summary || typeof result.summary !== "object") return null;
    return result;
  } catch {
    return null;
  }
}

cutList.addEventListener("input", () => {
  saveCutList();
  syncPlanButton();
});

planForm.addEventListener("change", (event) => {
  if (event.target.name === "solver") {
    saveCutList();
  }
});

const saved = loadCutList();

if (saved.solver) {
  planForm.elements.solver.value = saved.solver;
}

if (saved.stocks.length > 0) {
  for (const stock of saved.stocks) {
    fillStock(newChip(), stock);
  }
} else {
  for (const stock of stockExamples) {
    fillStock(newChip(), stock);
  }
}

if (saved.pieces.length > 0) {
  for (const piece of saved.pieces) {
    fillRow(addRow(false), piece);
  }
} else {
  addRow(false);
}
syncStockControls();

const savedResult = loadResult();
if (savedResult) {
  renderResult(savedResult);
}

// Stock input **********************************************
function showStockMessage(message) {
  stockMessage.textContent = message;
  stockMessage.hidden = false;
}

function addChip() {
  if (tickedCount() >= MAX_TICKED || stockCount() >= MAX_STOCK_BOXES) return;

  const existingLength = [
    ...stockLengthList.querySelectorAll('input[name="stock_length"]'),
  ].map((input) => Number(input.value));

  const number = Number(chipLength.value);

  if (!Number.isInteger(number) || number < 1 || number > MAX_STOCK_LENGTH) {
    showStockMessage(
      `Your stock needs to be a whole number in the range from 1 to ${MAX_STOCK_LENGTH} mm`,
    );
    return;
  }
  if (existingLength.includes(number)) {
    showStockMessage(`${number} mm is already in the list.`);
    return;
  }

  fillStock(newChip(), { length: number, checked: true });

  syncStockControls();
  chipLength.value = "";
  chipLength.focus();
}

function newChip() {
  const chip = cloneTemplate(stockTemplate);
  stockLengthList.append(chip);
  return chip;
}

function syncStockControls() {
  const ticked = tickedCount();
  const tickedFull = ticked >= MAX_TICKED;
  const boxesFull = stockCount() >= MAX_STOCK_BOXES;
  const canAdd = !tickedFull && !boxesFull;

  chipLength.disabled = !canAdd;
  addStockButton.disabled = !canAdd;

  stockLengthList
    .querySelectorAll('input[name="stock_length"]')
    .forEach((input) => {
      input.disabled = tickedFull && !input.checked;
    });
  syncPlanButton();

  if (ticked < 1) {
    showStockMessage("Tick at least one length");
  } else if (tickedFull) {
    showStockMessage(
      `At most ${MAX_TICKED} lengths can be ticked. Untick one to choose another.`,
    );
  } else if (boxesFull) {
    showStockMessage(`The list holds at most ${MAX_STOCK_BOXES} lengths.`);
  } else {
    stockMessage.hidden = true;
  }
  saveCutList();
}

function rowsComplete() {
  return [...cutList.querySelectorAll("input")].every(
    (input) => input.value.trim() !== "",
  );
}

function syncPlanButton() {
  const rows = rowCount();

  if (rows < 1 && !showOutput) {
    emptyState.hidden = false;
  }
  planButton.disabled = rows < 1 || tickedCount() < 1 || !rowsComplete();
}

chipLength.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addChip();
  }
});

stockLengthList.addEventListener("change", syncStockControls);

deleteStocks.addEventListener("click", () => {
  stockLengthList.replaceChildren();

  syncStockControls();
});

//  API calling and boards drawing ************************
async function solveRequest(requestBody) {
  const response = await fetch(`${API_URL}/api/solve/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
  });
  if (!response.ok) {
    const error = new Error(`Solve failed with status ${response.status}`);
    error.status = response.status;
    error.retryAfter = response.headers.get("Retry-After");
    error.body = await response.json().catch(() => null);
    throw error;
  }
  return response.json();
}

function showInvalid(messages) {
  const items = messages.map((message) => {
    const li = document.createElement("li");
    li.textContent = message;
    return li;
  });
  stateInvalidList.replaceChildren(...items);
  stateInvalid.hidden = messages.length === 0;
}

planForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const pieces = readRows();
  const stocks = readStocks()
    .filter((stock) => stock.checked)
    .map((stock) => stock.length);

  const errors = [];
  if (stocks.length === 0) {
    errors.push("You need to pick at least one stock length before planning.");
  }
  if (pieces.length === 0) {
    errors.push(
      "You need to add at least one piece to the cut list before planning.",
    );
  }
  showInvalid(errors);
  if (errors.length > 0) {
    return;
  }
  const solver = planForm.elements.solver.value;

  const requestBody = {
    pieces: pieces,
    stock_lengths: stocks,
    kerf: DEFAULT_KERF,
    solver: solver,
  };
  if (solver === "cp_sat") {
    requestBody.time_limit = 10;
  }

  let result;
  try {
    result = await solveRequest(requestBody);
  } catch (error) {
    console.error(error.status, error.body);
    return;
  }
  const plannedResult = { ...result, kerf: requestBody.kerf };
  renderResult(plannedResult);
  saveResult(plannedResult);
});

function groupBySection(boards) {
  return Map.groupBy(boards, (board) => board.section);
}

function stackKey(board) {
  const cuts = board.cuts.map((cut) => [cut.label, cut.length]);
  return JSON.stringify([board.stock_length, cuts]);
}

function groupIntoStacks(boards) {
  const groups = Map.groupBy(boards, stackKey);
  return [...groups.values()]
    .map((group) => ({ board: group[0], count: group.length }))
    .sort((a, b) => b.count - a.count);
}

function renderResult({ boards, summary, shopping_list, kerf }) {
  results.hidden = false;
  drawData(boards, kerf);
  drawSummary(summary);
  drawShoppingList(shopping_list);
}

function drawData(boards, kerf) {
  planSections.replaceChildren();
  for (const [section, sectionBoards] of groupBySection(boards)) {
    planSections.append(
      makeSection(section, groupIntoStacks(sectionBoards), kerf),
    );
  }
  showOutput = true;
  const longest = Math.max(...boards.map((board) => board.stock_length));
  const scale = Math.ceil(longest / 100) * 100;
  plan.style.setProperty("--scale", scale);
  drawRuler(scale);
}

function drawRuler(length) {
  ruler.replaceChildren();
  const tickTemplate = document.getElementById("ruler-tick-template");
  const majorTickTemplate = document.getElementById(
    "ruler-major-tick-template",
  );
  const ticks = length / 100;

  for (let i = 0; i <= ticks; i++) {
    if (i % 10 === 0 && i !== 0) {
      const majorTick = cloneTemplate(majorTickTemplate);
      ruler.append(majorTick);
      majorTick.querySelector("[data-ruler-label]").textContent = i * 100;
    } else {
      const tick = cloneTemplate(tickTemplate);
      ruler.append(tick);
    }
  }
}

function makeSection(name, stacks, kerf) {
  const sectionEl = cloneTemplate(planSectionTemplate);
  sectionEl.querySelector("[data-section-name]").textContent = name;
  const stacksEl = sectionEl.querySelector("[data-stacks]");
  for (const stack of stacks) {
    stacksEl.append(makeStack(stack, kerf));
  }
  return sectionEl;
}

function makeStack({ board, count }, kerf) {
  const stackEl = cloneTemplate(stackTemplate);
  stackEl.querySelector("[data-stack-count]").textContent = `${count}×`;
  stackEl.querySelector("[data-stack-offcut]").textContent = board.offcut;
  fillBoard(stackEl.querySelector("[data-board]"), board, kerf);
  stackEl.style.setProperty("--stock", board.stock_length);
  const boardsEl = stackEl.querySelector("[data-stack-boards]");

  for (let i = 1; i < count; i++) {
    boardsEl.append(cloneTemplate(stackUnderTemplate));
  }

  return stackEl;
}

function fillBoard(element, board, kerf) {
  const lastIndex = board.cuts.length - 1;

  for (const [index, cut] of board.cuts.entries()) {
    const pieceEl = cloneTemplate(boardPieceTemplate);
    pieceEl.style.setProperty("--len", cut.length);
    pieceEl.querySelector("[data-piece-length]").textContent = cut.length;
    pieceEl.querySelector("[data-piece-name]").textContent = cut.label;
    element.append(pieceEl);

    if (index < lastIndex || board.offcut > 0) {
      const kerfEl = cloneTemplate(boardKerfTemplate);
      kerfEl.style.setProperty("--len", kerf);
      element.append(kerfEl);
    }
  }

  if (board.offcut > 0) {
    const offcutEl = cloneTemplate(boardOffcutTemplate);
    offcutEl.style.setProperty("--len", board.offcut);
    element.append(offcutEl);
  }
  const cutsText = board.cuts
    .map((cut) => `${cut.label} ${cut.length}`)
    .join(", ");

  let label = `${board.stock_length} mm board cut into ${cutsText}`;
  if (board.offcut > 0) {
    label += `, offcut ${board.offcut} mm`;
  }

  element.setAttribute("aria-label", label);
}

function drawSummary(summary) {
  totalBoards.textContent = summary.board_count;
  totalBought.textContent = `${(summary.stock_length_total / 1000).toFixed(2)} m`;
  totalUsed.textContent = `${(summary.piece_length_total / 1000).toFixed(2)} m`;
  totalWaste.textContent = `${(summary.waste / 1000).toFixed(2)} m, ${summary.waste_percent.toFixed(1)}%`;
  planHeadline.textContent = `Buy ${summary.board_count} boards. ${(summary.waste / 1000).toFixed(2)} m ends up as waste.`;
}

function drawShoppingList(list) {
  shoppingBody.replaceChildren();
  list.forEach((item) => {
    const shoppingEl = cloneTemplate(shoppingRowTemplate);
    shoppingEl.querySelector("[data-shopping-section]").textContent =
      item.section;
    shoppingEl.querySelector("[data-shopping-length]").textContent =
      item.length;
    shoppingEl.querySelector("[data-shopping-quantity]").textContent =
      item.quantity;
    shoppingBody.append(shoppingEl);
  });
}
