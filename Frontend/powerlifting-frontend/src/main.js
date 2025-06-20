import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import { io } from "socket.io-client"; // Import Socket.IO client

const app = createApp(App);

// Connect to your Flask backend using the public URL
// IMPORTANT: This URL has been updated to your correct Render backend URL.
const socket = io("https://powerlifting-meet-system24.onrender.com"); // <--- THIS LINE IS THE CRITICAL CHANGE

// Make socket available globally in Vue components
app.config.globalProperties.$socket = socket;

// Optional: Log connection status - removed console.log statements for production build
socket.on("connect", () => {
  // console.log("Frontend connected to backend Socket.IO");
});

socket.on("disconnect", () => {
  // console.log("Frontend disconnected from backend Socket.IO");
});

app.use(store).use(router).mount("#app");
