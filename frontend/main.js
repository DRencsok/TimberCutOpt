import { API_URL } from "./config.js";

console.log(`API URL: ${API_URL}`);

// Wake up call
fetch(`${API_URL}/api/health`).catch(() => {});

const MAX_ROWS = 50;

const STORAGE_KEY = "timbercut.cutlist";

const docsLink = document.getElementById("api-docs-link");
const cutList = document.getElementById("cut-list");
const rowTemplate = document.getElementById("piece-row-template");
const planButton = document.getElementById("plan-button");
const emptyState = document.getElementById("state-empty");

const FIELDS = ["label", "length", "quantity", "section"];

const examples = [
  { label: "wall stud", length: 1950, quantity: 16, section: "47x100 C24" },
  { label: "nogging", length: 550, quantity: 12, section: "47x100 C24" },
  { label: "rafter", length: 2150, quantity: 7, section: "47x150 C24" },
];

const actions = {
  "add-piece": () => addRow(),
  "remove-piece": (button) => removeRow(button.closest("[data-piece-row]")),
  "load-example": () => loadExample(),
};

// A switch for the output on the right to not show an empty-state alert
let showOutput = false;
emptyState.hidden = true;

docsLink.href = `${API_URL}/api/docs/`;

function rowCount() {
  return cutList.querySelectorAll("[data-piece-row]").length;
}

function syncRowControls() {
  const count = rowCount();

  document.querySelectorAll('[data-action="add-piece"]').forEach((button) => {
    button.disabled = count >= MAX_ROWS;
  });
  syncPlanButton(count);
}

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

function readRows() {
  return Array.from(cutList.querySelectorAll("[data-piece-row]")).map((row) => {
    const piece = {};
    for (const field of FIELDS) {
      piece[field] = row.querySelector(`input[name="${field}"]`).value;
    }
    return piece;
  });
}

function fillRow(row, piece) {
  for (const field of FIELDS) {
    row.querySelector(`input[name="${field}"]`).value = piece[field] ?? "";
  }
}

function loadExample() {
  cutList.replaceChildren();

  for (const piece of examples) {
    fillRow(addRow(false), piece);
  }
  saveCutList();
}

function syncPlanButton(count) {
  if (count < 1 && !showOutput) {
    emptyState.hidden = false;
    planButton.disabled = true;
  } else if (count < 1) {
    planButton.disabled = true;
  } else {
    planButton.disabled = false;
  }
}

function saveCutList() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ pieces: readRows() }));
  } catch {
    // Storage blocked or full: the page keeps working, it just won't store.
  }
}

function loadCutList() {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (!Array.isArray(data?.pieces)) return [];
    return data.pieces
      .filter((piece) => piece && typeof piece === "object")
      .slice(0, MAX_ROWS);
  } catch {
    return [];
  }
}

cutList.addEventListener("input", saveCutList);

const savedPieces = loadCutList();

if (savedPieces.length > 0) {
  for (const piece of savedPieces) {
    fillRow(addRow(false), piece);
  }
  saveCutList();
} else {
  addRow(false);
}
