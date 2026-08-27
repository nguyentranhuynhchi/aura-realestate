// frontend/src/services/api.js
import axios from 'axios';

// Sửa thẳng thành URL của FastAPI Backend để tránh lệch cổng môi trường
const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    timeout: 180000 
});

export default api;