<template>
    <div class="container">
        <h3>AI-Powered Vietnamese Traditional Instrument Preservation System using 3D space</h3>
        <div class="formInput">
            <div class="form-box">
                <form @submit.prevent="uploadImage">
                    <label for="imageInput" style="margin-right:5px;"><b>Upload an image here to identify the instrument:</b></label>
                    <input class="input-button" type="file" id="imageInput" @change="onFileChange" />
                    <button class="submit-button" type="submit" :disabled="!selectedFile">Upload</button>
                </form>
                <div v-if="loading">Loading...</div>
                <div v-else-if="error">{{ error }}</div>
            </div>
            <hr>
            <div>
                <ul>
                    <li v-for="(instrument, index) in instruments" :key="index">
                        <p style="font-size:20px;"><b>{{ index + 1 }}. {{ nhac_cu_dt[instrument] }}</b></p>
                        <div v-if="existingModels3d.includes(instrument)">
                            <Instrument3D 
                                :key="instrument"    
                                :one_class_name="instrument"
                                :modelPath="'/models/' + instrument + '/' + instrument + '.gltf'" 
                            />
                        </div>
                        <div v-else>
                            Hiện tại, mô hình {{ nhac_cu_dt[instrument] }} đang được cập nhật!
                        </div>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script>
import PredictService from "../services/predict.service";
import Instrument3D from "@/components/Model3d.vue";

export default {
    components: {
        Instrument3D,
    },
    data() {
        return {
            instruments: [],
            loading: false,
            error: null,
            selectedFile: null,
            modelPaths: [],
            existingModels3d: ['cong_chieng', 'dan_bau', 'dan_co', 'dan_da', 'dan_nguyet', 'dan_sen', 'dan_tranh', 'dan_ty_ba', 'guitar', 'trong_quan'],
            nhac_cu_dt:{
                'cong_chieng': 'Cồng chiêng',
                'dan_bau': 'Đàn bầu',
                'dan_co': 'Đàn cò',
                'dan_da': 'Đàn đá',
                'dan_day': 'Đàn đáy',
                'dan_nguyet': 'Đàn nguyệt',
                'dan_sen': 'Đàn sến',
                'dan_t_rung': 'Đàn T\'rưng',
                'dan_tinh': 'Đàn tính',
                'dan_tranh': 'Đàn tranh',
                'dan_ty_ba': 'Đàn tỳ bà',
                'guitar': 'Guitar',
                'khen': 'Khèn',
                'trong_quan': 'Trống quân'
            }
        };
    },
    methods: {
        onFileChange(event) {
            this.selectedFile = event.target.files[0];
        },
        async uploadImage() {
            if (!this.selectedFile) {
                this.error = 'Please select an image file';
                return;
            }

            this.loading = true;
            this.error = null;

            const formData = new FormData();
            formData.append('image_input', this.selectedFile);
            try {
                const response = await PredictService.uploadImage(formData);
                this.instruments = [...new Set(response.data.cl_o)];
            } catch (error) {
                this.error = 'Failed to upload image or load instruments';
                console.error(error);
            } finally {
                this.loading = false;
            }
        },

    }
};
</script>

<style scoped>
.form-box {
    border: 1px solid #ccc;
    padding: 30px;
    border-radius: 8px;
    margin-bottom: 16px;
    background-color: #f9f9f9;

}

.submit-button {
    -moz-box-shadow: inset 0px 1px 0px 0px #ffffff;
    -webkit-box-shadow: inset 0px 1px 0px 0px #ffffff;
    box-shadow: inset 0px 1px 0px 0px #ffffff;
    background: -webkit-gradient(linear, left top, left bottom, color-stop(0.05, #ededed), color-stop(1, #dfdfdf));
    background: -moz-linear-gradient(center top, #ededed 5%, #dfdfdf 100%);
    filter: progid:DXImageTransform.Microsoft.gradient(startColorstr='#ededed', endColorstr='#dfdfdf');
    background-color: #ededed;
    -webkit-border-top-left-radius: 23px;
    -moz-border-radius-topleft: 23px;
    border-top-left-radius: 23px;
    -webkit-border-top-right-radius: 23px;
    -moz-border-radius-topright: 23px;
    border-top-right-radius: 23px;
    -webkit-border-bottom-right-radius: 23px;
    -moz-border-radius-bottomright: 23px;
    border-bottom-right-radius: 23px;
    -webkit-border-bottom-left-radius: 23px;
    -moz-border-radius-bottomleft: 23px;
    border-bottom-left-radius: 23px;
    text-indent: 0;
    border: 1px solid #dcdcdc;
    display: inline-block;
    color: #130707;
    font-family: Arial;
    font-size: 16px;
    font-weight: bold;
    font-style: normal;
    height: 32px;
    line-height: 32px;
    width: 104px;
    text-decoration: none;
    text-align: center;
    text-shadow: 1px 1px 0px #ffffff;
}

.submit-button:hover {
    background: -webkit-gradient(linear, left top, left bottom, color-stop(0.05, #dfdfdf), color-stop(1, #ededed));
    background: -moz-linear-gradient(center top, #dfdfdf 5%, #ededed 100%);
    filter: progid:DXImageTransform.Microsoft.gradient(startColorstr='#dfdfdf', endColorstr='#ededed');
    background-color: #dfdfdf;
}

.submit-button:active {
    position: relative;
    top: 1px;
}

.container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
}

.formInput {
    width: 100%;
    /* max-width: 800px; */
    margin-bottom: 20px;
}

ul {
    list-style-type: none;
    padding: 0;
}

li {
    margin-bottom: 20px;
}
</style>
