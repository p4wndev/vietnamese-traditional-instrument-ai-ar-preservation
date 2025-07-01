<template>
    <div class="container">
        <div class="overlay">
            <h3 class="introduce-infor">ViTIP: AI-Powered Vietnamese Traditional Instrument Preservation System</h3>
            <p class="description">The ViTIP project uses artificial intelligence to preserve Vietnam's traditional
                musical
                instruments.
                It detects and classifies instruments using image data, provides 3D visualizations, and enriches
                contextual
                information with a lightweight ontology.
                This project is for cultural heritage professionals, researchers,
                and the general public interested in preserving and learning about Vietnam’s cultural heritage.
            </p>
            <hr>

            <h3>Authors</h3>
            <ul class="authors-list">
                <li><a href="https://github.com/truongthanhma">Thanh Ma</a></li>
                <li><a href="https://github.com/NT-Hieu203">Thanh-Hieu Nguyen</a></li>
                <li><a href="https://github.com/Michael-Ngn">Phuc-Ky Nguyen</a></li>
                <li><a href="https://github.com/jerosiet">Yen-Thi Nguyen Thi</a></li>
                <li><a href="https://github.com/imxuan03">Thanh-Xuan Nguyen</a></li>
            </ul>

        </div>

    </div>
</template>

<script>

export default {
    components: {
    },
    data() {
        return {

        };
    },
    methods: {

    }
};
</script>

<style scoped>
html,
body {
    height: 100%;
    margin: 0;
}

.container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    /* căn giữa theo chiều dọc */
    align-items: center;
    /* căn giữa theo chiều ngang */
    height: 70vh;
    /* 100% chiều cao viewport */
    padding: 20px;
}

.description {
    font-size: 18px;
    line-height: 1.6;
    text-align: center;
    padding: 0;
}

.authors-list {
    padding: 0;
    margin: 0;
    display: flex;
    justify-content: center;
}

.authors-list li {
    margin: 5px 20px;
}

.authors-list li a {
    color: black;
}

.authors-list li a:hover {
    color: black
}
</style>
