// ... other imports
import { io } from "socket.io-client";

const app = createApp(App);

// Connect to your Flask backend using the Genezio deployed URL
const socket = io("YOUR_GENEZIO_BACKEND_URL"); // PASTE YOUR GENEZIO URL HERE

// Make socket available globally in Vue components
app.config.globalProperties.$socket = socket;

// ... rest of the code



import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import { io } from "socket.io-client"; // Import Socket.IO client

const app = createApp(App);

// Connect to your Flask backend
const socket = io("http://192.168.1.21:5000");

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
