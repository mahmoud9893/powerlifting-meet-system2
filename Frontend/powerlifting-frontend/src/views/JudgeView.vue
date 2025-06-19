<template>
  <div class="judge-app-container p-6 bg-gray-100 min-h-screen text-gray-800">
    <h1 class="text-3xl font-bold text-indigo-700 mb-6 border-b-2 pb-2">
      Judge Scorecard
    </h1>

    <div v-if="message" :class="['message-box p-3 rounded-md mb-4 text-center text-base', messageType === 'success' ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800']">
      {{ message }}
    </div>

    <!-- PIN Entry / Login Screen -->
    <div v-if="!isLoggedIn" class="login-card p-6 bg-white rounded-lg shadow-md max-w-md mx-auto">
      <h2 class="text-2xl font-semibold mb-4 text-center">Enter Judge PIN</h2>
      <input
        type="password"
        v-model="pinCode"
        placeholder="Enter 4-digit PIN"
        maxlength="4"
        @keyup.enter="handleLogin"
        class="pin-input w-full p-3 mb-4 border border-gray-300 rounded-md text-center text-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
      <button @click="handleLogin" class="login-btn w-full bg-indigo-600 text-white py-3 rounded-md hover:bg-indigo-700 transition duration-300 text-lg font-semibold shadow-md">
        Login
      </button>
      <p v-if="loginError" class="error-message text-red-600 text-sm mt-3 text-center">{{ loginError }}</p>
      <p class="info-text text-gray-500 text-sm mt-4 text-center">
        Please contact the organizer for your PIN.
      </p>
    </div>

    <!-- Main Judge Scorecard (Visible only after successful login) -->
    <div v-else class="scorecard-container max-w-2xl mx-auto">
      <div v-if="currentLift" class="current-lift-card p-6 bg-white rounded-lg shadow-md text-center">
        <h2 class="text-2xl font-bold text-indigo-700 mb-3">Current Lifter:</h2>
        <p class="lifter-name text-3xl font-extrabold text-gray-900 mb-2">{{ currentLift.lifter_name }}</p>
        <p class="details text-lg text-gray-600 mb-1">
          ID: {{ currentLift.lifter_id_number }} | Gender:
          {{ currentLift.gender }}
        </p>
        <p class="details text-lg text-gray-600 mb-4">
          Weight Class: {{ currentLift.weight_class_name || 'N/A' }} | Attempt:
          {{ currentLift.attempt_number }}
        </p>
        <p class="lift-type text-4xl font-bold text-indigo-600 mb-4">{{ currentLift.lift_type.toUpperCase() }}</p>
        <p class="weight-lifted text-5xl font-extrabold text-yellow-600 mb-6">
          {{ currentLift.weight_lifted }} kg
        </p>

        <div class="judge-buttons grid grid-cols-2 gap-4 mb-6">
          <button @click="submitScore(true)" class="good-lift-btn bg-green-500 text-white py-4 rounded-lg text-2xl font-bold hover:bg-green-600 transition duration-300 flex items-center justify-center">
            <svg class="w-8 h-8 mr-2" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Good Lift
          </button>
          <button @click="submitScore(false)" class="bad-lift-btn bg-red-500 text-white py-4 rounded-lg text-2xl font-bold hover:bg-red-600 transition duration-300 flex items-center justify-center">
            <svg class="w-8 h-8 mr-2" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> No Lift
          </button>
        </div>

        <div class="current-scores p-4 bg-gray-50 rounded-md">
          <h3 class="text-xl font-semibold mb-3 text-left">Current Scores:</h3>
          <p class="text-lg text-left">
            Judge 1:
            <span :class="getScoreClass(currentLift.judge1_score)">{{
              formatScore(currentLift.judge1_score)
            }}</span>
          </p>
          <p class="text-lg text-left">
            Judge 2:
            <span :class="getScoreClass(currentLift.judge2_score)">{{
              formatScore(currentLift.judge2_score)
            }}</span>
          </p>
          <p class="text-lg text-left">
            Judge 3:
            <span :class="getScoreClass(currentLift.judge3_score)">{{
              formatScore(currentLift.judge3_score)
            }}</span>
          </p>
          <p v-if="currentLift.overall_result !== null" class="overall-result text-2xl font-bold mt-4 text-left">
            Overall:
            <span
              :class="currentLift.overall_result ? 'text-green-700' : 'text-red-700'"
              >{{ currentLift.overall_result ? "GOOD" : "NO LIFT" }}</span>
          </p>
          <p v-else class="overall-result text-2xl font-bold mt-4 text-left text-orange-500">
            Overall: PENDING
          </p>
        </div>
      </div>
      <div v-else class="no-active-lift p-6 bg-white rounded-lg shadow-md text-center text-xl italic text-gray-600">
        <p>No active lift currently. Waiting for organizer...</p>
      </div>

      <!-- Judge ID display (now auto-assigned/shown after login) -->
      <div class="judge-id-section mt-8 p-4 bg-white rounded-lg shadow-md text-center">
        <p class="text-lg">
          You are logged in as Judge: <strong class="text-indigo-700">{{ judgeId }}</strong>
        </p>
        <button @click="logout" class="logout-btn mt-3 bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 transition duration-300 text-base font-semibold shadow-md">Logout</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { io } from "socket.io-client";

const pinCode = ref("");
const isLoggedIn = ref(false);
const loginError = ref("");
const judgeId = ref(null); // Stores "Judge 1", "Judge 2", etc.
const currentLift = ref(null);
const message = ref("");
const messageType = ref(""); // 'success' or 'error'

const showMessage = (msg, type = "info") => {
  message.value = msg;
  messageType.value = type;
  setTimeout(() => {
    message.value = "";
    messageType.value = "";
  }, 5000); // Message disappears after 5 seconds
};

// IMPORTANT: Ensure this URL points to your LIVE RENDER BACKEND URL
const BACKEND_API_URL = process.env.VUE_APP_BACKEND_API_URL || "https://powerlifting-meet-backend.onrender.com";
const SOCKET_IO_URL = process.env.VUE_APP_BACKEND_API_URL || "https://powerlifting-meet-backend.onrender.com";


const socket = io(SOCKET_IO_URL);

// --- Utility Functions for Display ---
const formatScore = (score) => {
  if (score === true) return "GOOD";
  if (score === false) return "BAD";
  return "N/A";
};

const getScoreClass = (score) => {
  if (score === true) return "text-green-600 font-semibold";
  if (score === false) return "text-red-600 font-semibold";
  return "text-gray-500 italic";
};

// --- Fetching and Action Functions ---
const fetchCurrentLift = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/current_lift`);
    if (response.ok) {
      const data = await response.json();
      currentLift.value = Object.keys(data).length > 0 ? data : null; // Handle empty object for no active lift
    } else {
      currentLift.value = null;
      console.error("Failed to fetch current lift:", response.statusText);
    }
  } catch (error) {
    console.error("Network error fetching current lift:", error);
  }
};

const handleLogin = async () => {
  loginError.value = "";
  try {
    const response = await fetch(`${BACKEND_API_URL}/login_judge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin: pinCode.value }),
    });
    const data = await response.json();
    if (response.ok) {
      isLoggedIn.value = true;
      judgeId.value = data.judge_id;
      localStorage.setItem("judgePin", pinCode.value); // Store PIN for persistence
      localStorage.setItem("judgeId", judgeId.value);
      showMessage("Logged in successfully!", "success");
      fetchCurrentLift(); // Fetch active lift once logged in
    } else {
      loginError.value = data.error || "Login failed.";
      showMessage(loginError.value, "error");
    }
  } catch (error) {
    loginError.value = "Network error during login.";
    showMessage(loginError.value, "error");
    console.error("Login network error:", error);
  }
};

const logout = () => {
  isLoggedIn.value = false;
  pinCode.value = "";
  judgeId.value = null;
  currentLift.value = null; // Clear current lift on logout
  localStorage.removeItem("judgePin"); // Clear stored PIN
  localStorage.removeItem("judgeId"); // Clear stored Judge ID
  showMessage("Logged out successfully.", "success");
};

const submitScore = async (score) => {
  if (!currentLift.value || !judgeId.value) {
    showMessage("No active lift or not logged in.", "error");
    return;
  }

  try {
    const response = await fetch(`${BACKEND_API_URL}/lifts/${currentLift.value.id}/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ judge_pin: pinCode.value, score: score }),
    });
    const data = await response.json();
    if (response.ok) {
      showMessage("Score submitted successfully!", "success");
      // The socket.io 'lift_updated' event will handle updating currentLift.value
    } else {
      showMessage(`Failed to submit score: ${data.error || response.statusText}`, "error");
    }
  } catch (error) {
    showMessage("Network error during score submission.", "error");
    console.error("Score submission network error:", error);
  }
};

// --- Socket.IO Event Listeners ---
onMounted(() => {
  // Attempt auto-login if PIN is stored
  const storedPin = localStorage.getItem("judgePin");
  const storedJudgeId = localStorage.getItem("judgeId");
  if (storedPin && storedJudgeId) {
    pinCode.value = storedPin;
    // We don't re-run handleLogin on mount to avoid unnecessary backend calls
    // Just set the state to logged in, and then fetch the current lift.
    isLoggedIn.value = true;
    judgeId.value = storedJudgeId;
    fetchCurrentLift();
  }

  socket.on("connect", () => {
    // console.log("Judge App Connected to Socket.IO");
  });

  socket.on("active_lift_changed", (data) => {
    // console.log("Judge App: Active lift changed via Socket.IO:", data);
    currentLift.value = data;
    if (data && judgeId.value) {
        showMessage(`New Active Lift: ${data.lifter_name} - ${data.weight_lifted}kg`, "info");
    } else if (!data) {
        showMessage("Active lift cleared by organizer.", "info");
    }
  });

  socket.on("lift_updated", (data) => {
    // console.log("Judge App: Lift updated via Socket.IO:", data);
    if (currentLift.value && currentLift.value.id === data.id) {
      currentLift.value = data;
      // Optionally show a message when scores are updated or overall result changes
      if (data.overall_result !== null) {
        showMessage(`Lift for ${data.lifter_name} resulted in: ${data.overall_result ? 'GOOD LIFT' : 'NO LIFT'}`, 'info');
      }
    }
  });
});

onUnmounted(() => {
  socket.off("connect");
  socket.off("active_lift_changed");
  socket.off("lift_updated");
});
</script>

<style scoped>
/* Scoped styles specific to JudgeView */
/* Adjust background, card styles, and button colors as needed */

/* Generic styles that might be useful */
.message-box {
  @apply font-medium;
}

.login-card {
  /* No specific styling needed beyond Tailwind classes for now */
}

.pin-input {
  /* Tailwind classes handle most of it */
}

.login-btn {
  /* Tailwind classes handle most of it */
}

.error-message {
  /* Tailwind classes handle most of it */
}

.info-text {
  /* Tailwind classes handle most of it */
}

.scorecard-container {
  /* No specific styling needed beyond Tailwind classes for now */
}

.current-lift-card {
  /* No specific styling needed beyond Tailwind classes for now */
}

.lifter-name {
  /* No specific styling needed beyond Tailwind classes for now */
}

.details {
  /* No specific styling needed beyond Tailwind classes for now */
}

.lift-type {
  /* No specific styling needed beyond Tailwind classes for now */
}

.weight-lifted {
  /* No specific styling needed beyond Tailwind classes for now */
}

.judge-buttons {
  /* No specific styling needed beyond Tailwind classes for now */
}

.good-lift-btn {
  /* Tailwind classes handle most of it */
}

.bad-lift-btn {
  /* Tailwind classes handle most of it */
}

.current-scores {
  /* No specific styling needed beyond Tailwind classes for now */
}

.score-good {
  @apply text-green-600 font-semibold;
}

.score-bad {
  @apply text-red-600 font-semibold;
}

.overall-result {
  /* No specific styling needed beyond Tailwind classes for now */
}

.no-active-lift {
  /* No specific styling needed beyond Tailwind classes for now */
}

.judge-id-section {
  /* No specific styling needed beyond Tailwind classes for now */
}

.logout-btn {
  /* Tailwind classes handle most of it */
}
</style>
