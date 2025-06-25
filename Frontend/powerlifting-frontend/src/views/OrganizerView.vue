<template>
  <!-- Main container for the Organizer View. Added dark background and Inter font. -->
  <div class="min-h-screen bg-gray-950 text-white p-6 font-inter">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">

    <!-- Main heading with gradient text for a strong, modern feel -->
    <h1
      class="text-4xl lg:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-blue-500 mb-8 border-b-4 border-indigo-500 pb-2">
      Meet Organizer Panel
    </h1>

    <!-- Meet State Card -->
    <div class="mb-8 p-6 bg-gray-800 rounded-2xl shadow-xl border border-gray-700">
      <h2 class="text-3xl font-bold text-indigo-300 mb-4 flex items-center">
        <svg
          class="mr-3 h-6 w-6 text-indigo-400"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg">
          <path
            d="M9 19V6l-5 4V21M9 19c-3.111 0-7-1.488-7-4s1.956-2 7-2m0 0v-5c0 1.25.968 2.5 3 2.5s3-1.25 3-2.5V4m0 0c0 1.25.968 2.5 3 2.5s3-1.25 3-2.5V4m-3 10v-4m-3 4v-4"
            stroke-linecap="round"
            stroke-linejoin="round" />
        </svg>
        Current Meet State
      </h2>
      <div v-if="meetState" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xl">
        <p><strong class="text-indigo-200">Current Lift Type:</strong> <span class="capitalize text-indigo-400 font-extrabold">{{ meetState.current_lift_type }}</span></p>
        <p><strong class="text-indigo-200">Current Attempt:</strong> <span class="text-indigo-400 font-extrabold">{{ meetState.current_attempt_number }}</span></p>
        <p><strong class="text-indigo-200">Active Lift ID:</strong> <span :class="{ 'text-green-400 font-semibold': meetState.current_active_lift_id, 'text-gray-500 italic': !meetState.current_active_lift_id }">{{ meetState.current_active_lift_id || 'None' }}</span></p>
      </div>
      <div v-else class="text-gray-500 text-xl">Loading meet state...</div>

      <div class="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Buttons with new styling: gradient, rounded, shadow, hover effects -->
        <button
          @click="advanceAttempt"
          class="
            bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-600 hover:to-blue-700
            text-white font-bold py-3 px-6 rounded-xl shadow-lg transition duration-300 ease-in-out
            transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-teal-500 focus:ring-opacity-50
          ">
          Advance Attempt
        </button>
        <button
          @click="setLiftType('squat')"
          class="
            bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700
            text-white font-bold py-3 px-6 rounded-xl shadow-lg transition duration-300 ease-in-out
            transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-purple-500 focus:ring-opacity-50
          ">
          Set Squat
        </button>
        <button
          @click="setLiftType('bench')"
          class="
            bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700
            text-white font-bold py-3 px-6 rounded-xl shadow-lg transition duration-300 ease-in-out
            transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-purple-500 focus:ring-opacity-50
          ">
          Set Bench
        </button>
        <button
          @click="setLiftType('deadlift')"
          class="
            bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700
            text-white font-bold py-3 px-6 rounded-xl shadow-lg transition duration-300 ease-in-out
            transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-purple-500 focus:ring-opacity-50
          ">
          Set Deadlift
        </button>
        <button
          @click="resetMeet"
          class="
            bg-red-600 hover:bg-red-700 active:bg-red-800
            text-white font-bold py-3 px-6 rounded-xl shadow-lg transition duration-300 ease-in-out
            transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-red-500 focus:ring-opacity-50
          ">
          Reset Meet
        </button>
      </div>
    </div>

    <!-- Add Lifter Section -->
    <div class="mb-8 p-6 bg-gray-800 rounded-2xl shadow-xl border border-gray-700">
      <h2 class="text-3xl font-bold text-green-300 mb-4 flex items-center">
        <svg
          class="mr-3 h-6 w-6 text-green-400"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg">
          <path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-6-9e7H5a2 2 0 00-2 2v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3.328c-.283-.585-.595-1.096-.925-1.536C12.435 4.095 11.233 4 10 4s-2.435.095-3.747.464c-.33.44-.642.951-.925 1.536H5z" />
        </svg>
        Add Lifter
      </h2>
      <form @submit.prevent="addLifter" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label for="lifterName" class="block text-gray-400 text-sm font-bold mb-2">Lifter Name:</label>
          <input
            type="text"
            id="lifterName"
            v-model="newLifter.lifter_name"
            required
            class="
              w-full p-3 rounded-lg bg-gray-700 text-white border border-gray-600
              focus:ring-2 focus:ring-green-500 focus:border-transparent
              transition duration-200 ease-in-out
            "
          />
        </div>
        <div>
          <label for="lifterId" class="block text-gray-400 text-sm font-bold mb-2">Lifter ID Number:</label>
          <input
            type="text"
            id="lifterId"
            v-model="newLifter.lifter_id_number"
            required
            class="
              w-full p-3 rounded-lg bg-gray-700 text-white border border-gray-600
              focus:ring-2 focus:ring-green-500 focus:border-transparent
              transition duration-200 ease-in-out
            "
          />
        </div>
        <div class="md:col-span-2">
          <button
            type="submit"
            class="
              w-full
              bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700
              text-white font-bold py-3 px-6 rounded-xl shadow-lg transition duration-300 ease-in-out
              transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-green-500 focus:ring-opacity-50
            ">
            Add Lifter
          </button>
        </div>
        <p v-if="lifterAddMessage" :class="lifterAddMessageType === 'success' ? 'text-green-400' : 'text-red-400'" class="md:col-span-2 mt-2">{{ lifterAddMessage }}</p>
      </form>
    </div>

    <!-- Current Active Lift Display -->
    <div class="mb-8 p-6 bg-gray-800 rounded-2xl shadow-xl border border-gray-700">
      <h2 class="text-3xl font-bold text-yellow-300 mb-4 flex items-center">
        <svg
          class="mr-3 h-6 w-6 text-yellow-400"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg">
          <path
            d="M13 10V3L4 14h7v7l9-11h-7z"
            stroke-linecap="round"
            stroke-linejoin="round" />
        </svg>
        Current Active Lift
      </h2>
      <div v-if="currentLift" class="bg-indigo-700 p-6 rounded-md border-2 border-indigo-500 text-center">
        <p class="text-4xl font-extrabold mb-2 text-white">
          {{ currentLift.lifter_name }}
        </p>
        <p class="text-2xl text-indigo-200 mb-3">
          ID: {{ currentLift.lifter_id_number }} |
          {{ currentLift.lift_type ? currentLift.lift_type.toUpperCase() : '' }} | Attempt
          {{ currentLift.attempt_number }}
        </p>
        <p class="text-6xl font-black text-yellow-300 mb-4">
          {{ currentLift.weight_lifted }} kg
        </p>
      </div>
      <div v-else class="text-gray-500 italic text-2xl text-center">
        No lifter currently active.
      </div>
      
      <div class="mt-8">
        <button
          @click="advanceToNextLift"
          class="
            w-full
            bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700
            text-white font-bold py-3 px-6 rounded-xl shadow-lg transition duration-300 ease-in-out
            transform hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-orange-500 focus:ring-opacity-50
          ">
          Advance to Next Lift (Set Active)
        </button>
      </div>
    </div>

    <!-- Lifters List -->
    <div class="p-6 bg-gray-800 rounded-2xl shadow-xl border border-gray-700">
      <h2 class="text-3xl font-bold text-blue-300 mb-4 flex items-center">
        <svg
          class="mr-3 h-6 w-6 text-blue-400"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-3M17 14h.01M10 6h.01M10 12h.01M10 18h.01M4 14h.01M4 20h.01M4 6h.01M7 10h10a.75.75 0 00.75-.75V5.25a.75.75 0 00-.75-.75H7a.75.75 0 00-.75.75v4.5c0 .414.336.75.75.75z" />
        </svg>
        Registered Lifters
      </h2>
      <div v-if="lifters.length > 0">
        <div class="overflow-x-auto">
          <table class="min-w-full bg-gray-700 text-white rounded-lg overflow-hidden text-lg">
            <thead class="bg-gray-600">
              <tr class="text-left text-sm font-semibold uppercase tracking-wider text-gray-300">
                <th class="px-6 py-3">Name</th>
                <th class="px-6 py-3">ID</th>
                <th class="px-6 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="lifter in lifters"
                :key="lifter.id"
                class="border-t border-gray-600 hover:bg-gray-600">
                <td class="px-6 py-4">{{ lifter.lifter_name }}</td>
                <td class="px-6 py-4">{{ lifter.lifter_id_number }}</td>
                <td class="px-6 py-4 text-center">
                  <button
                    @click="deleteLifter(lifter.id)"
                    class="
                      bg-red-500 hover:bg-red-600 active:bg-red-700
                      text-white font-bold py-2 px-4 rounded-md shadow-sm transition duration-200 ease-in-out
                      focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2 focus:ring-offset-gray-800
                    ">
                    Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else class="italic text-gray-500 text-2xl text-center">
        No lifters registered yet.
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
const lifters = ref([]);
const newLifter = ref({ lifter_name: "", lifter_id_number: "" });
const lifterAddMessage = ref(null);
const lifterAddMessageType = ref(null);

const BACKEND_API_URL = "https://powerlifting-meet-system24.onrender.com";
const SOCKET_IO_URL = "https://powerlifting-meet-system24.onrender.com";

// Initialize Socket.IO connection
const socket = io(SOCKET_IO_URL);

// --- Utility Functions ---
const showLifterAddMessage = (message, type) => {
  lifterAddMessage.value = message;
  lifterAddMessageType.value = type;
  setTimeout(() => {
    lifterAddMessage.value = null;
    lifterAddMessageType.value = null;
  }, 3000); // Message disappears after 3 seconds
};

// --- Fetching Functions ---
const fetchMeetState = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state`);
    const data = await response.json();
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
      // Check if data is an empty object, indicating no active lift
      currentLift.value = Object.keys(data).length > 0 ? data : null;
    } else {
      // If response is not ok, assume no current lift or an error
      currentLift.value = null;
      console.error("Failed to fetch current lift:", response.statusText);
    }
  } catch (error) {
    console.error("Network error fetching current lift:", error);
  }
};

const fetchLifters = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters`);
    const data = await response.json();
    lifters.value = data;
  } catch (error) {
    console.error("Error fetching lifters:", error);
  }
};

// --- Action Functions ---
const addLifter = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newLifter.value),
    });
    const data = await response.json();
    if (response.ok) {
      showLifterAddMessage("Lifter added successfully!", "success");
      newLifter.value = { lifter_name: "", lifter_id_number: "" }; // Clear form
      fetchLifters(); // Refresh list
    } else {
      showLifterAddMessage(data.error || "Failed to add lifter.", "error");
    }
  } catch (error) {
    console.error("Network error adding lifter:", error);
    showLifterAddMessage("Network error adding lifter.", "error");
  }
};

const deleteLifter = async (id) => {
  if (confirm("Are you sure you want to delete this lifter?")) { // Use custom modal in future
    try {
      const response = await fetch(`${BACKEND_API_URL}/lifters/${id}`, {
        method: "DELETE",
      });
      if (response.ok) {
        fetchLifters(); // Refresh list
      } else {
        const errorData = await response.json();
        console.error("Failed to delete lifter:", errorData.error);
        alert(errorData.error || "Failed to delete lifter."); // Use custom modal in future
      }
    } catch (error) {
      console.error("Network error deleting lifter:", error);
      alert("Network error deleting lifter."); // Use custom modal in future
    }
  }
};

const advanceAttempt = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state/next_attempt`, {
      method: "POST",
    });
    if (response.ok) {
      // Backend should emit meet_state_updated and active_lift_changed via Socket.IO
      // No need to manually refetch here if Socket.IO handles updates
    } else {
      const errorData = await response.json();
      console.error("Failed to advance attempt:", errorData.error);
      alert(errorData.error || "Failed to advance attempt."); // Use custom modal in future
    }
  } catch (error) {
    console.error("Network error advancing attempt:", error);
    alert("Network error advancing attempt."); // Use custom modal in future
  }
};

const setLiftType = async (liftType) => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state/set_lift_type`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lift_type: liftType }),
    });
    if (response.ok) {
      // Backend should emit meet_state_updated and active_lift_changed via Socket.IO
    } else {
      const errorData = await response.json();
      console.error(`Failed to set lift type to ${liftType}:`, errorData.error);
      alert(errorData.error || `Failed to set lift type to ${liftType}.`); // Use custom modal in future
    }
  } catch (error) {
    console.error(`Network error setting lift type to ${liftType}:`, error);
    alert(`Network error setting lift type to ${liftType}.`); // Use custom modal in future
  }
};

const resetMeet = async () => {
  if (confirm("Are you sure you want to RESET THE ENTIRE MEET? This cannot be undone!")) { // Use custom modal
    try {
      const response = await fetch(`${BACKEND_API_URL}/reset_meet`, {
        method: 'POST'
      });
      if (response.ok) {
        // Handle successful reset, e.g., clear local state, show message
        alert("Meet successfully reset!"); // Use custom modal
        // Trigger refetching of all initial data
        fetchMeetState();
        fetchCurrentLift();
        fetchLifters();
      } else {
        const errorData = await response.json();
        console.error("Failed to reset meet:", errorData.error);
        alert(errorData.error || "Failed to reset meet."); // Use custom modal
      }
    } catch (error) {
      console.error("Network error resetting meet:", error);
      alert("Network error resetting meet."); // Use custom modal
    }
  }
};

const advanceToNextLift = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state/set_active_lift`, {
      method: "POST",
    });
    if (response.ok) {
      // Backend should emit meet_state_updated and active_lift_changed via Socket.IO
    } else {
      const errorData = await response.json();
      console.error("Failed to advance to next lift:", errorData.error);
      alert(errorData.error || "Failed to advance to next lift."); // Use custom modal
    }
  } catch (error) {
    console.error("Network error advancing to next lift:", error);
    alert("Network error advancing to next lift."); // Use custom modal
  }
};


// --- Socket.IO Event Listeners ---
onMounted(() => {
  // Initial fetches
  fetchMeetState();
  fetchCurrentLift();
  fetchLifters();

  socket.on("connect", () => {
    console.log("Connected to Socket.IO from OrganizerView");
  });

  socket.on("disconnect", () => {
    console.log("Disconnected from Socket.IO in OrganizerView");
  });

  socket.on("meet_state_updated", (_data) => {
    console.log("Meet state updated via Socket.IO:", _data);
    meetState.value = _data;
    fetchCurrentLift(); // Active lift might change with state
    fetchLifters(); // Lifter list might be affected by reset
  });

  socket.on("active_lift_changed", (_data) => {
    console.log("Active lift changed via Socket.IO:", _data);
    currentLift.value = _data;
  });

  socket.on("lifter_list_updated", () => {
    console.log("Lifter list updated via Socket.IO.");
    fetchLifters();
  });
});

// Watchers
watch(meetState, (newMeetState) => {
  if (newMeetState) {
    // Optionally trigger more fetches or logic based on new meet state
  }
});
</script>

<style scoped>
/* No custom styles needed beyond Tailwind for this example,
   but you can add them here if necessary */
</style>
