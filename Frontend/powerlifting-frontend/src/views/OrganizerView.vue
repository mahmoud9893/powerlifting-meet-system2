<template>
  <div class="organizer-view p-6 bg-gray-100 min-h-screen">
    <h1 class="mb-6 border-b pb-2 text-3xl font-bold text-gray-800">
      Organizer Dashboard
    </h1>

    <!-- Current Meet State & Actions -->
    <div class="mb-8 rounded-lg bg-white p-6 shadow-md">
      <h2 class="mb-4 flex items-center text-xl md:text-2xl font-semibold text-gray-700">
        <svg
          class="mr-2 h-5 w-5 md:h-6 md:w-6 text-indigo-600"
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
        Meet State
      </h2>
      <div
        v-if="meetState"
        class="grid grid-cols-1 gap-2 text-base md:text-lg md:grid-cols-2">
        <p>
          <strong>Current Lift Type:</strong>
          <span class="capitalize font-medium text-indigo-700">{{
            meetState.current_lift_type
          }}</span>
        </p>
        <p>
          <strong>Current Attempt:</strong>
          <span class="font-medium text-indigo-700">{{
            meetState.current_attempt_number
          }}</span>
        </p>
        <p>
          <strong>Active Lift ID:</strong>
          <span
            :class="{
              'font-medium text-green-600': meetState.current_active_lift_id,
              'italic text-gray-500': !meetState.current_active_lift_id,
            }">
            {{ meetState.current_active_lift_id || "None" }}
          </span>
        </p>
      </div>
      <div v-else class="text-gray-600 text-base md:text-lg">Loading meet state...</div>

      <div class="border-t pt-4 mt-6">
        <h3 class="mb-3 text-lg md:text-xl font-semibold text-gray-700">Control Panel</h3>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-4">
          <button
            :class="{ 'bg-indigo-700': meetState?.current_lift_type === 'squat' }"
            class="btn-primary"
            @click="changeLiftType('squat')">
            Set Squat
          </button>
          <button
            :class="{ 'bg-indigo-700': meetState?.current_lift_type === 'bench' }"
            class="btn-primary"
            @click="changeLiftType('bench')">
            Set Bench
          </button>
          <button
            :class="{ 'bg-indigo-700': meetState?.current_lift_type === 'deadlift' }"
            class="btn-primary"
            @click="changeLiftType('deadlift')">
            Set Deadlift
          </button>
          <button
            :disabled="meetState?.current_attempt_number === 3"
            class="btn-secondary"
            @click="advanceAttempt">
            Advance Attempt ({{ meetState?.current_attempt_number || 0 }}/3)
          </button>
          <button class="btn-success" @click="setActiveLift(null)">
            Auto Set Next Active Lift
          </button>
          <button class="btn-info" @click="exportMeetData">
            Export Meet Data (Excel)
          </button>
        </div>
      </div>
    </div>

    <!-- Current Active Lift Details -->
    <div class="mb-8 rounded-lg bg-white p-6 shadow-md">
      <h2 class="mb-4 flex items-center text-xl md:text-2xl font-semibold text-gray-700">
        <svg
          class="mr-2 h-5 w-5 md:h-6 md:w-6 text-indigo-600"
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
      <div
        v-if="currentLift"
        class="rounded-md border border-indigo-200 bg-indigo-50 p-4">
        <p class="mb-2 text-lg md:text-xl font-bold text-indigo-800">
          {{ currentLift.lifter_name }} ({{ currentLift.lifter_id_number }}) -
          {{ currentLift.lift_type.toUpperCase() }}
        </p>
        <p class="text-base md:text-lg">
          Weight:
          <span class="font-semibold">{{ currentLift.weight_lifted }} kg</span>
          | Attempt:
          <span class="font-semibold">{{ currentLift.attempt_number }}</span>
        </p>
        <p class="text-sm md:text-base text-gray-600">Status: {{ currentLift.status }}</p>
        <div class="mt-3 text-sm md:text-base">
          <p>
            Judge 1:
            <span :class="scoreClass(currentLift.judge1_score)">{{
              formatScore(currentLift.judge1_score)
            }}</span>
          </p>
          <p>
            Judge 2:
            <span :class="scoreClass(currentLift.judge2_score)">{{
              formatScore(currentLift.judge2_score)
            }}</span>
          </p>
          <p>
            Judge 3:
            <span :class="scoreClass(currentLift.judge3_score)">{{
              formatScore(currentLift.judge3_score)
            }}</span>
          </p>
          <p class="mt-2 font-bold text-base md:text-lg">
            Overall Result:
            <span :class="overallResultClass(currentLift.overall_result)">{{
              formatOverallResult(currentLift.overall_result)
            }}</span>
          </p>
        </div>
      </div>
      <div v-else class="italic text-gray-600 text-base md:text-lg">No lift currently active.</div>
    </div>

    <!-- Pending Lifts in Queue -->
    <div class="mb-8 rounded-lg bg-white p-6 shadow-md">
      <h2 class="mb-4 flex items-center text-xl md:text-2xl font-semibold text-gray-700">
        <svg
          class="mr-2 h-5 w-5 md:h-6 md:w-6 text-indigo-600"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg">
          <path
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            stroke-linecap="round"
            stroke-linejoin="round" />
        </svg>
        Next Lifts in Queue ({{ meetState?.current_lift_type }} - Attempt
        {{ meetState?.current_attempt_number }})
      </h2>
      <div v-if="nextLiftsInQueue.length > 0">
        <div class="overflow-x-auto">
          <table class="min-w-full border border-gray-200 bg-white text-sm md:text-base">
            <thead>
              <tr
                class="bg-gray-100 text-left text-xs md:text-sm font-semibold uppercase tracking-wider text-gray-600">
                <th class="border-b-2 border-gray-200 px-6 py-3">
                  Lifter Name
                </th>
                <th class="border-b-2 border-gray-200 px-6 py-3">Lifter ID</th>
                <th class="border-b-2 border-gray-200 px-6 py-3">Weight</th>
                <th class="border-b-2 border-gray-200 px-6 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="lift in nextLiftsInQueue"
                :key="lift.id"
                class="hover:bg-gray-50">
                <td class="border-b border-gray-200 px-6 py-4">
                  {{ lift.lifter_name }}
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                  {{ lift.lifter_id_number }}
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                  {{ lift.weight_lifted }} kg
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                  <button
                    class="btn-small-primary"
                    @click="setActiveLift(lift.id)">
                    Set Active
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else class="italic text-gray-600 text-base md:text-lg">
        No pending lifts for the current type and attempt.
      </div>
    </div>

    <!-- Lifter Management -->
    <div class="mb-8 rounded-lg bg-white p-6 shadow-md">
      <h2 class="mb-4 flex items-center text-xl md:text-2xl font-semibold text-gray-700">
        <svg
          class="mr-2 h-5 w-5 md:h-6 md:w-6 text-indigo-600"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg">
          <path
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H2v-2a3 3 0 015.356-1.857M17 20v-2c0-.653-.106-1.294-.308-1.884c.3-.12.63-.19.968-.19h.324c1.652 0 3-1.348 3-3V7a3 3 0 00-3-3H4a3 3 0 00-3 3v7c0 1.652 1.348 3 3 3h.324c.338 0 .668.07.968.19A3 3 0 007 18v2H2"
            stroke-linecap="round"
            stroke-linejoin="round" />
        </svg>
        Lifter Management
      </h2>

      <div class="mb-6 rounded-md border bg-gray-50 p-4">
        <h3 class="mb-3 text-lg md:text-xl font-semibold text-gray-700">Add New Lifter</h3>
        <form
          class="grid grid-cols-1 gap-4 md:grid-cols-2"
          @submit.prevent="addLifter">
          <input
            v-model="newLifter.name"
            class="form-input text-sm md:text-base"
            placeholder="Name"
            required
            type="text" />
          <select v-model="newLifter.gender" class="form-select text-sm md:text-base" required>
            <option value="" disabled>Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
          <input
            v-model="newLifter.lifter_id_number"
            class="form-input text-sm md:text-base"
            placeholder="Lifter ID"
            required
            type="text" />
          <input
            v-model.number="newLifter.actual_weight"
            class="form-input text-sm md:text-base"
            placeholder="Actual Weight (kg)"
            required
            step="0.01"
            type="number" />
          <input
            v-model="newLifter.birth_date"
            class="form-input text-sm md:text-base"
            placeholder="Birth Date"
            required
            type="date" />
          <input
            v-model.number="newLifter.opener_squat"
            class="form-input text-sm md:text-base"
            placeholder="Opener Squat (kg)"
            required
            step="0.01"
            type="number" />
          <input
            v-model.number="newLifter.opener_bench"
            class="form-input text-sm md:text-base"
            placeholder="Opener Bench (kg)"
            required
            step="0.01"
            type="number" />
          <input
            v-model.number="newLifter.opener_deadlift"
            class="form-input text-sm md:text-base"
            placeholder="Opener Deadlift (kg)"
            required
            step="0.01"
            type="number" />
          <button class="btn-primary col-span-full" type="submit">
            Add Lifter
          </button>
        </form>
      </div>

      <h3 class="mb-3 mt-8 text-lg md:text-xl font-semibold text-gray-700">
        All Registered Lifters
      </h3>
      <div v-if="allLifters.length > 0" class="overflow-x-auto">
        <table class="min-w-full border border-gray-200 bg-white text-sm md:text-base">
          <thead>
            <tr
              class="bg-gray-100 text-left text-xs md:text-sm font-semibold uppercase tracking-wider text-gray-600">
              <th class="border-b-2 border-gray-200 px-6 py-3">Name</th>
              <th class="border-b-2 border-gray-200 px-6 py-3">ID</th>
              <th class="border-b-2 border-gray-200 px-6 py-3">Gender</th>
              <th class="border-b-2 border-gray-200 px-6 py-3">Age</th>
              <th class="border-b-2 border-gray-200 px-6 py-3">Weight</th>
              <th class="border-b-2 border-gray-200 px-6 py-3">Primary WC</th>
              <th class="border-b-2 border-gray-200 px-6 py-3">Primary AC</th>
              <th class="border-b-2 border-gray-200 px-6 py-3">Addtl WC</th>
              <th class="border-b-2 border-gray-200 px-6 py-3">Addtl AC</th>
              <th class="border-b-2 border-gray-200 px-6 py-3">Actions</th>
            </tr>
          </thead>
            <tbody>
            <tr
                v-for="lifter in allLifters"
                :key="lifter.id"
                class="hover:bg-gray-50">
                <td class="border-b border-gray-200 px-6 py-4">
                {{ lifter.name }}
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                {{ lifter.lifter_id_number }}
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                {{ lifter.gender }}
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                {{ lifter.age }}
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                {{ lifter.actual_weight }} kg
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                {{ lifter.primary_weight_class_name }}
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                {{ lifter.primary_age_class_name }}
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                <select
                    v-model="lifter.selectedAdditionalWeightClass"
                    class="form-select p-1 text-xs md:text-sm">
                    <option :value="null">Add Class</option>
                    <option
                    v-for="wc in availableWeightClasses(lifter)"
                    :key="wc.id"
                    :value="wc.id">
                    {{ wc.name }}
                    </option>
                </select>
                <button
                    :disabled="!lifter.selectedAdditionalWeightClass"
                    class="btn-small-secondary mt-1"
                    @click="
                    addAdditionalWeightClass(
                        lifter.id,
                        lifter.selectedAdditionalWeightClass
                    )
                    ">
                    Add
                </button>
                <div class="mt-1 flex flex-wrap">
                    <span
                    v-for="wcName in lifter.additional_weight_class_names"
                    :key="wcName"
                    class="badge-class mr-1 mb-1 bg-blue-200 text-blue-800 text-xs md:text-sm">
                    {{ wcName }}
                    <button
                        class="ml-1 font-bold text-blue-600 hover:text-blue-900"
                        @click="
                        removeAdditionalWeightClass(
                            lifter.id,
                            getWeightClassIdByName(wcName)
                        )
                        ">
                        &times;
                    </button>
                    </span>
                </div>
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                <select
                    v-model="lifter.selectedAdditionalAgeClass"
                    class="form-select p-1 text-xs md:text-sm">
                    <option :value="null">Add Class</option>
                    <option
                    v-for="ac in availableAgeClasses(lifter)"
                    :key="ac.id"
                    :value="ac.id">
                    {{ ac.name }}
                    </option>
                </select>
                <button
                    :disabled="!lifter.selectedAdditionalAgeClass"
                    class="btn-small-secondary mt-1"
                    @click="
                    addAdditionalAgeClass(
                        lifter.id,
                        lifter.selectedAdditionalAgeClass
                    )
                    ">
                    Add
                </button>
                <div class="mt-1 flex flex-wrap">
                    <span
                    v-for="acName in lifter.additional_age_class_names"
                    :key="acName"
                    class="badge-class mr-1 mb-1 bg-purple-200 text-purple-800 text-xs md:text-sm">
                    {{ acName }}
                    <button
                        class="ml-1 font-bold text-purple-600 hover:text-purple-900"
                        @click="
                        removeAdditionalAgeClass(
                            lifter.id,
                            getAgeClassIdByName(acName)
                        )
                        ">
                        &times;
                    </button>
                    </span>
                </div>
                </td>
                <td class="border-b border-gray-200 px-6 py-4">
                <!-- Add more actions like edit lifter if needed -->
                </td>
            </tr>
            </tbody>
        </table>
      </div>
      <div v-else class="italic text-gray-600 text-base md:text-lg">No lifters registered.</div>
    </div>

    <!-- Class Management -->
    <div class="mb-8 rounded-lg bg-white p-6 shadow-md">
      <h2 class="mb-4 flex items-center text-xl md:text-2xl font-semibold text-gray-700">
        <svg
          class="mr-2 h-5 w-5 md:h-6 md:w-6 text-indigo-600"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg">
          <path
            d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z"
            stroke-linecap="round"
            stroke-linejoin="round" />
        </svg>
        Class Management
      </h2>

      <!-- Weight Class Management -->
      <div class="mb-6 rounded-md border bg-gray-50 p-4">
        <h3 class="mb-3 text-lg md:text-xl font-semibold text-gray-700">Weight Classes</h3>
        <form
          class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-4"
          @submit.prevent="addWeightClass">
          <input
            v-model="newWeightClass.name"
            class="form-input text-sm md:text-base"
            placeholder="Class Name (e.g., Men's 83kg)"
            required
            type="text" />
          <input
            v-model.number="newWeightClass.min_weight"
            class="form-input text-sm md:text-base"
            placeholder="Min Weight (kg)"
            required
            step="0.01"
            type="number" />
          <input
            v-model.number="newWeightClass.max_weight"
            class="form-input text-sm md:text-base"
            placeholder="Max Weight (kg, optional)"
            step="0.01"
            type="number" />
          <select v-model="newWeightClass.gender" class="form-select text-sm md:text-base" required>
            <option value="" disabled>Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Both">Both</option>
          </select>
          <button class="btn-primary col-span-full" type="submit">
            Add Weight Class
          </button>
        </form>
        <ul class="list-disc pl-5 text-sm md:text-base">
          <li
            v-for="wc in weightClasses"
            :key="wc.id"
            class="flex items-center justify-between py-1">
            {{ wc.name }} ({{ wc.min_weight }}kg -
            {{ wc.max_weight ? wc.max_weight + "kg" : "Open" }}) [{{
              wc.gender
            }}]
            <button class="btn-small-danger" @click="deleteWeightClass(wc.id)">
              Delete
            </button>
          </li>
        </ul>
      </div>

      <!-- Age Class Management -->
      <div class="mb-6 rounded-md border bg-gray-50 p-4 mt-8">
        <h3 class="mb-3 text-lg md:text-xl font-semibold text-gray-700">Age Classes</h3>
        <form
          class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-4"
          @submit.prevent="addAgeClass">
          <input
            v-model="newAgeClass.name"
            class="form-input text-sm md:text-base"
            placeholder="Class Name (e.g., Junior)"
            required
            type="text" />
          <input
            v-model.number="newAgeClass.min_age"
            class="form-input text-sm md:text-base"
            placeholder="Min Age"
            required
            type="number" />
          <input
            v-model.number="newAgeClass.max_age"
            class="form-input text-sm md:text-base"
            placeholder="Max Age (optional)"
            type="number" />
          <button class="btn-primary col-span-full" type="submit">
            Add Age Class
          </button>
        </form>
        <ul class="list-disc pl-5 text-sm md:text-base">
          <li
            v-for="ac in ageClasses"
            :key="ac.id"
            class="flex items-center justify-between py-1">
            {{ ac.name }} ({{ ac.min_age }} -
            {{ ac.max_age ? ac.max_age + " years" : "Open" }})
            <button class="btn-small-danger" @click="deleteAgeClass(ac.id)">
              Delete
            </button>
          </li>
        </ul>
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

// Functions to filter available classes for dropdowns (not computed)
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
    window.alert("Error fetching meet state. See console for details."); // Using window.alert
    console.error("Error fetching meet state:", error);
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
    window.alert("Error fetching lifters. See console for details."); // Using window.alert
    console.error("Error fetching lifters:", error);
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
    window.alert("Error fetching current lift. See console for details."); // Using window.alert
    console.error("Error fetching current lift:", error);
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
    window.alert("Error fetching next lifts in queue. See console for details."); // Using window.alert
    console.error("Error fetching next lifts in queue:", error);
  }
};

const fetchWeightClasses = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/weight_classes`);
    const data = await response.json();
    weightClasses.value = data;
  } catch (error) {
    window.alert("Error fetching weight classes. See console for details."); // Using window.alert
    console.error("Error fetching weight classes:", error);
  }
};

const fetchAgeClasses = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/age_classes`);
    const data = await response.json();
    ageClasses.value = data;
  } catch (error) {
    window.alert("Error fetching age classes. See console for details."); // Using window.alert
    console.error("Error fetching age classes:", error);
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
      window.alert(`Failed to change lift type: ${errorData.error || response.statusText}`); // Using window.alert
    }
  } catch (error) {
    window.alert("Network error or unexpected error while changing lift type."); // Using window.alert
    console.error("Error changing lift type:", error);
  }
};

const advanceAttempt = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state/advance_attempt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}), // Empty body for a POST request that triggers an action
    });
    if (!response.ok) {
      const errorData = await response.json();
      window.alert(`Failed to advance attempt: ${errorData.error || response.statusText}`); // Using window.alert
    }
  } catch (error) {
    window.alert("Network error or unexpected error while advancing attempt."); // Using window.alert
    console.error("Error advancing attempt:", error);
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
      window.alert(`Failed to add lifter: ${errorData.error || response.statusText}`); // Using window.alert
    }
  } catch (error) {
    window.alert("Network error or unexpected error while adding lifter."); // Using window.alert
    console.error("Error adding lifter:", error);
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
      window.alert(`Failed to set active lift: ${errorData.error || response.statusText}`); // Using window.alert
    }
  } catch (error) {
    window.alert("Network error or unexpected error while setting active lift."); // Using window.alert
    console.error("Error setting active lift:", error);
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
      window.alert(`Failed to add weight class: ${errorData.error || response.statusText}`); // Using window.alert
    }
  } catch (error) {
    window.alert("Network error or unexpected error while adding weight class."); // Using window.alert
    console.error("Error adding weight class:", error);
  }
};

const deleteWeightClass = async (wcId) => {
  if (!window.confirm("Are you sure you want to delete this weight class? This cannot be undone if lifters are assigned!")) { // Using window.confirm
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
      window.alert(`Failed to delete weight class: ${errorData.error || response.statusText}`); // Using window.alert
    }
  } catch (error) {
    window.alert("Network error or unexpected error while deleting weight class."); // Using window.alert
    console.error("Error deleting weight class:", error);
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
      window.alert(`Failed to add age class: ${errorData.error || response.statusText}`); // Using window.alert
    }
  } catch (error) {
    window.alert("Network error or unexpected error while adding age class."); // Using window.alert
    console.error("Error adding age class:", error);
  }
};

const deleteAgeClass = async (acId) => {
  if (!window.confirm("Are you sure you want to delete this age class? This cannot be undone if lifters are assigned!")) { // Using window.confirm
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
      window.alert(`Failed to delete age class: ${errorData.error || response.statusText}`); // Using window.alert
    }
  } catch (error) {
    window.alert("Network error or unexpected error while deleting age class."); // Using window.alert
    console.error("Error deleting age class:", error);
  }
};

const addAdditionalWeightClass = async (lifterId, weightClassId) => {
  if (!weightClassId) return;
  try {
    const response = await fetch(
      `${BACKEND_API_URL}/lifters/${lifterId}/add_additional_weight_class`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ weight_class_id: weightClassId }),
      }
    );
    if (!response.ok) {
      const errorData = await response.json();
      window.alert( // Using window.alert
        `Failed to add additional weight class: ${errorData.error || response.statusText}`
      );
    } else {
      fetchLifters(); // Refresh lifter data
    }
  } catch (error) {
    window.alert("Network error or unexpected error while adding additional weight class."); // Using window.alert
    console.error("Error adding additional weight class:", error);
  }
};

const removeAdditionalWeightClass = async (lifterId, weightClassId) => {
  if (!window.confirm("Are you sure you want to remove this additional weight class?")) { // Using window.confirm
    return;
  }
  try {
    const response = await fetch(
      `${BACKEND_API_URL}/lifters/${lifterId}/remove_additional_weight_class`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ weight_class_id: weightClassId }),
      }
    );
    if (!response.ok) {
      const errorData = await response.json();
      window.alert( // Using window.alert
        `Failed to remove additional weight class: ${errorData.error || response.statusText}`
      );
    } else {
      fetchLifters(); // Refresh lifter data
    }
  } catch (error) {
    window.alert("Network error or unexpected error while removing additional weight class."); // Using window.alert
    console.error("Error removing additional weight class:", error);
  }
};

const addAdditionalAgeClass = async (lifterId, ageClassId) => {
  if (!ageClassId) return;
  try {
    const response = await fetch(
      `${BACKEND_API_URL}/lifters/${lifterId}/add_additional_age_class`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ age_class_id: ageClassId }),
      }
    );
    if (!response.ok) {
      const errorData = await response.json();
      window.alert(`Failed to add additional age class: ${errorData.error || response.statusText}`); // Using window.alert
    } else {
      fetchLifters(); // Refresh lifter data
    }
  } catch (error) {
    window.alert("Network error or unexpected error while adding additional age class."); // Using window.alert
    console.error("Error adding additional age class:", error);
  }
};

const removeAdditionalAgeClass = async (lifterId, ageClassId) => {
  if (!window.confirm("Are you sure you want to remove this additional age class?")) { // Using window.confirm
    return;
  }
  try {
    const response = await fetch(
      `${BACKEND_API_URL}/lifters/${lifterId}/remove_additional_age_class`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ age_class_id: ageClassId }),
      }
    );
    if (!response.ok) {
      const errorData = await response.json();
      window.alert( // Using window.alert
        `Failed to remove additional age class: ${errorData.error || response.statusText}`
      );
    } else {
      fetchLifters(); // Refresh lifter data
    }
  } catch (error) {
    window.alert("Network error or unexpected error while removing additional age class."); // Using window.alert
    console.error("Error removing additional age class:", error);
  }
};

const exportMeetData = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/export_meet_data`);
    if (response.ok) {
      window.alert( // Using window.alert
        "Meet data export triggered on backend. Check backend logs for file path."
      );
    } else {
      const errorData = await response.json();
      window.alert(`Failed to export data: ${errorData.error || response.statusText}`); // Using window.alert
    }
  } catch (error) {
    window.alert("Network error or unexpected error during data export."); // Using window.alert
    console.error("Error during data export:", error);
  }
};

// --- Socket.IO Event Listeners ---
onMounted(() => {
  fetchMeetState();
  fetchLifters();
  fetchWeightClasses();
  fetchAgeClasses();

  socket.on("connect", () => {
    // console.log("Connected to Socket.IO from OrganizerView"); // Re-enabled for debugging connection issues
  });

  socket.on("meet_state_updated", (_data) => {
    // console.log("Meet state updated via Socket.IO:", _data);
    meetState.value = _data;
    fetchCurrentLift(); // Refetch active lift if meet state changes (e.g., attempt or lift type)
    fetchNextLiftsInQueue(); // Refetch queue
  });

  socket.on("active_lift_changed", (_data) => {
    // console.log("Active lift changed via Socket.IO:", _data);
    currentLift.value = _data;
    fetchNextLiftsInQueue(); // Active lift changed, so queue might change
  });

  socket.on("lift_updated", (_data) => {
    // console.log("Lift updated via Socket.IO:", _data);
    if (currentLift.value && currentLift.value.id === _data.id) {
      currentLift.value = _data; // Update current active lift if it's the one that changed
    }
    fetchNextLiftsInQueue(); // A lift status changed, so queue might need refresh
  });

  socket.on("lifter_added", () => {
    // console.log("Lifter added via Socket.IO:");
    fetchLifters(); // Refresh all lifters
  });

  socket.on("lifter_updated", () => {
    // console.log("Lifter updated via Socket.IO:");
    fetchLifters(); // Refresh all lifters in case primary/additional classes changed
  });

  socket.on("weight_class_updated", () => {
    fetchWeightClasses();
    fetchLifters();
  });

  socket.on("age_class_updated", () => {
    fetchAgeClasses();
    fetchLifters();
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
  @apply bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition duration-300 ease-in-out shadow-md text-base md:text-lg;
}

.btn-secondary {
  @apply bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition duration-300 ease-in-out shadow-md text-base md:text-lg;
}

.btn-success {
  @apply bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition duration-300 ease-in-out shadow-md text-base md:text-lg;
}

.btn-info {
  @apply bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-300 ease-in-out shadow-md text-base md:text-lg;
}

.btn-danger {
  @apply bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 transition duration-300 ease-in-out shadow-md text-base md:text-lg;
}

.btn-small-primary {
  @apply bg-indigo-500 text-white py-1 px-2 text-xs md:text-sm rounded-md hover:bg-indigo-600 transition duration-300 ease-in-out;
}

.btn-small-secondary {
  @apply bg-gray-500 text-white py-1 px-2 text-xs md:text-sm rounded-md hover:bg-gray-600 transition duration-300 ease-in-out;
}

.btn-small-danger {
  @apply bg-red-500 text-white py-1 px-2 text-xs md:text-sm rounded-md hover:bg-red-600 transition duration-300 ease-in-out;
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
