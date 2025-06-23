<template>
  <div class="judges-view p-6 bg-gray-900 min-h-screen text-white flex flex-col items-center justify-center">
    <h1 class="text-4xl font-extrabold text-teal-400 mb-8 border-b-4 border-teal-500 pb-2 text-center">
      Judge Panel
    </h1>

    <div v-if="!judgeName" class="login-section bg-gray-800 p-8 rounded-lg shadow-xl w-full max-w-md">
      <h2 class="text-2xl font-bold text-teal-300 mb-4">Judge Login</h2>
      <input
        type="password"
        v-model="pin"
        placeholder="Enter PIN"
        class="w-full p-3 mb-4 rounded-md bg-gray-700 text-white border border-gray-600 focus:ring-teal-500 focus:border-teal-500"
      />
      <button
        @click="login"
        class="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 px-4 rounded-md transition duration-300 ease-in-out">
        Login
      </button>
      <p v-if="loginError" class="text-red-500 mt-3 text-center">{{ loginError }}</p>
    </div>

    <div v-else class="judge-dashboard bg-gray-800 p-8 rounded-lg shadow-xl w-full max-w-2xl">
      <h2 class="text-3xl font-bold text-teal-300 mb-6 text-center">Welcome, {{ judgeName }}!</h2>
      
      <!-- Current Active Lift Display for Judges -->
      <div v-if="currentLift" class="bg-teal-700 p-6 rounded-md border-2 border-teal-500 text-center mb-6">
        <p class="text-4xl font-extrabold mb-2 text-white">
          {{ currentLift.lifter_name }}
        </p>
        <p class="text-2xl text-teal-200 mb-3">
          ID: {{ currentLift.lifter_id_number }} |
          {{ currentLift.lift_type ? currentLift.lift_type.toUpperCase() : '' }} | Attempt
          {{ currentLift.attempt_number }}
        </p>
        <p class="text-6xl font-black text-yellow-300 mb-4">
          {{ currentLift.weight_lifted }} kg
        </p>

        <p class="text-xl text-teal-100 mb-4">Your Score:</p>
        <div class="flex justify-center space-x-4 mb-4">
          <button
            @click="submitScore(true)"
            :disabled="hasScored"
            class="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-md transition duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed">
            GOOD LIFT
          </button>
          <button
            @click="submitScore(false)"
            :disabled="hasScored"
            class="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-md transition duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed">
            NO LIFT
          </button>
        </div>
        <p v-if="hasScored" class="text-green-300 text-xl">Score Submitted!</p>
        <p v-else-if="scoreError" class="text-red-400 text-xl">{{ scoreError }}</p>
      </div>
      <div v-else class="text-gray-500 italic text-2xl text-center">
        No lifter currently active. Waiting for Organizer to set active lift.
      </div>

      <button
        @click="logout"
        class="mt-8 bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
        Logout
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { io } from "socket.io-client";

const pin = ref("");
const judgeName = ref(localStorage.getItem("judgeName") || null);
const loginError = ref(null);
const currentLift = ref(null);
const scoreError = ref(null);
const hasScored = ref(false);

const BACKEND_API_URL = "https://powerlifting-meet-system24.onrender.com";
const SOCKET_IO_URL = "https://powerlifting-meet-system24.onrender.com";

const socket = io(SOCKET_IO_URL);

// --- Login/Logout Logic ---
const login = async () => {
  loginError.value = null;
  try {
    const response = await fetch(`${BACKEND_API_URL}/login_judge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin: pin.value }),
    });
    const data = await response.json();
    if (response.ok) {
      judgeName.value = data.judge_id;
      localStorage.setItem("judgeName", data.judge_id); // Persist login
      pin.value = ""; // Clear pin
      fetchCurrentLift(); // Fetch current lift immediately after login
    } else {
      loginError.value = data.error || "Login failed.";
    }
  } catch (error) {
    loginError.value = "Network error during login.";
    console.error("Login network error:", error);
  }
};

const logout = () => {
  judgeName.value = null;
  localStorage.removeItem("judgeName");
  currentLift.value = null;
  hasScored.value = false;
  scoreError.value = null;
};

// --- Fetching and Scoring Lift Logic ---
const fetchCurrentLift = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/current_lift`);
    if (response.ok) {
      const data = await response.json();
      currentLift.value = Object.keys(data).length > 0 ? data : null;
      hasScored.value = checkIfJudgeHasScored(currentLift.value); // Reset score status
    } else {
      currentLift.value = null;
      console.error("Failed to fetch current lift:", response.statusText);
    }
  }
  catch (error) {
    console.error("Network error fetching current lift:", error);
  }
};

const checkIfJudgeHasScored = (lift) => {
  if (!lift || !judgeName.value) return false;
  if (judgeName.value === "Judge 1" && lift.judge1_score !== null) return true;
  if (judgeName.value === "Judge 2" && lift.judge2_score !== null) return true;
  if (judgeName.value === "Judge 3" && lift.judge3_score !== null) return true;
  return false;
};

const submitScore = async (score) => {
  scoreError.value = null;
  hasScored.value = false; // Optimistically reset

  if (!currentLift.value || !judgeName.value) {
    scoreError.value = "No active lift or not logged in.";
    return;
  }

  try {
    const response = await fetch(`${BACKEND_API_URL}/lifts/${currentLift.value.id}/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ judge_pin: pin.value, score: score }), // Send actual pin for validation
    });
    const data = await response.json();
    if (response.ok) {
      // Update local currentLift with the latest data from backend
      currentLift.value = data;
      hasScored.value = checkIfJudgeHasScored(currentLift.value); // Re-check after update
    } else {
      scoreError.value = data.error || "Failed to submit score.";
    }
  } catch (error) {
    scoreError.value = "Network error submitting score.";
    console.error("Submit score network error:", error);
  }
};

// --- Socket.IO Event Listeners ---
onMounted(() => {
  // Only fetch current lift on mount if already logged in (e.g., from localStorage)
  if (judgeName.value) {
    fetchCurrentLift();
  }

  socket.on("connect", () => {
    // console.log("Connected to Socket.IO from JudgesView");
  });

  socket.on("active_lift_changed", (_data) => {
    // console.log("Active lift changed via Socket.IO for JudgesView:", _data);
    currentLift.value = _data;
    hasScored.value = checkIfJudgeHasScored(currentLift.value); // Reset score status for new active lift
    scoreError.value = null; // Clear previous score errors
  });

  socket.on("lift_updated", (_data) => {
    // console.log("Lift updated via Socket.IO for JudgesView:", _data);
    if (currentLift.value && currentLift.value.id === _data.id) {
      currentLift.value = _data;
      hasScored.value = checkIfJudgeHasScored(currentLift.value); // Re-check if this judge has scored
    }
  });
});
</script>

<style scoped>
/* Scoped styles for JudgesView if needed */
</style>
