import { createWebHistory, createRouter } from "vue-router";

const routes = [
    {
        path: "/",
        name: "main",
        component: () => import("@/views/Prediction.vue"),
    },
    {
        path: "/video-detect",
        name: "video-detect",
        component: () => import("@/views/VideoDetect.vue"),
    },
    {
        path: "/contact-us",
        name: "contact-us",
        component: () => import("@/views/ContactUs.vue"),
    },
];

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
});

export default router;