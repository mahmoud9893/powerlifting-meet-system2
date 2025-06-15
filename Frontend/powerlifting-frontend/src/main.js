import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import { io } from "socket.io-client"; // This line should appear ONLY ONCE

const app = createApp(App);

// Connect to your Flask backend using the public URL
// IMPORTANT: REPLACE 'http://YOUR_COMPUTERS_IP_ADDRESS:5000' with your LIVE RENDER BACKEND URL (e.g., 'https://your-backend-name.onrender.com')
const socket = io("https://powerlifting-meet-backend.onrender.com");

// Make socket available globally in Vue components
app.config.globalProperties.$socket = socket;

// Optional: Log connection status
socket.on("connect", () => {
  console.log("Frontend connected to backend Socket.IO");
});

socket.on("disconnect", () => {
  console.log("Frontend disconnected from backend Socket.IO");
});

app.use(store).use(router).mount("#app");



