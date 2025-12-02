import axios from 'axios';

const api = axios.create({

    baseURL: 'https://study-assistant-api.onrender.com', // <--- SUA URL DO RENDER AQUI
});

export default api;