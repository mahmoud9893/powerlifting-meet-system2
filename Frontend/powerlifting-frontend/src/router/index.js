import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import OrganizerView from "../views/OrganizerView.vue";
import PublicDisplayView from "../views/PublicDisplayView.vue";
// Ensure you are importing the JudgesView.vue file that was provided
import JudgesView from '../views/JudgesView.vue'

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView
  },
  {
    path: "/organizer",
    name: "organizer",
    component: OrganizerView
  },
  {
    path: "/display", // Changed from /public to /display to match your URL
    name: "display", // Changed name for consistency
    component: PublicDisplayView
  },
  {
    // Judge App Route
    path: "/judge",
    name: "judge",
    component: JudgesView // Ensure this uses JudgesView, not JudgeView
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
