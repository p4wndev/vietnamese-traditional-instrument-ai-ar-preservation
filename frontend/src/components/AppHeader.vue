<template>
    <nav class="navbar navbar-expand-lg">
        <div class="navbar-brand-container d-flex justify-content-between w-100 container">
            <router-link to="/" class="navbar-brand">
                <img src="/logo.png" alt="" class="logo">
            </router-link>
            <div class="ms-auto navbar-nav">
                <router-link to="/" class="nav-item nav-link"><b>Trang chủ</b></router-link>
                <router-link to="/video-detect" class="nav-item nav-link"><b>Video Annotation</b></router-link>
                <router-link to="/contact" class="nav-item nav-link"><b>Liên hệ</b></router-link>
            </div>
        </div>
    </nav>
</template>

<script>
export default {
    computed: {},
    name: "app-header",
    methods: {
    },
};
</script>

<style scoped>
.logo {
    width: 100px;
    height: auto;
}

.navbar {
    background-color: #fff;
    height: 80px;
    position: sticky;
    width: 100%;
    top: 0;
    z-index: 90;
    box-shadow: 0 4px 4px 0 rgba(0, 0, 0, .1);
    margin-bottom: 20px;
}

.navbar-brand-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    flex-direction: row;
}

.navbar-brand {
    margin-right: 20px;
}

.navbar-nav {
    display: flex;
    list-style: none;
    padding-left: 0;
}

.nav-item {
    margin-left: 1rem;
}
</style>