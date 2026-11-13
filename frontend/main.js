import { API_URL } from "./config.js";

console.log(`API URL: ${API_URL}`);

const docsLink = document.getElementById("api-docs-link");
docsLink.href = `${API_URL}/api/docs/`;
