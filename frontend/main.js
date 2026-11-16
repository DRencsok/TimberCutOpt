import { API_URL } from "./config.js";

console.log(`API URL: ${API_URL}`);

// Wake up call
fetch(`${API_URL}/api/health`).catch(() => {});

const MAX_ROWS = 50;
const MAX_TICKED = 10;
const MAX_STOCK_BOXES = 20;
const MAX_STOCK_LENGTH = 20000;

const STORAGE_KEY = "timbercut.cutlist";

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

const actions = {
  "add-piece": () => addRow(),
  "remove-piece": (button) => removeRow(button.closest("[data-piece-row]")),
  "load-example": () => loadExample(),
  "add-stock": () => addChip(),
};

// A switch for the output on the right to not show an empty-state alert
let showOutput = false;
emptyState.hidden = true;

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

// Pieces **************************************************
function addRow(focus = true) {
  if (rowCount() >= MAX_ROWS) return;

  const row = rowTemplate.content.firstElementChild.cloneNode(true);
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
  chip.querySelector(".chip__face").textContent = values["length"];
  input.checked = values["checked"];
}

function loadExample() {
  cutList.replaceChildren();
  stockLengthList.replaceChildren();

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
      JSON.stringify({ pieces: readRows(), stocks: readStocks() }),
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
    };
  } catch {
    return { pieces: [], stocks: [] };
  }
}

function validateList(arr, max) {
  if (!Array.isArray(arr)) return [];
  return arr.filter((item) => item && typeof item === "object").slice(0, max);
}

cutList.addEventListener("input", saveCutList);

const saved = loadCutList();

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
  const chip = stockTemplate.content.firstElementChild.cloneNode(true);
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

function syncPlanButton() {
  const rows = rowCount();

  if (rows < 1 && !showOutput) {
    emptyState.hidden = false;
  }
  planButton.disabled = rows < 1 || tickedCount() < 1;
}

chipLength.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addChip();
  }
});

stockLengthList.addEventListener("change", syncStockControls);
