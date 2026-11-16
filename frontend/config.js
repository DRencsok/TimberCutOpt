const LOCAL_HOST = ["localhost", "127.0.0.1"];

export const API_URL = LOCAL_HOST.includes(location.hostname)
  ? "http://localhost:8000"
  : "https://timbercutopt.onrender.com";