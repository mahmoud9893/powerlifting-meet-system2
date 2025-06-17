<template>
  <div class="organizer-view p-6 bg-gray-100 min-h-screen">
    <h1 class="text-3xl font-bold text-gray-800 mb-6 border-b pb-2">Organizer Dashboard</h1>

    <!-- Current Meet State & Actions -->
    <div class="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 class="text-2xl font-semibold text-gray-700 mb-4 flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l-5 4V21M9 19c-3.111 0-7-1.488-7-4s1.956-2 7-2m0 0v-5c0 1.25.968 2.5 3 2.5s3-1.25 3-2.5V4m0 0c0 1.25.968 2.5 3 2.5s3-1.25 3-2.5V4m-3 10v-4m-3 4v-4" />
        </svg>
        Meet State
      </h2>
      <div v-if="meetState" class="grid grid-cols-1 md:grid-cols-2 gap-4 text-lg">
        <p><strong>Current Lift Type:</strong> <span class="capitalize text-indigo-700 font-medium">{{ meetState.current_lift_type }}</span></p>
        <p><strong>Current Attempt:</strong> <span class="text-indigo-700 font-medium">{{ meetState.current_attempt_number }}</span></p>
        <p>
          <strong>Active Lift ID:</strong>
          <span :class="{'text-green-600 font-medium': meetState.current_active_lift_id, 'text-gray-500 italic': !meetState.current_active_lift_id}">
            {{ meetState.current_active_lift_id || 'None' }}
          </span>
        </p>
      </div>
      <div v-else class="text-gray-600">Loading meet state...</div>

      <div class="mt-6 border-t pt-4">
        <h3 class="text-xl font-semibold text-gray-700 mb-3">Control Panel</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <button @click="changeLiftType('squat')" class="btn-primary" :class="{'bg-indigo-700': meetState?.current_lift_type === 'squat'}">Set Squat</button>
          <button @click="changeLiftType('bench')" class="btn-primary" :class="{'bg-indigo-700': meetState?.current_lift_type === 'bench'}">Set Bench</button>
          <button @click="changeLiftType('deadlift')" class="btn-primary" :class="{'bg-indigo-700': meetState?.current_lift_type === 'deadlift'}">Set Deadlift</button>
          <button @click="advanceAttempt" class="btn-secondary" :disabled="meetState?.current_attempt_number === 3">Advance Attempt ({{ meetState?.current_attempt_number || 0 }}/3)</button>
          <button @click="setActiveLift(null)" class="btn-success">Auto Set Next Active Lift</button>
          <button @click="exportMeetData" class="btn-info">Export Meet Data (Excel)</button>
        </div>
      </div>
    </div>

    <!-- Current Active Lift Details -->
    <div class="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 class="text-2xl font-semibold text-gray-700 mb-4 flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Current Active Lift
      </h2>
      <div v-if="currentLift" class="border p-4 rounded-md bg-indigo-50 border-indigo-200">
        <p class="text-xl font-bold text-indigo-800 mb-2">{{ currentLift.lifter_name }} ({{ currentLift.lifter_id_number }}) - {{ currentLift.lift_type.toUpperCase() }}</p>
        <p class="text-lg">Weight: <span class="font-semibold">{{ currentLift.weight_lifted }} kg</span> | Attempt: <span class="font-semibold">{{ currentLift.attempt_number }}</span></p>
        <p class="text-sm text-gray-600">Status: {{ currentLift.status }}</p>
        <div class="mt-3">
          <p>Judge 1: <span :class="scoreClass(currentLift.judge1_score)">{{ formatScore(currentLift.judge1_score) }}</span></p>
          <p>Judge 2: <span :class="scoreClass(currentLift.judge2_score)">{{ formatScore(currentLift.judge2_score) }}</span></p>
          <p>Judge 3: <span :class="scoreClass(currentLift.judge3_score)">{{ formatScore(currentLift.judge3_score) }}</span></p>
          <p class="font-bold mt-2">Overall Result: <span :class="overallResultClass(currentLift.overall_result)">{{ formatOverallResult(currentLift.overall_result) }}</span></p>
        </div>
      </div>
      <div v-else class="text-gray-600 italic">No lift currently active.</div>
    </div>

    <!-- Pending Lifts in Queue -->
    <div class="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 class="text-2xl font-semibold text-gray-700 mb-4 flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Next Lifts in Queue ({{ meetState?.current_lift_type }} - Attempt {{ meetState?.current_attempt_number }})
      </h2>
      <div v-if="nextLiftsInQueue.length > 0">
        <div class="overflow-x-auto">
          <table class="min-w-full bg-white border border-gray-200">
            <thead>
              <tr class="bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                <th class="py-3 px-6 border-b-2 border-gray-200">Lifter Name</th>
                <th class="py-3 px-6 border-b-2 border-gray-200">Lifter ID</th>
                <th class="py-3 px-6 border-b-2 border-gray-200">Weight</th>
                <th class="py-3 px-6 border-b-2 border-gray-200">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lift in nextLiftsInQueue" :key="lift.id" class="hover:bg-gray-50">
                <td class="py-4 px-6 border-b border-gray-200">{{ lift.lifter_name }}</td>
                <td class="py-4 px-6 border-b border-gray-200">{{ lift.lifter_id_number }}</td>
                <td class="py-4 px-6 border-b border-gray-200">{{ lift.weight_lifted }} kg</td>
                <td class="py-4 px-6 border-b border-gray-200">
                  <button @click="setActiveLift(lift.id)" class="btn-small-primary">Set Active</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else class="text-gray-600 italic">No pending lifts for the current type and attempt.</div>
    </div>

    <!-- Lifter Management -->
    <div class="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 class="text-2xl font-semibold text-gray-700 mb-4 flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H2v-2a3 3 0 015.356-1.857M17 20v-2c0-.653-.106-1.294-.308-1.884c.3-.12.63-.19.968-.19h.324c1.652 0 3-1.348 3-3V7a3 3 0 00-3-3H4a3 3 0 00-3 3v7c0 1.652 1.348 3 3 3h.324c.338 0 .668.07.968.19A3 3 0 007 18v2H2" />
        </svg>
        Lifter Management
      </h2>

      <div class="mb-6 border p-4 rounded-md bg-gray-50">
        <h3 class="text-xl font-semibold text-gray-700 mb-3">Add New Lifter</h3>
        <form @submit.prevent="addLifter" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input type="text" v-model="newLifter.name" placeholder="Name" required class="form-input" />
          <select v-model="newLifter.gender" required class="form-select">
            <option value="" disabled>Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
          <input type="text" v-model="newLifter.lifter_id_number" placeholder="Lifter ID" required class="form-input" />
          <input type="number" step="0.01" v-model.number="newLifter.actual_weight" placeholder="Actual Weight (kg)" required class="form-input" />
          <input type="date" v-model="newLifter.birth_date" placeholder="Birth Date" required class="form-input" />
          <input type="number" step="0.01" v-model.number="newLifter.opener_squat" placeholder="Opener Squat (kg)" required class="form-input" />
          <input type="number" step="0.01" v-model.number="newLifter.opener_bench" placeholder="Opener Bench (kg)" required class="form-input" />
          <input type="number" step="0.01" v-model.number="newLifter.opener_deadlift" placeholder="Opener Deadlift (kg)" required class="form-input" />
          <button type="submit" class="btn-primary col-span-full">Add Lifter</button>
        </form>
      </div>

      <h3 class="text-xl font-semibold text-gray-700 mb-3 mt-8">All Registered Lifters</h3>
      <div v-if="allLifters.length > 0" class="overflow-x-auto">
        <table class="min-w-full bg-white border border-gray-200">
          <thead>
            <tr class="bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              <th class="py-3 px-6 border-b-2 border-gray-200">Name</th>
              <th class="py-3 px-6 border-b-2 border-gray-200">ID</th>
              <th class="py-3 px-6 border-b-2 border-gray-200">Gender</th>
              <th class="py-3 px-6 border-b-2 border-gray-200">Age</th>
              <th class="py-3 px-6 border-b-2 border-gray-200">Weight</th>
              <th class="py-3 px-6 border-b-2 border-gray-200">Primary WC</th>
              <th class="py-3 px-6 border-b-2 border-gray-200">Primary AC</th>
              <th class="py-3 px-6 border-b-2 border-gray-200">Addtl WC</th>
              <th class="py-3 px-6 border-b-2 border-gray-200">Addtl AC</th>
              <th class="py-3 px-6 border-b-2 border-gray-200">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lifter in allLifters" :key="lifter.id" class="hover:bg-gray-50">
              <td class="py-4 px-6 border-b border-gray-200">{{ lifter.name }}</td>
              <td class="py-4 px-6 border-b border-gray-200">{{ lifter.lifter_id_number }}</td>
              <td class="py-4 px-6 border-b border-gray-200">{{ lifter.gender }}</td>
              <td class="py-4 px-6 border-b border-gray-200">{{ lifter.age }}</td>
              <td class="py-4 px-6 border-b border-gray-200">{{ lifter.actual_weight }} kg</td>
              <td class="py-4 px-6 border-b border-gray-200">{{ lifter.primary_weight_class_name }}</td>
              <td class="py-4 px-6 border-b border-gray-200">{{ lifter.primary_age_class_name }}</td>
              <td class="py-4 px-6 border-b border-gray-200">
                <select v-model="lifter.selectedAdditionalWeightClass" class="form-select text-sm p-1">
                  <option :value="null">Add Class</option>
                  <option v-for="wc in availableWeightClasses(lifter)" :key="wc.id" :value="wc.id">{{ wc.name }}</option>
                </select>
                <button @click="addAdditionalWeightClass(lifter.id, lifter.selectedAdditionalWeightClass)" :disabled="!lifter.selectedAdditionalWeightClass" class="btn-small-secondary mt-1">Add</button>
                <div class="flex flex-wrap mt-1">
                  <span v-for="wcName in lifter.additional_weight_class_names" :key="wcName" class="badge-class mr-1 mb-1 bg-blue-200 text-blue-800">
                    {{ wcName }} <button @click="removeAdditionalWeightClass(lifter.id, getWeightClassIdByName(wcName))" class="ml-1 text-blue-600 hover:text-blue-900 font-bold">&times;</button>
                  </span>
                </div>
              </td>
              <td class="py-4 px-6 border-b border-gray-200">
                <select v-model="lifter.selectedAdditionalAgeClass" class="form-select text-sm p-1">
                  <option :value="null">Add Class</option>
                  <option v-for="ac in availableAgeClasses(lifter)" :key="ac.id" :value="ac.id">{{ ac.name }}</option>
                </select>
                <button @click="addAdditionalAgeClass(lifter.id, lifter.selectedAdditionalAgeClass)" :disabled="!lifter.selectedAdditionalAgeClass" class="btn-small-secondary mt-1">Add</button>
                <div class="flex flex-wrap mt-1">
                  <span v-for="acName in lifter.additional_age_class_names" :key="acName" class="badge-class mr-1 mb-1 bg-purple-200 text-purple-800">
                    {{ acName }} <button @click="removeAdditionalAgeClass(lifter.id, getAgeClassIdByName(acName))" class="ml-1 text-purple-600 hover:text-purple-900 font-bold">&times;</button>
                  </span>
                </div>
              </td>
              <td class="py-4 px-6 border-b border-gray-200">
                <!-- Add more actions like edit lifter if needed -->
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-gray-600 italic">No lifters registered.</div>
    </div>

    <!-- Class Management -->
    <div class="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 class="text-2xl font-semibold text-gray-700 mb-4 flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
        </svg>
        Class Management
      </h2>

      <!-- Weight Class Management -->
      <div class="mb-6 border p-4 rounded-md bg-gray-50">
        <h3 class="text-xl font-semibold text-gray-700 mb-3">Weight Classes</h3>
        <form @submit.prevent="addWeightClass" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <input type="text" v-model="newWeightClass.name" placeholder="Class Name (e.g., Men's 83kg)" required class="form-input" />
          <input type="number" step="0.01" v-model.number="newWeightClass.min_weight" placeholder="Min Weight (kg)" required class="form-input" />
          <input type="number" step="0.01" v-model.number="newWeightClass.max_weight" placeholder="Max Weight (kg, optional)" class="form-input" />
          <select v-model="newWeightClass.gender" required class="form-select">
            <option value="" disabled>Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Both">Both</option>
          </select>
          <button type="submit" class="btn-primary col-span-full">Add Weight Class</button>
        </form>
        <ul class="list-disc pl-5">
          <li v-for="wc in weightClasses" :key="wc.id" class="flex justify-between items-center py-1">
            {{ wc.name }} ({{ wc.min_weight }}kg - {{ wc.max_weight ? wc.max_weight + 'kg' : 'Open' }}) [{{ wc.gender }}]
            <button @click="deleteWeightClass(wc.id)" class="btn-small-danger">Delete</button>
          </li>
        </ul>
      </div>

      <!-- Age Class Management -->
      <div class="mb-6 border p-4 rounded-md bg-gray-50 mt-8">
        <h3 class="text-xl font-semibold text-gray-700 mb-3">Age Classes</h3>
        <form @submit.prevent="addAgeClass" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <input type="text" v-model="newAgeClass.name" placeholder="Class Name (e.g., Junior)" required class="form-input" />
          <input type="number" v-model.number="newAgeClass.min_age" placeholder="Min Age" required class="form-input" />
          <input type="number" v-model.number="newAgeClass.max_age" placeholder="Max Age (optional)" class="form-input" />
          <button type="submit" class="btn-primary col-span-full">Add Age Class</button>
        </form>
        <ul class="list-disc pl-5">
          <li v-for="ac in ageClasses" :key="ac.id" class="flex justify-between items-center py-1">
            {{ ac.name }} ({{ ac.min_age }} - {{ ac.max_age ? ac.max_age + ' years' : 'Open' }})
            <button @click="deleteAgeClass(ac.id)" class="btn-small-danger">Delete</button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { io } from "socket.io-client";

// Reactive state variables
const meetState = ref(null);
const currentLift = ref(null);
const allLifters = ref([]);
const nextLiftsInQueue = ref([]);
const weightClasses = ref([]);
const ageClasses = ref([]);

const newLifter = ref({
  name: "",
  gender: "",
  lifter_id_number: "",
  actual_weight: null,
  birth_date: "",
  opener_squat: null,
  opener_bench: null,
  opener_deadlift: null,
});

const newWeightClass = ref({
  name: "",
  min_weight: null,
  max_weight: null,
  gender: "",
});

const newAgeClass = ref({
  name: "",
  min_age: null,
  max_age: null,
});

// Determine API URL based on environment
const BACKEND_API_URL = process.env.VUE_APP_BACKEND_API_URL || "http://localhost:5000";
const SOCKET_IO_URL = process.env.VUE_APP_BACKEND_API_URL || "http://localhost:5000";

// Initialize Socket.IO connection
const socket = io(SOCKET_IO_URL);

// --- Utility Functions for Display ---
const formatScore = (score) => {
  if (score === true) return "GOOD";
  if (score === false) return "BAD";
  return "N/A";
};

const scoreClass = (score) => {
  if (score === true) return "text-green-600 font-semibold";
  if (score === false) return "text-red-600 font-semibold";
  return "text-gray-500 italic";
};

const formatOverallResult = (result) => {
  if (result === true) return "GOOD LIFT";
  if (result === false) return "NO LIFT";
  return "PENDING";
};

const overallResultClass = (result) => {
  if (result === true) return "text-green-700 font-bold";
  if (result === false) return "text-red-700 font-bold";
  return "text-orange-500 italic";
};

// Computed properties for dropdowns to filter available classes for lifters
const availableWeightClasses = (lifter) => {
  return weightClasses.value.filter(
    (wc) =>
      wc.id !== lifter.primary_weight_class_id &&
      !lifter.additional_weight_class_ids.includes(wc.id)
  );
};

const availableAgeClasses = (lifter) => {
  return ageClasses.value.filter(
    (ac) =>
      ac.id !== lifter.primary_age_class_id &&
      !lifter.additional_age_class_ids.includes(ac.id)
  );
};

// Helper to get ID by name (needed for removing additional classes by name)
const getWeightClassIdByName = (name) => {
  const wc = weightClasses.value.find((wc) => wc.name === name);
  return wc ? wc.id : null;
};

const getAgeClassIdByName = (name) => {
  const ac = ageClasses.value.find((ac) => ac.name === name);
  return ac ? ac.id : null;
};

// --- Fetching Functions ---
const fetchMeetState = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state`);
    const data = await response.json();
    meetState.value = data;
  } catch (error) {
    alert("Error fetching meet state. See console for details.");
  }
};

const fetchLifters = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters`);
    const data = await response.json();
    allLifters.value = data.map((lifter) => ({
      ...lifter,
      selectedAdditionalWeightClass: null,
      selectedAdditionalAgeClass: null,
    }));
  } catch (error) {
    alert("Error fetching lifters. See console for details.");
  }
};

const fetchCurrentLift = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/current_lift`);
    if (response.ok) {
      const data = await response.json();
      currentLift.value = data;
    } else {
      currentLift.value = null; // No active lift
    }
  } catch (error) {
    alert("Error fetching current lift. See console for details.");
  }
};

const fetchNextLiftsInQueue = async () => {
  try {
    // This endpoint triggers backend queue logic if needed, then fetches current queue
    await fetch(`${BACKEND_API_URL}/next_lift_in_queue`); 
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
    alert("Error fetching next lifts in queue. See console for details.");
  }
};

const fetchWeightClasses = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/weight_classes`);
    const data = await response.json();
    weightClasses.value = data;
  } catch (error) {
    alert("Error fetching weight classes. See console for details.");
  }
};

const fetchAgeClasses = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/age_classes`);
    const data = await response.json();
    ageClasses.value = data;
  } catch (error) {
    alert("Error fetching age classes. See console for details.");
  }
};

// --- Actions / API Calls ---
const changeLiftType = async (liftType) => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_lift_type: liftType }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      alert(`Failed to change lift type: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    alert("Network error or unexpected error while changing lift type.");
  }
};

const advanceAttempt = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state/advance_attempt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) {
      const errorData = await response.json();
      alert(`Failed to advance attempt: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    alert("Network error or unexpected error while advancing attempt.");
  }
};

const addLifter = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newLifter.value),
    });
    if (response.ok) {
      newLifter.value = {
        name: "",
        gender: "",
        lifter_id_number: "",
        actual_weight: null,
        birth_date: "",
        opener_squat: null,
        opener_bench: null,
        opener_deadlift: null,
      };
      await fetchLifters(); // Refresh lifters after adding
    } else {
      const errorData = await response.json();
      alert(`Failed to add lifter: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    alert("Network error or unexpected error while adding lifter.");
  }
};

const setActiveLift = async (liftId) => {
  try {
    const payload = liftId ? { lift_id: liftId } : {};
    const response = await fetch(`${BACKEND_API_URL}/set_active_lift`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorData = await response.json();
      alert(`Failed to set active lift: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    alert("Network error or unexpected error while setting active lift.");
  }
};

const addWeightClass = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/weight_classes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newWeightClass.value),
    });
    if (response.ok) {
      newWeightClass.value = {
        name: "",
        min_weight: null,
        max_weight: null,
        gender: "",
      };
      fetchWeightClasses(); // Refresh list
      fetchLifters(); // Lifters might be re-assigned, refresh them too
    } else {
      const errorData = await response.json();
      alert(`Failed to add weight class: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    alert("Network error or unexpected error while adding weight class.");
  }
};

const deleteWeightClass = async (wcId) => {
  if (!confirm("Are you sure you want to delete this weight class? This cannot be undone if lifters are assigned!")) {
    return;
  }
  try {
    const response = await fetch(`${BACKEND_API_URL}/weight_classes/${wcId}`, {
      method: "DELETE",
    });
    if (response.ok) {
      fetchWeightClasses();
      fetchLifters(); // Lifters might be re-assigned, refresh them too
    } else {
      const errorData = await response.json();
      alert(`Failed to delete weight class: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    alert("Network error or unexpected error while deleting weight class.");
  }
};

const addAgeClass = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/age_classes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newAgeClass.value),
    });
    if (response.ok) {
      newAgeClass.value = { name: "", min_age: null, max_age: null };
      fetchAgeClasses(); // Refresh list
      fetchLifters(); // Lifters might be re-assigned, refresh them too
    } else {
      const errorData = await response.json();
      alert(`Failed to add age class: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    alert("Network error or unexpected error while adding age class.");
  }
};

const deleteAgeClass = async (acId) => {
  if (!confirm("Are you sure you want to delete this age class? This cannot be undone if lifters are assigned!")) {
    return;
  }
  try {
    const response = await fetch(`${BACKEND_API_URL}/age_classes/${acId}`, {
      method: "DELETE",
    });
    if (response.ok) {
      fetchAgeClasses();
      fetchLifters(); // Lifters might be re-assigned, refresh them too
    } else {
      const errorData = await response.json();
      alert(`Failed to delete age class: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    alert("Network error or unexpected error while deleting age class.");
  }
};

const addAdditionalWeightClass = async (lifterId, weightClassId) => {
  if (!weightClassId) return;
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters/${lifterId}/add_additional_weight_class`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weight_class_id: weightClassId }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      alert(`Failed to add additional weight class: ${errorData.error || response.statusText}`);
    } else {
      fetchLifters(); // Refresh lifter data
    }
  } catch (error) {
    alert("Network error or unexpected error while adding additional weight class.");
  }
};

const removeAdditionalWeightClass = async (lifterId, weightClassId) => {
  if (!confirm("Are you sure you want to remove this additional weight class?")) {
    return;
  }
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters/${lifterId}/remove_additional_weight_class`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weight_class_id: weightClassId }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      alert(`Failed to remove additional weight class: ${errorData.error || response.statusText}`);
    } else {
      fetchLifters(); // Refresh lifter data
    }
  } catch (error) {
    alert("Network error or unexpected error while removing additional weight class.");
  }
};

const addAdditionalAgeClass = async (lifterId, ageClassId) => {
  if (!ageClassId) return;
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters/${lifterId}/add_additional_age_class`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ age_class_id: ageClassId }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      alert(`Failed to add additional age class: ${errorData.error || response.statusText}`);
    } else {
      fetchLifters(); // Refresh lifter data
    }
  } catch (error) {
    alert("Network error or unexpected error while adding additional age class.");
  }
};

const removeAdditionalAgeClass = async (lifterId, ageClassId) => {
  if (!confirm("Are you sure you want to remove this additional age class?")) {
    return;
  }
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters/${lifterId}/remove_additional_age_class`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ age_class_id: ageClassId }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      alert(`Failed to remove additional age class: ${errorData.error || response.statusText}`);
    } else {
      fetchLifters(); // Refresh lifter data
    }
  } catch (error) {
    alert("Network error or unexpected error while removing additional age class.");
  }
};

const exportMeetData = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/export_meet_data`);
    if (response.ok) {
      alert("Meet data export triggered on backend. Check backend logs for file path.");
      // In a real application, you'd typically get a downloadable file directly from the response.
      // For now, it just confirms the backend process.
    } else {
      const errorData = await response.json();
      alert(`Failed to export data: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    alert("Network error or unexpected error during data export.");
  }
};

// --- Socket.IO Event Listeners ---
onMounted(() => {
  fetchMeetState();
  fetchLifters();
  fetchWeightClasses();
  fetchAgeClasses();

  socket.on("connect", () => {
    // console.log("Connected to Socket.IO from OrganizerView");
  });

  socket.on("meet_state_updated", (data) => {
    // console.log("Meet state updated via Socket.IO:", data);
    meetState.value = data;
    fetchCurrentLift(); // Refetch active lift if meet state changes (e.g., attempt or lift type)
    fetchNextLiftsInQueue(); // Refetch queue
  });

  socket.on("active_lift_changed", (data) => {
    // console.log("Active lift changed via Socket.IO:", data);
    currentLift.value = data;
    fetchNextLiftsInQueue(); // Active lift changed, so queue might change
  });

  socket.on("lift_updated", (data) => {
    // console.log("Lift updated via Socket.IO:", data);
    if (currentLift.value && currentLift.value.id === data.id) {
      currentLift.value = data; // Update current active lift if it's the one that changed
    }
    fetchNextLiftsInQueue(); // A lift status changed, so queue might need refresh
  });

  socket.on("lifter_added", (data) => {
    // console.log("Lifter added via Socket.IO:", data);
    fetchLifters(); // Refresh all lifters
  });

  socket.on("lifter_updated", (data) => {
    // console.log("Lifter updated via Socket.IO:", data);
    fetchLifters(); // Refresh all lifters in case primary/additional classes changed
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
/* Basic Button Styles */
.btn-primary {
  @apply bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition duration-300 ease-in-out shadow-md;
}

.btn-secondary {
  @apply bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition duration-300 ease-in-out shadow-md;
}

.btn-success {
  @apply bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition duration-300 ease-in-out shadow-md;
}

.btn-info {
  @apply bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-300 ease-in-out shadow-md;
}

.btn-danger {
  @apply bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 transition duration-300 ease-in-out shadow-md;
}

.btn-small-primary {
  @apply bg-indigo-500 text-white py-1 px-2 text-sm rounded-md hover:bg-indigo-600 transition duration-300 ease-in-out;
}

.btn-small-secondary {
  @apply bg-gray-500 text-white py-1 px-2 text-sm rounded-md hover:bg-gray-600 transition duration-300 ease-in-out;
}

.btn-small-danger {
  @apply bg-red-500 text-white py-1 px-2 text-sm rounded-md hover:bg-red-600 transition duration-300 ease-in-out;
}

/* Form Input Styles */
.form-input {
  @apply p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500;
}

.form-select {
  @apply p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white;
}

/* Badge styles for additional classes */
.badge-class {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
}
</style>
