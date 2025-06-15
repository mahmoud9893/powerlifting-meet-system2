import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue"; // Assuming you have a HomeView
import OrganizerView from "../views/OrganizerView.vue";
import PublicDisplayView from "../views/PublicDisplayView.vue";
import JudgeView from "../../../../MobileApp/src/views/JudgeView.vue"; // Corrected path and casing

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView,
  },
  {
    path: "/organizer",
    name: "organizer",
    component: OrganizerView,
  },
  {
    path: "/public",
    name: "public",
    component: PublicDisplayView,
  },
  {
    // NEW: Judge App Route
    path: "/judge",
    name: "judge",
    component: JudgeView,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
