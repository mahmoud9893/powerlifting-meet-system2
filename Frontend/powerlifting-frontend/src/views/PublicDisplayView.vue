<template>
  <div class="public-display-view p-6 bg-gray-900 min-h-screen text-white">
    <h1 class="text-4xl font-extrabold text-indigo-400 mb-6 border-b-4 border-indigo-500 pb-2">
      Live Meet Display
    </h1>

    <!-- Current Meet State -->
    <div class="mb-8 p-6 bg-gray-800 rounded-lg shadow-xl">
      <h2 class="text-3xl font-bold text-indigo-300 mb-4 flex items-center">
        <svg
          class="mr-3 h-8 w-8 text-indigo-400"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
>
          <path
            d="M9 19V6l-5 4V21M9 19c-3.111 0-7-1.488-7-4s1.956-2 7-2m0 0v-5c0 1.25.968 2.5 3 2.5s3-1.25 3-2.5V4m0 0c0 1.25.968 2.5 3 2.5s3-1.25 3-2.5V4m-3 10v-4m-3 4v-4"
            stroke-linecap="round"
            stroke-linejoin="round"
/>
        </svg>
        Meet Progress
      </h2>
      <div v-if="meetState" class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xl">
        <p>
          <strong class="text-indigo-200">Current Lift:</strong>
          <span class="capitalize text-indigo-400 font-extrabold">{{
            meetState.current_lift_type
          }}</span>
        </p>
        <p>
          <strong class="text-indigo-200">Attempt:</strong>
          <span class="text-indigo-400 font-extrabold">{{
            meetState.current_attempt_number
          }}</span>
        </p>
        <p>
          <strong class="text-indigo-200">Active Lift ID:</strong>
          <span :class="{
            'text-green-400 font-semibold': meetState.current_active_lift_id,
            'text-gray-500 italic': !meetState.current_active_lift_id,
          }"
>
            {{ meetState.current_active_lift_id || "None" }}
          </span>
        </p>
      </div>
      <div v-else class="text-gray-500 text-xl">Loading meet state...</div>
    </div>

    <!-- Current Active Lift Display -->
    <div class="mb-8 p-6 bg-gray-800 rounded-lg shadow-xl">
      <h2 class="text-3xl font-bold text-indigo-300 mb-4 flex items-center">
        <svg
          class="mr-3 h-8 w-8 text-indigo-400"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
>
          <path
            d="M13 10V3L4 14h7v7l9-11h-7z"
            stroke-linecap="round"
            stroke-linejoin="round"
/>
        </svg>
        On The Platform
      </h2>
      <div
        v-if="currentLift"
        class="bg-indigo-700 p-6 rounded-md border-2 border-indigo-500 text-center"
>
        <p class="text-4xl font-extrabold mb-2 text-white">
          {{ currentLift.lifter_name }}
        </p>
        <p class="text-2xl text-indigo-200 mb-3">
          ID: {{ currentLift.lifter_id_number }} |
          {{ currentLift.lift_type.toUpperCase() }} | Attempt
          {{ currentLift.attempt_number }}
        </p>
        <p class="text-6xl font-black text-yellow-300 mb-4">
          {{ currentLift.weight_lifted }} kg
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xl">
          <div class="p-3 bg-indigo-600 rounded-md">
            Judge 1:
            <span :class="scoreClass(currentLift.judge1_score)">{{
              formatScore(currentLift.judge1_score)
            }}</span>
          </div>
          <div class="p-3 bg-indigo-600 rounded-md">
            Judge 2:
            <span :class="scoreClass(currentLift.judge2_score)">{{
              formatScore(currentLift.judge2_score)
            }}</span>
          </div>
          <div class="p-3 bg-indigo-600 rounded-md">
            Judge 3:
            <span :class="scoreClass(currentLift.judge3_score)">{{
              formatScore(currentLift.judge3_score)
            }}</span>
          </div>
        </div>

        <p v-if="currentLift.overall_result !== null" class="text-5xl font-extrabold mt-6">
          Overall:
          <span :class="overallResultClass(currentLift.overall_result)">{{
            formatOverallResult(currentLift.overall_result)
          }}</span>
        </p>
        <p v-else class="text-4xl font-extrabold mt-6 text-orange-300 animate-pulse">
          PENDING JUDGES...
        </p>
      </div>
      <div v-else class="text-gray-500 italic text-2xl text-center">
        No lifter currently active. Waiting for the Organizer...
      </div>
    </div>

    <!-- Next Lifts in Queue -->
    <div class="p-6 bg-gray-800 rounded-lg shadow-xl">
      <h2 class="text-3xl font-bold text-indigo-300 mb-4 flex items-center">
        <svg
          class="mr-3 h-8 w-8 text-indigo-400"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
>
          <path
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            stroke-linecap="round"
            stroke-linejoin="round"
/>
        </svg>
        Upcoming Lifts ({{ meetState?.current_lift_type }} - Attempt
        {{ meetState?.current_attempt_number }})
      </h2>
      <div v-if="nextLiftsInQueue.length > 0">
        <div class="overflow-x-auto">
          <table class="min-w-full bg-gray-700 text-white rounded-lg overflow-hidden text-lg">
            <thead class="bg-gray-600">
              <tr
                class="text-left text-sm font-semibold uppercase tracking-wider text-gray-300"
>
                <th class="px-6 py-3">Lifter Name</th>
                <th class="px-6 py-3">Lifter ID</th>
                <th class="px-6 py-3">Weight</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="lift in nextLiftsInQueue"
                :key="lift.id"
                class="border-t border-gray-600 hover:bg-gray-600"
>
                <td class="px-6 py-4">{{ lift.lifter_name }}</td>
                <td class="px-6 py-4">{{ lift.lifter_id_number }}</td>
                <td class="px-6 py-4">{{ lift.weight_lifted }} kg</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else class="italic text-gray-500 text-2xl text-center">
        No pending lifts for the current type and attempt.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import { io } from "socket.io-client";

// Reactive state variables
const meetState = ref(null);
const currentLift = ref(null);
const nextLiftsInQueue = ref([]);

// Determine API URL based on environment
// This will prioritize the VUE_APP_BACKEND_API_URL environment variable (set in Netlify)
// If not set, it will fallback to your Render backend URL directly for robustness.
const BACKEND_API_URL = process.env.VUE_APP_BACKEND_API_URL || "https://powerlifting-meet-backend.onrender.com";
const SOCKET_IO_URL = process.env.VUE_APP_BACKEND_API_URL || "https://powerlifting-meet-backend.onrender.com";

// Initialize Socket.IO connection
const socket = io(SOCKET_IO_URL);

// --- Utility Functions for Display ---
const formatScore = (score) => {
  if (score === true) return "GOOD";
  if (score === false) return "BAD";
  return "N/A";
};

const scoreClass = (score) => {
  if (score === true) return "text-green-400 font-semibold";
  if (score === false) return "text-red-400 font-semibold";
  return "text-gray-400 italic";
};

const formatOverallResult = (result) => {
  if (result === true) return "GOOD LIFT";
  if (result === false) return "NO LIFT";
  return "PENDING"; // Should not show 'PENDING' if overall_result is not null
};

const overallResultClass = (result) => {
  if (result === true) return "text-green-500";
  if (result === false) return "text-red-500";
  return "text-orange-500"; // Should not be reached if overall_result is not null
};

// --- Fetching Functions ---
const fetchMeetState = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state`);
    const data = await await response.json();
    meetState.value = data;
  } catch (error) {
    console.error("Error fetching meet state:", error);
  }
};

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

const fetchNextLiftsInQueue = async () => {
  try {
    await fetch(`${BACKEND_API_URL}/next_lift_in_queue`); // Trigger backend queue logic if needed
    const allLiftsResponse = await fetch(`${BACKEND_API_URL}/lifts`);
    if (allLiftsResponse.ok) {
      const allLifts = await allLiftsResponse.json();
      nextLiftsInQueue.value = allLifts
        .filter(
          (lift) =>
            lift.status === "pending" &&
            lift.lift_type === meetState.value?.current_lift_type &&
            lift.attempt_number === meetState.value?.current_attempt_number
        )
        .sort((a, b) => {
          // Sort by weight_lifted (ascending), then by lifter_id_number (ascending)
          if (a.weight_lifted !== b.weight_lifted) {
            return a.weight_lifted - b.weight_lifted;
          }
          return a.lifter_id_number.localeCompare(b.lifter_id_number);
        });
    } else {
      nextLiftsInQueue.value = [];
    }
  } catch (error) {
    console.error("Error fetching next lifts in queue:", error);
  }
};

// --- Socket.IO Event Listeners ---
onMounted(() => {
  fetchMeetState();
  fetchCurrentLift();
  fetchNextLiftsInQueue();

  socket.on("connect", () => {
    // console.log("Connected to Socket.IO from PublicDisplayView");
  });

  socket.on("meet_state_updated", (_data) => {
    // console.log("Meet state updated via Socket.IO:", _data);
    meetState.value = _data;
    fetchCurrentLift();
    fetchNextLiftsInQueue();
  });

  socket.on("active_lift_changed", (_data) => {
    // console.log("Active lift changed via Socket.IO:", _data);
    currentLift.value = _data;
    fetchNextLiftsInQueue();
  });

  socket.on("lift_updated", (_data) => {
    // console.log("Lift updated via Socket.IO:", _data);
    if (currentLift.value && currentLift.value.id === _data.id) {
      currentLift.value = _data;
    }
    fetchNextLiftsInQueue();
  });
});

// Watcher for meetState changes to ensure nextLiftsInQueue is always relevant
watch(meetState, (newMeetState) => {
  if (newMeetState) {
    fetchNextLiftsInQueue();
  }
});
</script>

<style scoped>
/* You can add custom styles here if Tailwind alone isn't sufficient */
/* For example, specific font sizes not easily expressible with Tailwind classes */
</style>
