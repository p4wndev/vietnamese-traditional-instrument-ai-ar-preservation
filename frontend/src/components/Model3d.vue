<template>
    <div class="model3d-container">
        <div ref="container3D" class="model3d"></div>
        <div class="ontology-infor">
            <p style="margin-bottom:5px; font-size:18px"><b>Thông tin đàn:</b></p>
            <ul style="margin-left:20px;">
                <li v-for="(item, index) in ontology_info" :key="index">
                    <b>- {{ index }}:</b> {{ item }}
                </li>
            </ul>
        </div>
        <p style="margin-bottom:20px; font-size:18px"><b>Các loại hình nghệ thuật</b></p>
        <div class="ontology-video">
            <div v-for="(video, videoIndex) in videos" :key="videoIndex" class="ontology-video-item">
                <!-- Hiển thị video đầu tiên -->
                <div v-if="video['Có URL là ']" class="video-container">
                    <iframe :width="280" :height="135" :src="getEmbedUrl(video['Có URL là '])" frameborder="0"
                        allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
                        allowfullscreen></iframe>
                </div>
                <!-- Hiển thị các thông tin khác, trừ thông tin "Có URL là " -->
                <div v-for="(value, key) in filteredVideo(video)" :key="`${videoIndex}-${key}`">
                    <b>- {{ key }}:</b> {{ value }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import * as THREE from "https://cdn.skypack.dev/three@0.129.0/build/three.module.js";
import { OrbitControls } from "https://cdn.skypack.dev/three@0.129.0/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "https://cdn.skypack.dev/three@0.129.0/examples/jsm/loaders/GLTFLoader.js";
import PredictService from "../services/predict.service";

export default {
    data() {
        return {
            ontology_info: String,
            videos: [],
        };
    },
    props: {
        modelPath: String, // Đường dẫn đến file .gltf của mô hình
        one_class_name: String,
    },
    mounted() {
        this.initScene();
        this.getOntologyInfor();
    },
    methods: {
        getEmbedUrl(url) {
            // Lấy video ID từ URL
            const videoId = url.split('v=')[1] ? url.split('v=')[1].split('&')[0] : url.split('youtu.be/')[1].split('?')[0];
            return `https://www.youtube.com/embed/${videoId}`;
        },
        filteredVideo(video) {
            // Loại bỏ thuộc tính "Có URL là " khỏi đối tượng video
            const { "Có URL là ": _, ...filtered } = video;
            return filtered;
        },
        async initScene() {
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(
                75,
                this.$refs.container3D.clientWidth / this.$refs.container3D.clientHeight,
                0.1,
                1000
            );

            const renderer = new THREE.WebGLRenderer({ alpha: true });
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.setSize(this.$refs.container3D.clientWidth, this.$refs.container3D.clientHeight);
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1;
            this.$refs.container3D.appendChild(renderer.domElement);

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.25;
            controls.screenSpacePanning = false;
            controls.minDistance = 5;
            controls.maxDistance = 10;
            controls.maxPolarAngle = Math.PI / 2;

            let object;

            const loader = new GLTFLoader();
            loader.load(
                this.modelPath,
                (gltf) => {
                    object = gltf.scene;
                    scene.add(object);
                    const box = new THREE.Box3().setFromObject(object);
                    const center = box.getCenter(new THREE.Vector3());
                    object.position.sub(center);
                },
                (xhr) => {
                    console.log((xhr.loaded / xhr.total) * 100 + "% loaded");
                },
                (error) => {
                    console.error(error);
                }
            );

            camera.position.z = 5;

            // Add lights to the scene, so we can actually see the 3D model
            const topLight = new THREE.DirectionalLight(0xffffff, 1); // (color, intensity)
            topLight.position.set(500, 500, 500); // top-left-ish
            topLight.castShadow = true;
            scene.add(topLight);

            const light1 = new THREE.DirectionalLight(0xffffff, 2);
            light1.position.set(-200, 300, 200);
            scene.add(light1);

            const light2 = new THREE.DirectionalLight(0xffffff, 2);
            light2.position.set(200, -300, -200);
            scene.add(light2);

            const light3 = new THREE.DirectionalLight(0xffffff, 2);
            light3.position.set(-200, -300, 200);
            scene.add(light3);

            const light4 = new THREE.DirectionalLight(0xffffff, 2);
            light4.position.set(200, 300, -200);
            scene.add(light4);

            const ambientLight = new THREE.AmbientLight(0x333333, 1);
            scene.add(ambientLight);

            // Render the scene
            const animate = () => {
                requestAnimationFrame(animate);

                // Tự động xoay mô hình theo phương thẳng đứng
                if (object) {
                    object.rotation.y += 0.01; // Thay đổi giá trị này để điều chỉnh tốc độ quay
                }

                controls.update(); // only required if controls.enableDamping = true, or if controls.autoRotate = true
                renderer.render(scene, camera);
            };



            window.addEventListener("resize", () => {
                camera.aspect = this.$refs.container3D.clientWidth / this.$refs.container3D.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(this.$refs.container3D.clientWidth, this.$refs.container3D.clientHeight);
            });
            animate();
        },
        async getOntologyInfor() {
            try {
                console.log(this.one_class_name)
                const response = await PredictService.getOntologyInfor(this.one_class_name);
                this.ontology_info = response.data.ontology_info;
                this.videos = response.data.videos;
            } catch (error) {
                this.error = 'Failed to retrieve ontology information.';
                console.error(error);
            }
        }
    },
};
</script>

<style scoped>
.ontology-infor {
    padding: 20px;
}

.ontology-infor {
    width: 100%;
    margin-top: 20px;
    padding: 10px;
    background-color: #f9f9f9;
    border: 1px solid #ccc;
    border-radius: 8px;
    margin-bottom: 20px;
}

.ontology-infor ul,
.ontology-video ul {
    list-style-type: none;
    padding: 0;
}

.ontology-infor li,
.ontology-video li {
    margin-bottom: 5px;
}

.model3d-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    /* Sắp xếp các thẻ div bên trong theo chiều dọc */
    align-items: center;
    /* gap: 20px; */
}

.model3d {
    width: 80%;
    height: 500px;
    /* Điều chỉnh chiều cao cho phù hợp */
    border: 3px solid black;
    box-sizing: border-box;
}

.ontology-video {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
}

.ontology-video-item {
    background-color: #f0f0f0;
    /* Màu nền cho các phần tử */
    padding: 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.video-container {
    display: flex;
    justify-content: center;
    width: 100%;
    margin-bottom: 10px;
}
</style>